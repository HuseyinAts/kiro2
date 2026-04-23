"""
LangChain RAG (Retrieval-Augmented Generation) System
Advanced document retrieval and generation using LangChain
"""

import asyncio
import logging
import os
from pathlib import Path
from typing import Any

from langchain.chains import ConversationalRetrievalChain, RetrievalQA
from langchain.memory import ConversationBufferMemory, ConversationSummaryBufferMemory

# For hybrid search
from langchain.retrievers import (
    ContextualCompressionRetriever,
    EnsembleRetriever,
    MultiQueryRetriever,
    TimeWeightedVectorStoreRetriever,
)
from langchain.retrievers.document_compressors import LLMChainExtractor
from langchain.text_splitter import (
    CharacterTextSplitter,
    Language,
    MarkdownTextSplitter,
    PythonCodeTextSplitter,
    RecursiveCharacterTextSplitter,
    TokenTextSplitter,
)

# LangChain imports - Updated to non-deprecated versions
from langchain_community.document_loaders import (
    CSVLoader,
    DirectoryLoader,
    JSONLoader,
    PythonLoader,
    TextLoader,
    UnstructuredMarkdownLoader,
    UnstructuredWordDocumentLoader,
)
from langchain_community.document_loaders import (
    PyPDFLoader as PDFLoader,
)
from langchain_community.embeddings import (
    CohereEmbeddings,
    HuggingFaceEmbeddings,
)
from langchain_community.retrievers import BM25Retriever
from langchain_community.vectorstores import FAISS, Chroma
from langchain_core.documents import Document
from langchain_core.prompts import PromptTemplate
from langchain_openai import OpenAIEmbeddings

logger = logging.getLogger(__name__)


class DocumentProcessor:
    """Process various document types for RAG"""

    def __init__(self):
        self.loaders = {
            ".txt": TextLoader,
            ".pdf": PDFLoader,
            ".md": UnstructuredMarkdownLoader,
            ".docx": UnstructuredWordDocumentLoader,
            ".json": JSONLoader,
            ".csv": CSVLoader,
            ".py": PythonLoader,
        }

        self.text_splitters = {
            "recursive": RecursiveCharacterTextSplitter,
            "character": CharacterTextSplitter,
            "token": TokenTextSplitter,
            "markdown": MarkdownTextSplitter,
            "python": PythonCodeTextSplitter,
        }

    def load_document(self, file_path: str) -> list[Document]:
        """Load a single document"""
        try:
            file_ext = Path(file_path).suffix.lower()

            if file_ext in self.loaders:
                loader_class = self.loaders[file_ext]

                if file_ext == ".json":
                    # JSON needs special handling
                    loader = loader_class(file_path, jq_schema=".", text_content=False)
                else:
                    loader = loader_class(file_path)

                documents = loader.load()
                logger.info(f"Loaded {len(documents)} documents from {file_path}")
                return documents
            # Try generic text loader
            loader = TextLoader(file_path, encoding="utf-8")
            return loader.load()

        except Exception as e:
            logger.error(f"Error loading document {file_path}: {e}")
            return []

    def load_directory(
        self,
        directory_path: str,
        glob_pattern: str = "**/*.txt",
        recursive: bool = True,
    ) -> list[Document]:
        """Load all documents from a directory"""
        try:
            loader = DirectoryLoader(
                directory_path,
                glob=glob_pattern,
                recursive=recursive,
                show_progress=True,
            )

            documents = loader.load()
            logger.info(f"Loaded {len(documents)} documents from {directory_path}")
            return documents

        except Exception as e:
            logger.error(f"Error loading directory {directory_path}: {e}")
            return []

    def split_documents(
        self,
        documents: list[Document],
        splitter_type: str = "recursive",
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        language: str | None = None,
    ) -> list[Document]:
        """Split documents into chunks"""

        splitter_class = self.text_splitters.get(
            splitter_type, RecursiveCharacterTextSplitter
        )

        if splitter_type == "python" and language:
            splitter = splitter_class(
                language=Language[language.upper()],
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
            )
        elif splitter_type == "token":
            splitter = splitter_class(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                model_name="gpt-3.5-turbo",
            )
        else:
            splitter = splitter_class(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""],
            )

        chunks = splitter.split_documents(documents)
        logger.info(f"Split into {len(chunks)} chunks")

        return chunks

    def create_documents_from_texts(
        self, texts: list[str], metadatas: list[dict] | None = None
    ) -> list[Document]:
        """Create documents from raw texts"""

        documents = []
        for i, text in enumerate(texts):
            metadata = metadatas[i] if metadatas and i < len(metadatas) else {}
            doc = Document(page_content=text, metadata=metadata)
            documents.append(doc)

        return documents


class VectorStoreManager:
    """Manage vector stores for RAG"""

    def __init__(self, embeddings_type: str = "openai"):
        self.embeddings = self._initialize_embeddings(embeddings_type)
        self.vector_stores = {}
        # Removed deprecated VectorstoreIndexCreator - use direct vector store creation
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000, chunk_overlap=200
        )

    def _initialize_embeddings(self, embeddings_type: str):
        """Initialize embeddings model"""

        if embeddings_type == "openai" and os.getenv("OPENAI_API_KEY"):
            return OpenAIEmbeddings(
                model="text-embedding-ada-002",
                openai_api_key=os.getenv("OPENAI_API_KEY"),
            )
        if embeddings_type == "cohere" and os.getenv("COHERE_API_KEY"):
            return CohereEmbeddings(
                model="embed-multilingual-v2.0",
                cohere_api_key=os.getenv("COHERE_API_KEY"),
            )
        # Default to free HuggingFace embeddings
        return HuggingFaceEmbeddings(
            model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )

    def create_vector_store(
        self, documents: list[Document], store_name: str, store_type: str = "faiss"
    ) -> Any:
        """Create a vector store from documents"""

        try:
            if store_type == "faiss":
                vector_store = FAISS.from_documents(documents, self.embeddings)
            elif store_type == "chroma":
                vector_store = Chroma.from_documents(
                    documents,
                    self.embeddings,
                    collection_name=store_name,
                    persist_directory=f"./chroma_db/{store_name}",
                )
            else:
                # Default to FAISS
                vector_store = FAISS.from_documents(documents, self.embeddings)

            self.vector_stores[store_name] = vector_store
            logger.info(
                f"Created vector store '{store_name}' with {len(documents)} documents"
            )

            return vector_store

        except Exception as e:
            logger.error(f"Error creating vector store: {e}")
            return None

    def load_vector_store(
        self,
        store_name: str,
        store_type: str = "faiss",
        persist_directory: str = "./vector_stores",
    ) -> Any:
        """Load existing vector store"""

        try:
            if store_type == "faiss":
                store_path = os.path.join(persist_directory, f"{store_name}.faiss")
                vector_store = FAISS.load_local(store_path, self.embeddings)
            elif store_type == "chroma":
                vector_store = Chroma(
                    persist_directory=f"./chroma_db/{store_name}",
                    embedding_function=self.embeddings,
                )
            else:
                raise ValueError(f"Unsupported store type: {store_type}")

            self.vector_stores[store_name] = vector_store
            logger.info(f"Loaded vector store '{store_name}'")

            return vector_store

        except Exception as e:
            logger.error(f"Error loading vector store: {e}")
            return None

    def save_vector_store(
        self, store_name: str, persist_directory: str = "./vector_stores"
    ):
        """Save vector store to disk"""

        if store_name not in self.vector_stores:
            logger.error(f"Vector store '{store_name}' not found")
            return

        try:
            os.makedirs(persist_directory, exist_ok=True)
            vector_store = self.vector_stores[store_name]

            if isinstance(vector_store, FAISS):
                store_path = os.path.join(persist_directory, f"{store_name}.faiss")
                vector_store.save_local(store_path)
                logger.info(f"Saved FAISS store to {store_path}")
            elif isinstance(vector_store, Chroma):
                # Chroma auto-persists
                logger.info("Chroma store auto-persisted")

        except Exception as e:
            logger.error(f"Error saving vector store: {e}")

    def add_documents(self, store_name: str, documents: list[Document]):
        """Add documents to existing vector store"""

        if store_name not in self.vector_stores:
            logger.error(f"Vector store '{store_name}' not found")
            return

        try:
            vector_store = self.vector_stores[store_name]
            vector_store.add_documents(documents)
            logger.info(f"Added {len(documents)} documents to '{store_name}'")

        except Exception as e:
            logger.error(f"Error adding documents: {e}")

    def similarity_search(
        self, store_name: str, query: str, k: int = 4, filter: dict | None = None
    ) -> list[Document]:
        """Perform similarity search"""

        if store_name not in self.vector_stores:
            logger.error(f"Vector store '{store_name}' not found")
            return []

        try:
            vector_store = self.vector_stores[store_name]

            if filter:
                results = vector_store.similarity_search(query, k=k, filter=filter)
            else:
                results = vector_store.similarity_search(query, k=k)

            return results

        except Exception as e:
            logger.error(f"Error in similarity search: {e}")
            return []

    def max_marginal_relevance_search(
        self,
        store_name: str,
        query: str,
        k: int = 4,
        fetch_k: int = 20,
        lambda_mult: float = 0.5,
    ) -> list[Document]:
        """Perform MMR search for diverse results"""

        if store_name not in self.vector_stores:
            return []

        try:
            vector_store = self.vector_stores[store_name]
            results = vector_store.max_marginal_relevance_search(
                query, k=k, fetch_k=fetch_k, lambda_mult=lambda_mult
            )
            return results

        except Exception as e:
            logger.error(f"Error in MMR search: {e}")
            return []


class AdvancedRAGSystem:
    """Advanced RAG system with multiple retrieval strategies"""

    def __init__(self, llm_service):
        self.llm_service = llm_service
        self.doc_processor = DocumentProcessor()
        self.vector_manager = VectorStoreManager()
        self.retrievers = {}
        self.chains = {}

    def create_multi_query_retriever(self, store_name: str, llm=None):
        """Create multi-query retriever for better recall"""

        if store_name not in self.vector_manager.vector_stores:
            logger.error(f"Vector store '{store_name}' not found")
            return None

        vector_store = self.vector_manager.vector_stores[store_name]
        base_retriever = vector_store.as_retriever()

        llm = llm or self.llm_service.chat_model or self.llm_service.llm

        retriever = MultiQueryRetriever.from_llm(retriever=base_retriever, llm=llm)

        self.retrievers[f"multi_query_{store_name}"] = retriever
        return retriever

    def create_contextual_compression_retriever(self, store_name: str, llm=None):
        """Create retriever with contextual compression"""

        if store_name not in self.vector_manager.vector_stores:
            return None

        vector_store = self.vector_manager.vector_stores[store_name]
        base_retriever = vector_store.as_retriever()

        llm = llm or self.llm_service.chat_model or self.llm_service.llm

        # Create compressor
        compressor = LLMChainExtractor.from_llm(llm)

        # Create compression retriever
        retriever = ContextualCompressionRetriever(
            base_compressor=compressor, base_retriever=base_retriever
        )

        self.retrievers[f"compressed_{store_name}"] = retriever
        return retriever

    def create_hybrid_retriever(
        self, store_name: str, documents: list[Document], bm25_weight: float = 0.5
    ):
        """Create hybrid retriever (dense + sparse)"""

        if store_name not in self.vector_manager.vector_stores:
            return None

        vector_store = self.vector_manager.vector_stores[store_name]

        # Dense retriever (vector store)
        dense_retriever = vector_store.as_retriever(search_kwargs={"k": 4})

        # Sparse retriever (BM25)
        bm25_retriever = BM25Retriever.from_documents(documents)
        bm25_retriever.k = 4

        # Ensemble retriever
        ensemble_retriever = EnsembleRetriever(
            retrievers=[bm25_retriever, dense_retriever],
            weights=[bm25_weight, 1 - bm25_weight],
        )

        self.retrievers[f"hybrid_{store_name}"] = ensemble_retriever
        return ensemble_retriever

    def create_time_weighted_retriever(self, store_name: str, decay_rate: float = 0.01):
        """Create time-weighted retriever for recent documents"""

        if store_name not in self.vector_manager.vector_stores:
            return None

        vector_store = self.vector_manager.vector_stores[store_name]

        retriever = TimeWeightedVectorStoreRetriever(
            vectorstore=vector_store, decay_rate=decay_rate, k=4
        )

        self.retrievers[f"time_weighted_{store_name}"] = retriever
        return retriever

    def create_qa_chain(
        self,
        store_name: str,
        chain_type: str = "stuff",
        retriever_type: str = "default",
        return_source_documents: bool = True,
    ):
        """Create QA chain with specified retriever"""

        # Get retriever
        if retriever_type == "default":
            if store_name not in self.vector_manager.vector_stores:
                return None
            retriever = self.vector_manager.vector_stores[store_name].as_retriever()
        else:
            retriever_key = f"{retriever_type}_{store_name}"
            if retriever_key not in self.retrievers:
                logger.error(f"Retriever '{retriever_key}' not found")
                return None
            retriever = self.retrievers[retriever_key]

        # Create QA chain
        llm = self.llm_service.chat_model or self.llm_service.llm

        qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type=chain_type,
            retriever=retriever,
            return_source_documents=return_source_documents,
            verbose=True,
        )

        self.chains[f"qa_{store_name}_{retriever_type}"] = qa_chain
        return qa_chain

    def create_conversational_chain(self, store_name: str, memory_type: str = "buffer"):
        """Create conversational retrieval chain"""

        if store_name not in self.vector_manager.vector_stores:
            return None

        retriever = self.vector_manager.vector_stores[store_name].as_retriever()
        llm = self.llm_service.chat_model or self.llm_service.llm

        # Create memory
        if memory_type == "summary":
            memory = ConversationSummaryBufferMemory(
                llm=llm,
                memory_key="chat_history",
                return_messages=True,
                output_key="answer",
            )
        else:
            memory = ConversationBufferMemory(
                memory_key="chat_history", return_messages=True, output_key="answer"
            )

        # Create chain
        chain = ConversationalRetrievalChain.from_llm(
            llm=llm,
            retriever=retriever,
            memory=memory,
            return_source_documents=True,
            verbose=True,
        )

        self.chains[f"conversational_{store_name}"] = chain
        return chain

    def create_custom_qa_chain(self, store_name: str, custom_prompt: str):
        """Create QA chain with custom prompt"""

        if store_name not in self.vector_manager.vector_stores:
            return None

        retriever = self.vector_manager.vector_stores[store_name].as_retriever()
        llm = self.llm_service.chat_model or self.llm_service.llm

        # Create custom prompt
        prompt_template = PromptTemplate(
            template=custom_prompt, input_variables=["context", "question"]
        )

        # Create chain
        chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=retriever,
            return_source_documents=True,
            chain_type_kwargs={"prompt": prompt_template},
        )

        self.chains[f"custom_{store_name}"] = chain
        return chain

    async def query(self, query: str, chain_name: str) -> dict[str, Any]:
        """Query using specified chain"""

        if chain_name not in self.chains:
            return {"success": False, "error": f"Chain '{chain_name}' not found"}

        try:
            chain = self.chains[chain_name]

            # Check if conversational
            if "conversational" in chain_name:
                result = await chain.arun({"question": query})
            else:
                result = await chain.arun(query)

            # Extract answer and sources
            if isinstance(result, dict):
                answer = result.get("answer", result.get("result", str(result)))
                sources = result.get("source_documents", [])
            else:
                answer = str(result)
                sources = []

            return {
                "success": True,
                "answer": answer,
                "sources": [
                    {"content": doc.page_content[:200], "metadata": doc.metadata}
                    for doc in sources
                ],
                "chain_used": chain_name,
            }

        except Exception as e:
            logger.error(f"Query error: {e}")
            return {"success": False, "error": str(e)}


# Educational content RAG system
class EducationalRAG:
    """RAG system specifically for educational content"""

    def __init__(self, llm_service):
        self.rag_system = AdvancedRAGSystem(llm_service)
        self.subject_stores = {}

    async def index_curriculum(
        self, subject: str, grade: int, content_files: list[str]
    ):
        """Index curriculum content for a subject"""

        # Load documents
        documents = []
        for file_path in content_files:
            docs = self.rag_system.doc_processor.load_document(file_path)
            # Add metadata
            for doc in docs:
                doc.metadata.update(
                    {"subject": subject, "grade": grade, "source_file": file_path}
                )
            documents.extend(docs)

        # Split documents
        chunks = self.rag_system.doc_processor.split_documents(
            documents, chunk_size=500, chunk_overlap=50
        )

        # Create vector store
        store_name = f"{subject}_grade_{grade}"
        self.rag_system.vector_manager.create_vector_store(
            chunks, store_name, store_type="faiss"
        )

        # Create specialized retrievers
        self.rag_system.create_multi_query_retriever(store_name)
        self.rag_system.create_hybrid_retriever(store_name, chunks)

        # Create QA chains
        self.rag_system.create_qa_chain(store_name, retriever_type="multi_query")
        self.rag_system.create_conversational_chain(store_name)

        # Custom educational prompt
        edu_prompt = """You are an educational assistant helping students learn {subject}.
        Use the following context to answer the question in a clear, educational manner.
        Include examples when helpful.
        
        Context: {context}
        Question: {question}
        
        Educational Answer:"""

        self.rag_system.create_custom_qa_chain(store_name, edu_prompt)

        self.subject_stores[subject] = store_name

        logger.info(f"Indexed curriculum for {subject} grade {grade}")

    async def answer_question(
        self, question: str, subject: str, use_conversation: bool = False
    ) -> dict[str, Any]:
        """Answer educational question"""

        if subject not in self.subject_stores:
            return {"success": False, "error": f"Subject '{subject}' not indexed"}

        store_name = self.subject_stores[subject]

        if use_conversation:
            chain_name = f"conversational_{store_name}"
        else:
            chain_name = f"custom_{store_name}"

        result = await self.rag_system.query(question, chain_name)

        # Add educational metadata
        if result["success"]:
            result["educational_context"] = {
                "subject": subject,
                "question_type": self._classify_question(question),
                "difficulty": self._estimate_difficulty(question),
                "suggested_followup": self._generate_followup(question),
            }

        return result

    def _classify_question(self, question: str) -> str:
        """Classify question type"""
        question_lower = question.lower()

        if "nedir" in question_lower or "what" in question_lower:
            return "definition"
        if "nasıl" in question_lower or "how" in question_lower:
            return "explanation"
        if "neden" in question_lower or "why" in question_lower:
            return "reasoning"
        if "örnek" in question_lower or "example" in question_lower:
            return "example"
        return "general"

    def _estimate_difficulty(self, question: str) -> str:
        """Estimate question difficulty"""
        # Simple heuristic based on question length and complexity
        words = question.split()
        if len(words) < 5:
            return "easy"
        if len(words) < 10:
            return "medium"
        return "hard"

    def _generate_followup(self, question: str) -> str:
        """Generate follow-up question"""
        question_type = self._classify_question(question)

        followups = {
            "definition": "Can you provide an example?",
            "explanation": "Why is this important?",
            "reasoning": "How does this apply in practice?",
            "example": "Can you explain the concept?",
            "general": "Would you like more details?",
        }

        return followups.get(question_type, "Would you like to know more?")


# Example usage
async def example_usage():
    """Example of using LangChain RAG system"""

    from core.langchain_llm_service import get_langchain_service

    llm_service = get_langchain_service()
    edu_rag = EducationalRAG(llm_service)

    # Index some educational content
    await edu_rag.index_curriculum(
        subject="matematik",
        grade=8,
        content_files=["./data/math_grade8.txt"],  # Example files
    )

    # Answer questions
    result = await edu_rag.answer_question(
        question="Pythagoras teoremi nedir?", subject="matematik", use_conversation=True
    )

    print(f"Answer: {result}")


if __name__ == "__main__":
    asyncio.run(example_usage())

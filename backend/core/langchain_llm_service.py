"""
LangChain-based LLM Service
Advanced LLM operations using LangChain framework
"""

import asyncio
import logging
import os
from typing import Any

# LangChain Core imports (updated for 2026 - no deprecated paths)
from langchain.agents import AgentExecutor
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain.chains import ConversationalRetrievalChain, LLMChain, RetrievalQA
from langchain.memory import (
    ConversationBufferMemory,
    ConversationBufferWindowMemory,
    ConversationSummaryBufferMemory,
    ConversationSummaryMemory,
)
from langchain.prompts import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    MessagesPlaceholder,
    SystemMessagePromptTemplate,
)
from langchain.schema import AIMessage, Document, HumanMessage
from langchain.text_splitter import RecursiveCharacterTextSplitter

# LangChain Community imports (migrated from deprecated langchain.* paths)
from langchain_community.cache import InMemoryCache, RedisCache
from langchain_community.llms import HuggingFaceHub
from langchain_community.tools import DuckDuckGoSearchRun, WikipediaQueryRun
from langchain_community.vectorstores import FAISS, Chroma

# LangChain Partner packages (migrated from deprecated langchain.chat_models/embeddings)
try:
    from langchain_openai import ChatOpenAI, OpenAI, OpenAIEmbeddings
except ImportError:
    ChatOpenAI = None  # type: ignore
    OpenAI = None  # type: ignore
    OpenAIEmbeddings = None  # type: ignore

try:
    from langchain_anthropic import ChatAnthropic
except ImportError:
    ChatAnthropic = None  # type: ignore

try:
    from langchain_huggingface import HuggingFaceEmbeddings
except ImportError:
    from langchain_community.embeddings import HuggingFaceEmbeddings

from langchain.tools import Tool

# Global langchain cache setting
import langchain

# OpenAIFunctionsAgent import removed - deprecated

logger = logging.getLogger(__name__)


class LangChainConfig:
    """LangChain configuration"""

    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "")
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY", "")
        self.huggingface_api_key = os.getenv("HUGGINGFACEHUB_API_TOKEN", "")
        self.cohere_api_key = os.getenv("COHERE_API_KEY", "")

        self.model_name = os.getenv("LLM_MODEL", "gpt-3.5-turbo")
        self.temperature = float(os.getenv("LLM_TEMPERATURE", "0.7"))
        self.max_tokens = int(os.getenv("LLM_MAX_TOKENS", "2000"))

        self.embedding_model = os.getenv("EMBEDDING_MODEL", "text-embedding-ada-002")
        self.vector_store_type = os.getenv("VECTOR_STORE", "faiss")

        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        self.enable_cache = os.getenv("ENABLE_LLM_CACHE", "true").lower() == "true"

        self.enable_streaming = os.getenv("ENABLE_STREAMING", "false").lower() == "true"
        self.verbose = os.getenv("LANGCHAIN_VERBOSE", "false").lower() == "true"


class LangChainLLMService:
    """LangChain-based LLM service"""

    def __init__(self, config: LangChainConfig | None = None):
        self.config = config or LangChainConfig()
        self.llm = None
        self.chat_model = None
        self.embeddings = None
        self.memory_stores = {}
        self.vector_stores = {}
        self.chains = {}
        self.agents = {}

        self._initialize()

    def _initialize(self):
        """Initialize LangChain components"""

        # Set up caching
        if self.config.enable_cache:
            try:
                langchain.llm_cache = RedisCache(redis_url=self.config.redis_url)
                logger.info("Redis cache enabled for LangChain")
            except (ConnectionError, OSError, Exception) as e:
                logger.warning(f"Redis cache unavailable ({e}), falling back to in-memory")
                langchain.llm_cache = InMemoryCache()
                logger.info("In-memory cache enabled for LangChain")

        # Initialize LLMs
        self._initialize_llms()

        # Initialize embeddings
        self._initialize_embeddings()

        # Initialize default memory
        self._initialize_memory()

        logger.info("LangChain LLM Service initialized")

    def _initialize_llms(self):
        """Initialize LLM models"""

        callbacks = (
            [StreamingStdOutCallbackHandler()] if self.config.enable_streaming else []
        )

        # OpenAI models
        if self.config.openai_api_key:
            self.chat_model = ChatOpenAI(
                model_name=self.config.model_name,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                openai_api_key=self.config.openai_api_key,
                callbacks=callbacks,
                verbose=self.config.verbose,
            )

            self.llm = OpenAI(
                model_name="text-davinci-003",
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                openai_api_key=self.config.openai_api_key,
                callbacks=callbacks,
            )

        # Anthropic models
        elif self.config.anthropic_api_key:
            self.chat_model = ChatAnthropic(
                model="claude-2",
                temperature=self.config.temperature,
                max_tokens_to_sample=self.config.max_tokens,
                anthropic_api_key=self.config.anthropic_api_key,
                callbacks=callbacks,
            )

        # HuggingFace models
        elif self.config.huggingface_api_key:
            self.llm = HuggingFaceHub(
                repo_id="google/flan-t5-xl",
                huggingfacehub_api_token=self.config.huggingface_api_key,
                model_kwargs={
                    "temperature": self.config.temperature,
                    "max_length": self.config.max_tokens,
                },
            )

        # Default to mock model
        if not self.chat_model and not self.llm:
            logger.warning("No LLM API keys found, using mock model")
            self.llm = self._create_mock_llm()

    def _initialize_embeddings(self):
        """Initialize embedding models"""

        if self.config.openai_api_key:
            self.embeddings = OpenAIEmbeddings(
                model=self.config.embedding_model,
                openai_api_key=self.config.openai_api_key,
            )
        else:
            # Use free HuggingFace embeddings
            self.embeddings = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2"
            )

    def _initialize_memory(self):
        """Initialize memory systems"""

        # Conversation buffer memory
        self.memory_stores["buffer"] = ConversationBufferMemory(
            return_messages=True, memory_key="chat_history"
        )

        # Window memory (last N turns)
        self.memory_stores["window"] = ConversationBufferWindowMemory(
            k=10, return_messages=True, memory_key="chat_history"  # Keep last 10 turns
        )

        # Summary memory
        if self.llm:
            self.memory_stores["summary"] = ConversationSummaryMemory(
                llm=self.llm, return_messages=True, memory_key="chat_history"
            )

            # Summary buffer memory
            self.memory_stores["summary_buffer"] = ConversationSummaryBufferMemory(
                llm=self.llm,
                max_token_limit=2000,
                return_messages=True,
                memory_key="chat_history",
            )

    def _create_mock_llm(self):
        """Create mock LLM for testing"""

        class MockLLM:
            def __call__(self, prompt):
                return f"Mock response for: {prompt[:50]}..."

            def predict(self, prompt):
                return self(prompt)

            def predict_messages(self, messages):
                return AIMessage(content="Mock response")

        return MockLLM()

    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        memory_type: str = "buffer",
        **kwargs,
    ) -> dict[str, Any]:
        """Generate response using LangChain"""

        try:
            # Get or create memory
            memory = self.memory_stores.get(memory_type, self.memory_stores["buffer"])

            # Create prompt template
            if system_prompt:
                messages = [
                    SystemMessagePromptTemplate.from_template(system_prompt),
                    MessagesPlaceholder(variable_name="chat_history"),
                    HumanMessagePromptTemplate.from_template("{input}"),
                ]
                prompt_template = ChatPromptTemplate.from_messages(messages)
            else:
                prompt_template = ChatPromptTemplate.from_messages(
                    [
                        MessagesPlaceholder(variable_name="chat_history"),
                        HumanMessagePromptTemplate.from_template("{input}"),
                    ]
                )

            # Create conversation chain
            if self.chat_model:
                chain = LLMChain(
                    llm=self.chat_model,
                    prompt=prompt_template,
                    memory=memory,
                    verbose=self.config.verbose,
                )
            else:
                chain = LLMChain(
                    llm=self.llm,
                    prompt=prompt_template,
                    memory=memory,
                    verbose=self.config.verbose,
                )

            # Generate response
            response = await chain.apredict(input=prompt, **kwargs)

            return {
                "success": True,
                "response": response,
                "memory": memory.chat_memory.messages,
                "model": self.config.model_name,
            }

        except Exception as e:
            logger.error(f"LangChain generation error: {e}")
            return {"success": False, "error": str(e)}

    async def generate_with_tools(
        self, prompt: str, tools: list[str] = None, **kwargs
    ) -> dict[str, Any]:
        """Generate response using LangChain agent with tools"""

        try:
            # Load tools
            if not tools:
                tools = ["ddg-search", "wikipedia"]

            loaded_tools = []

            # Add search tools
            if "ddg-search" in tools:
                search = DuckDuckGoSearchRun()
                loaded_tools.append(
                    Tool(
                        name="Search",
                        func=search.run,
                        description="Search the web for current information",
                    )
                )

            if "wikipedia" in tools:
                wiki = WikipediaQueryRun()
                loaded_tools.append(
                    Tool(
                        name="Wikipedia",
                        func=wiki.run,
                        description="Search Wikipedia for detailed information",
                    )
                )

            # Create agent using modern LangChain patterns
            from langchain.agents import create_openai_functions_agent, create_react_agent
            from langchain import hub

            if self.chat_model and ChatOpenAI is not None:
                # Use OpenAI functions agent for compatible models
                try:
                    prompt_template = hub.pull("hwchase17/openai-functions-agent")
                    agent = create_openai_functions_agent(
                        llm=self.chat_model, tools=loaded_tools, prompt=prompt_template
                    )
                except Exception as e:
                    logger.warning(f"OpenAI functions agent failed: {e}, using ReAct")
                    prompt_template = hub.pull("hwchase17/react")
                    agent = create_react_agent(
                        llm=self.chat_model, tools=loaded_tools, prompt=prompt_template
                    )
            else:
                # Use ReAct agent for non-OpenAI models
                prompt_template = hub.pull("hwchase17/react")
                agent = create_react_agent(
                    llm=self.llm, tools=loaded_tools, prompt=prompt_template
                )

            # Create executor
            executor = AgentExecutor(
                agent=agent,
                tools=loaded_tools,
                verbose=self.config.verbose,
                max_iterations=5,
            )

            # Run agent
            response = await executor.arun(input=prompt)

            return {
                "success": True,
                "response": response,
                "tools_used": [tool.name for tool in loaded_tools],
            }

        except Exception as e:
            logger.error(f"Agent execution error: {e}")
            return {"success": False, "error": str(e)}

    def create_vector_store(
        self,
        documents: list[str],
        store_name: str = "default",
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
    ) -> Any:
        """Create vector store for RAG"""

        try:
            # Split documents
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size, chunk_overlap=chunk_overlap
            )

            docs = []
            for i, doc_text in enumerate(documents):
                chunks = text_splitter.split_text(doc_text)
                for chunk in chunks:
                    docs.append(
                        Document(page_content=chunk, metadata={"source": f"doc_{i}"})
                    )

            # Create vector store
            if self.config.vector_store_type == "chroma":
                vector_store = Chroma.from_documents(
                    documents=docs,
                    embedding=self.embeddings,
                    collection_name=store_name,
                )
            else:  # Default to FAISS
                vector_store = FAISS.from_documents(
                    documents=docs, embedding=self.embeddings
                )

            self.vector_stores[store_name] = vector_store

            logger.info(f"Created vector store '{store_name}' with {len(docs)} chunks")
            return vector_store

        except Exception as e:
            logger.error(f"Vector store creation error: {e}")
            return None

    def create_rag_chain(
        self,
        vector_store_name: str = "default",
        chain_type: str = "stuff",
        return_source_documents: bool = True,
    ) -> Any:
        """Create RAG (Retrieval-Augmented Generation) chain"""

        try:
            vector_store = self.vector_stores.get(vector_store_name)
            if not vector_store:
                logger.error(f"Vector store '{vector_store_name}' not found")
                return None

            # Create retriever
            retriever = vector_store.as_retriever(
                search_type="similarity", search_kwargs={"k": 4}
            )

            # Create RAG chain
            if self.chat_model:
                rag_chain = RetrievalQA.from_chain_type(
                    llm=self.chat_model,
                    chain_type=chain_type,
                    retriever=retriever,
                    return_source_documents=return_source_documents,
                    verbose=self.config.verbose,
                )
            else:
                rag_chain = RetrievalQA.from_chain_type(
                    llm=self.llm,
                    chain_type=chain_type,
                    retriever=retriever,
                    return_source_documents=return_source_documents,
                    verbose=self.config.verbose,
                )

            self.chains[f"rag_{vector_store_name}"] = rag_chain

            logger.info(f"Created RAG chain for '{vector_store_name}'")
            return rag_chain

        except Exception as e:
            logger.error(f"RAG chain creation error: {e}")
            return None

    def create_conversational_rag_chain(
        self, vector_store_name: str = "default"
    ) -> Any:
        """Create conversational RAG chain with memory"""

        try:
            vector_store = self.vector_stores.get(vector_store_name)
            if not vector_store:
                logger.error(f"Vector store '{vector_store_name}' not found")
                return None

            # Create retriever
            retriever = vector_store.as_retriever()

            # Create memory
            memory = ConversationBufferMemory(
                memory_key="chat_history", return_messages=True, output_key="answer"
            )

            # Create conversational chain
            if self.chat_model:
                conv_chain = ConversationalRetrievalChain.from_llm(
                    llm=self.chat_model,
                    retriever=retriever,
                    memory=memory,
                    return_source_documents=True,
                    verbose=self.config.verbose,
                )
            else:
                conv_chain = ConversationalRetrievalChain.from_llm(
                    llm=self.llm,
                    retriever=retriever,
                    memory=memory,
                    return_source_documents=True,
                    verbose=self.config.verbose,
                )

            self.chains[f"conv_rag_{vector_store_name}"] = conv_chain

            logger.info(f"Created conversational RAG chain for '{vector_store_name}'")
            return conv_chain

        except Exception as e:
            logger.error(f"Conversational RAG chain creation error: {e}")
            return None

    async def query_rag(
        self, query: str, chain_name: str = "rag_default"
    ) -> dict[str, Any]:
        """Query RAG chain"""

        try:
            chain = self.chains.get(chain_name)
            if not chain:
                return {"success": False, "error": f"Chain '{chain_name}' not found"}

            # Run query
            result = await chain.arun(query)

            # Get source documents if available
            source_docs = []
            if (
                hasattr(chain, "return_source_documents")
                and chain.return_source_documents
            ):
                if hasattr(result, "source_documents"):
                    source_docs = [
                        {"content": doc.page_content[:200], "metadata": doc.metadata}
                        for doc in result.source_documents
                    ]

            return {
                "success": True,
                "response": result
                if isinstance(result, str)
                else result.get("answer", str(result)),
                "source_documents": source_docs,
            }

        except Exception as e:
            logger.error(f"RAG query error: {e}")
            return {"success": False, "error": str(e)}

    def create_custom_chain(
        self,
        chain_name: str,
        prompt_template: str,
        input_variables: list[str],
        memory_type: str = "buffer",
    ) -> Any:
        """Create custom LangChain chain"""

        try:
            # Create prompt
            prompt = ChatPromptTemplate.from_template(prompt_template)

            # Get memory
            memory = self.memory_stores.get(memory_type, self.memory_stores["buffer"])

            # Create chain
            if self.chat_model:
                chain = LLMChain(
                    llm=self.chat_model,
                    prompt=prompt,
                    memory=memory,
                    verbose=self.config.verbose,
                )
            else:
                chain = LLMChain(
                    llm=self.llm,
                    prompt=prompt,
                    memory=memory,
                    verbose=self.config.verbose,
                )

            self.chains[chain_name] = chain

            logger.info(f"Created custom chain '{chain_name}'")
            return chain

        except Exception as e:
            logger.error(f"Custom chain creation error: {e}")
            return None

    def get_conversation_summary(self, memory_type: str = "buffer") -> str:
        """Get conversation summary"""

        memory = self.memory_stores.get(memory_type)
        if not memory:
            return "No conversation history"

        if hasattr(memory, "moving_summary_buffer"):
            return memory.moving_summary_buffer

        messages = memory.chat_memory.messages
        if not messages:
            return "No messages in history"

        summary = []
        for msg in messages[-5:]:  # Last 5 messages
            if isinstance(msg, HumanMessage):
                summary.append(f"Human: {msg.content[:100]}...")
            elif isinstance(msg, AIMessage):
                summary.append(f"AI: {msg.content[:100]}...")

        return "\n".join(summary)

    def clear_memory(self, memory_type: str | None = None):
        """Clear conversation memory"""

        if memory_type:
            if memory_type in self.memory_stores:
                self.memory_stores[memory_type].clear()
                logger.info(f"Cleared {memory_type} memory")
        else:
            # Clear all memories
            for mem_type, memory in self.memory_stores.items():
                memory.clear()
            logger.info("Cleared all memories")


# Singleton instance
_langchain_service = None


def get_langchain_service() -> LangChainLLMService:
    """Get or create LangChain service singleton"""
    global _langchain_service

    if _langchain_service is None:
        _langchain_service = LangChainLLMService()

    return _langchain_service


# Example usage
async def example_usage():
    """Example of using LangChain service"""

    service = get_langchain_service()

    # Basic generation
    result = await service.generate(
        "Explain quantum computing", system_prompt="You are a physics teacher"
    )
    print(f"Response: {result['response']}")

    # Generation with tools
    result = await service.generate_with_tools(
        "What is the current weather in Istanbul?"
    )
    print(f"Agent response: {result['response']}")

    # Create vector store for RAG
    documents = [
        "Istanbul is the largest city in Turkey.",
        "The Bosphorus divides Istanbul between Europe and Asia.",
        "Istanbul was formerly known as Constantinople.",
    ]

    vector_store = service.create_vector_store(documents, "istanbul_facts")

    # Create RAG chain
    rag_chain = service.create_rag_chain("istanbul_facts")

    # Query RAG
    result = await service.query_rag("What divides Istanbul?", "rag_istanbul_facts")
    print(f"RAG response: {result['response']}")


if __name__ == "__main__":
    asyncio.run(example_usage())

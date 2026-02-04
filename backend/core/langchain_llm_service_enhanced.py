"""
Enhanced LangChain LLM Service with Custom Endpoints
Supports Anthropic, HuggingFace Hub, and Custom HF Endpoints
"""

import asyncio
import logging
import os
from typing import Any

import requests

# LangChain imports
try:
    # Try new imports first, fallback to old ones
    try:
        from langchain_community.chat_models import ChatAnthropic, ChatOpenAI
        from langchain_community.embeddings import (
            HuggingFaceEmbeddings,
            OpenAIEmbeddings,
        )
        from langchain_community.llms import Anthropic, HuggingFaceHub, OpenAI
    except ImportError:
        # Fallback to old imports
        from langchain.chat_models import ChatAnthropic, ChatOpenAI
        from langchain.embeddings import HuggingFaceEmbeddings, OpenAIEmbeddings
        from langchain.llms import Anthropic, HuggingFaceHub, OpenAI

    from langchain.chains import LLMChain, RetrievalQA
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
    )
    from langchain.schema import Document

    # Try new callback imports
    try:
        from langchain.callbacks.manager import CallbackManager
        from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
    except ImportError:
        try:
            from langchain.callbacks import StreamingStdOutCallbackHandler

            CallbackManager = None  # Not available in newer versions
        except ImportError:
            CallbackManager = None
            StreamingStdOutCallbackHandler = None

    from langchain.cache import InMemoryCache

    try:
        from langchain.cache import RedisCache
    except ImportError:
        RedisCache = None

    import langchain
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from langchain.vectorstores import FAISS, Chroma

    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    print("[WARNING] LangChain not installed. Using mock implementation.")

logger = logging.getLogger(__name__)


class LangChainConfig:
    """Enhanced LangChain configuration with custom endpoints"""

    def __init__(self):
        # API Keys
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "")
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY", "")
        self.huggingface_api_key = os.getenv("HUGGINGFACEHUB_API_TOKEN", "")
        self.cohere_api_key = os.getenv("COHERE_API_KEY", "")

        # Custom HuggingFace Endpoint
        self.custom_hf_endpoint = os.getenv(
            "CUSTOM_HF_ENDPOINT",
            "https://cf781mfqobm2ynkk.us-east-1.aws.endpoints.huggingface.cloud",
        )

        # Model settings
        self.model_name = os.getenv("LLM_MODEL", "gpt-3.5-turbo")
        self.hf_model_id = os.getenv("HF_MODEL_ID", "meta-llama/Llama-2-7b-chat-hf")
        self.anthropic_model = os.getenv("ANTHROPIC_MODEL", "claude-2")

        self.temperature = float(os.getenv("LLM_TEMPERATURE", "0.7"))
        self.max_tokens = int(os.getenv("LLM_MAX_TOKENS", "2000"))

        # Embedding settings
        self.embedding_model = os.getenv("EMBEDDING_MODEL", "text-embedding-ada-002")
        self.hf_embedding_model = os.getenv(
            "HF_EMBEDDING_MODEL",
            "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        )

        # Vector store settings
        self.vector_store_type = os.getenv("VECTOR_STORE", "faiss")

        # Cache settings
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        self.enable_cache = os.getenv("ENABLE_LLM_CACHE", "true").lower() == "true"

        # Other settings
        self.enable_streaming = os.getenv("ENABLE_STREAMING", "false").lower() == "true"
        self.verbose = os.getenv("LANGCHAIN_VERBOSE", "true").lower() == "true"


class CustomHuggingFaceEndpoint:
    """Custom HuggingFace Endpoint wrapper for LangChain"""

    def __init__(self, endpoint_url: str, api_token: str = None, **kwargs):
        self.endpoint_url = endpoint_url
        self.api_token = api_token
        self.temperature = kwargs.get("temperature", 0.7)
        self.max_tokens = kwargs.get("max_tokens", 512)
        self.headers = {
            "Authorization": f"Bearer {api_token}" if api_token else "",
            "Content-Type": "application/json",
        }

    def __call__(self, prompt: str) -> str:
        """Call the endpoint"""
        return self.generate(prompt)

    def generate(self, prompt: str) -> str:
        """Generate response from custom endpoint"""
        payload = {
            "inputs": prompt,
            "parameters": {
                "temperature": self.temperature,
                "max_new_tokens": self.max_tokens,
                "do_sample": True,
                "top_p": 0.95,
                "top_k": 50,
            },
        }

        try:
            response = requests.post(
                self.endpoint_url, headers=self.headers, json=payload, timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                if isinstance(result, list) and len(result) > 0:
                    return result[0].get("generated_text", "")
                if isinstance(result, dict):
                    return result.get("generated_text", "")
                return str(result)
            logger.error(f"Endpoint error: {response.status_code} - {response.text}")
            return f"Error: {response.status_code}"

        except Exception as e:
            logger.error(f"Custom endpoint error: {e}")
            return f"Error: {e!s}"

    async def agenerate(self, prompt: str) -> str:
        """Async generation"""
        return self.generate(prompt)

    def predict(self, text: str) -> str:
        """Predict method for compatibility"""
        return self.generate(text)


class EnhancedLangChainLLMService:
    """Enhanced LangChain service with multiple model support"""

    def __init__(self, config: LangChainConfig | None = None):
        self.config = config or LangChainConfig()
        self.models = {}
        self.chat_models = {}
        self.embeddings = {}
        self.memory_stores = {}
        self.vector_stores = {}
        self.chains = {}

        self._initialize()

    def _initialize(self):
        """Initialize all components"""

        if not LANGCHAIN_AVAILABLE:
            logger.warning("LangChain not available, using mock implementation")
            self._initialize_mock()
            return

        # Set up caching
        if self.config.enable_cache:
            try:
                langchain.llm_cache = RedisCache(redis_url=self.config.redis_url)
                logger.info("[CHECK] Redis cache enabled")
            except:
                langchain.llm_cache = InMemoryCache()
                logger.info("[CHECK] In-memory cache enabled")

        # Initialize models
        self._initialize_all_models()

        # Initialize embeddings
        self._initialize_embeddings()

        # Initialize memory stores
        self._initialize_memory()

        logger.info("[CHECK] Enhanced LangChain Service initialized")

    def _initialize_all_models(self):
        """Initialize all available models"""

        callbacks = (
            [StreamingStdOutCallbackHandler()] if self.config.enable_streaming else []
        )

        # 1. Anthropic Claude
        if self.config.anthropic_api_key:
            try:
                # Claude chat model
                self.chat_models["anthropic"] = ChatAnthropic(
                    model=self.config.anthropic_model,
                    temperature=self.config.temperature,
                    max_tokens_to_sample=self.config.max_tokens,
                    anthropic_api_key=self.config.anthropic_api_key,
                    callbacks=callbacks,
                )

                # Claude completion model
                self.models["anthropic"] = Anthropic(
                    model=self.config.anthropic_model,
                    temperature=self.config.temperature,
                    max_tokens_to_sample=self.config.max_tokens,
                    anthropic_api_key=self.config.anthropic_api_key,
                )

                logger.info("[CHECK] Anthropic Claude initialized")
            except Exception as e:
                logger.error(f"[X] Anthropic initialization failed: {e}")

        # 2. HuggingFace Hub
        if self.config.huggingface_api_key:
            try:
                # Standard HuggingFace Hub
                self.models["huggingface"] = HuggingFaceHub(
                    repo_id=self.config.hf_model_id,
                    huggingfacehub_api_token=self.config.huggingface_api_key,
                    model_kwargs={
                        "temperature": self.config.temperature,
                        "max_new_tokens": self.config.max_tokens,
                        "top_p": 0.95,
                    },
                )
                logger.info(
                    f"[CHECK] HuggingFace Hub initialized with {self.config.hf_model_id}"
                )
            except Exception as e:
                logger.error(f"[X] HuggingFace Hub initialization failed: {e}")

        # 3. Custom HuggingFace Endpoint
        if self.config.custom_hf_endpoint:
            try:
                # Try using HuggingFaceEndpoint if available
                try:
                    from langchain.llms import HuggingFaceEndpoint

                    self.models["custom_hf"] = HuggingFaceEndpoint(
                        endpoint_url=self.config.custom_hf_endpoint,
                        huggingfacehub_api_token=self.config.huggingface_api_key,
                        model_kwargs={
                            "temperature": self.config.temperature,
                            "max_new_tokens": self.config.max_tokens,
                        },
                    )
                except ImportError:
                    # Fallback to custom implementation
                    self.models["custom_hf"] = CustomHuggingFaceEndpoint(
                        endpoint_url=self.config.custom_hf_endpoint,
                        api_token=self.config.huggingface_api_key,
                        temperature=self.config.temperature,
                        max_tokens=self.config.max_tokens,
                    )

                logger.info(
                    f"[CHECK] Custom HF Endpoint initialized: {self.config.custom_hf_endpoint[:50]}..."
                )
            except Exception as e:
                logger.error(f"[X] Custom HF Endpoint initialization failed: {e}")

        # 4. OpenAI (if available)
        if self.config.openai_api_key:
            try:
                self.chat_models["openai"] = ChatOpenAI(
                    model_name=self.config.model_name,
                    temperature=self.config.temperature,
                    max_tokens=self.config.max_tokens,
                    openai_api_key=self.config.openai_api_key,
                    callbacks=callbacks,
                    verbose=self.config.verbose,
                )

                self.models["openai"] = OpenAI(
                    model_name="text-davinci-003",
                    temperature=self.config.temperature,
                    max_tokens=self.config.max_tokens,
                    openai_api_key=self.config.openai_api_key,
                )

                logger.info("[CHECK] OpenAI models initialized")
            except Exception as e:
                logger.error(f"[X] OpenAI initialization failed: {e}")

        # Set default model
        if not self.models:
            # Create a mock model if none available
            self.models["mock"] = self._create_mock_model()
            logger.warning("⚠️ No models available, using mock")

    def _initialize_embeddings(self):
        """Initialize embedding models"""

        # OpenAI embeddings
        if self.config.openai_api_key:
            try:
                self.embeddings["openai"] = OpenAIEmbeddings(
                    model=self.config.embedding_model,
                    openai_api_key=self.config.openai_api_key,
                )
                logger.info("[CHECK] OpenAI embeddings initialized")
            except:
                pass

        # HuggingFace embeddings (always available)
        try:
            self.embeddings["huggingface"] = HuggingFaceEmbeddings(
                model_name=self.config.hf_embedding_model,
                model_kwargs={"device": "cpu"},
                encode_kwargs={"normalize_embeddings": True},
            )
            logger.info(
                f"[CHECK] HuggingFace embeddings initialized: {self.config.hf_embedding_model}"
            )
        except Exception as e:
            logger.error(f"[X] HuggingFace embeddings failed: {e}")

    def _initialize_memory(self):
        """Initialize memory stores"""

        # Buffer memory
        self.memory_stores["buffer"] = ConversationBufferMemory(
            return_messages=True, memory_key="chat_history"
        )

        # Window memory
        self.memory_stores["window"] = ConversationBufferWindowMemory(
            k=10, return_messages=True, memory_key="chat_history"
        )

        # Summary memory (if LLM available)
        if self.models:
            llm = list(self.models.values())[0]

            self.memory_stores["summary"] = ConversationSummaryMemory(
                llm=llm, return_messages=True, memory_key="chat_history"
            )

            self.memory_stores["summary_buffer"] = ConversationSummaryBufferMemory(
                llm=llm,
                max_token_limit=2000,
                return_messages=True,
                memory_key="chat_history",
            )

        logger.info(
            f"[CHECK] Memory stores initialized: {list(self.memory_stores.keys())}"
        )

    def _create_mock_model(self):
        """Create a mock model for testing"""

        class MockLLM:
            def __call__(self, prompt):
                return f"[Mock Response] {prompt[:50]}..."

            def predict(self, text):
                return self(text)

            async def apredict(self, text):
                return self(text)

        return MockLLM()

    def _initialize_mock(self):
        """Initialize mock components when LangChain not available"""
        self.models["mock"] = self._create_mock_model()
        self.embeddings["mock"] = None
        self.memory_stores["buffer"] = {"messages": []}
        logger.info("[CHECK] Mock components initialized")

    async def generate(
        self,
        prompt: str,
        model_type: str = "auto",
        memory_type: str = "buffer",
        **kwargs,
    ) -> dict[str, Any]:
        """Generate response using specified model"""

        try:
            # Select model
            if model_type == "auto":
                # Priority: Anthropic > HuggingFace > Custom HF > OpenAI > Mock
                if "anthropic" in self.models:
                    model_type = "anthropic"
                elif "huggingface" in self.models:
                    model_type = "huggingface"
                elif "custom_hf" in self.models:
                    model_type = "custom_hf"
                elif "openai" in self.models:
                    model_type = "openai"
                else:
                    model_type = "mock"

            model = self.models.get(model_type) or self.chat_models.get(model_type)

            if not model:
                return {
                    "success": False,
                    "error": f"Model type '{model_type}' not available",
                }

            # Get memory
            memory = self.memory_stores.get(memory_type, self.memory_stores["buffer"])

            # Create prompt template
            prompt_template = ChatPromptTemplate.from_messages(
                [
                    MessagesPlaceholder(variable_name="chat_history"),
                    HumanMessagePromptTemplate.from_template("{input}"),
                ]
            )

            # Create chain
            if LANGCHAIN_AVAILABLE:
                chain = LLMChain(
                    llm=model,
                    prompt=prompt_template,
                    memory=memory,
                    verbose=self.config.verbose,
                )

                response = await chain.apredict(input=prompt, **kwargs)
            else:
                # Mock response
                response = model(prompt)

            return {
                "success": True,
                "response": response,
                "model_used": model_type,
                "memory_type": memory_type,
            }

        except Exception as e:
            logger.error(f"Generation error: {e}")
            return {"success": False, "error": str(e)}

    def create_vector_store(
        self,
        documents: list[str],
        store_name: str = "default",
        store_type: str = "faiss",
    ) -> Any:
        """Create vector store for RAG"""

        if not LANGCHAIN_AVAILABLE:
            logger.warning("LangChain not available for vector store")
            return None

        try:
            # Get embeddings
            embeddings = self.embeddings.get("huggingface") or self.embeddings.get(
                "openai"
            )

            if not embeddings:
                logger.error("No embeddings available")
                return None

            # Create documents
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000, chunk_overlap=200
            )

            docs = []
            for i, text in enumerate(documents):
                chunks = text_splitter.split_text(text)
                for chunk in chunks:
                    docs.append(
                        Document(page_content=chunk, metadata={"source": f"doc_{i}"})
                    )

            # Create vector store
            if store_type == "chroma":
                vector_store = Chroma.from_documents(
                    documents=docs, embedding=embeddings, collection_name=store_name
                )
            else:  # Default to FAISS
                vector_store = FAISS.from_documents(
                    documents=docs, embedding=embeddings
                )

            self.vector_stores[store_name] = vector_store
            logger.info(
                f"[CHECK] Vector store '{store_name}' created with {len(docs)} chunks"
            )

            return vector_store

        except Exception as e:
            logger.error(f"Vector store creation error: {e}")
            return None

    def create_rag_chain(
        self, store_name: str = "default", model_type: str = "auto"
    ) -> Any:
        """Create RAG chain"""

        if not LANGCHAIN_AVAILABLE:
            return None

        vector_store = self.vector_stores.get(store_name)
        if not vector_store:
            logger.error(f"Vector store '{store_name}' not found")
            return None

        # Select model
        if model_type == "auto":
            model = (
                self.models.get("anthropic")
                or self.models.get("huggingface")
                or self.models.get("custom_hf")
                or self.models.get("openai")
                or self.models.get("mock")
            )
        else:
            model = self.models.get(model_type) or self.chat_models.get(model_type)

        if not model:
            logger.error("No model available for RAG")
            return None

        # Create RAG chain
        rag_chain = RetrievalQA.from_chain_type(
            llm=model,
            chain_type="stuff",
            retriever=vector_store.as_retriever(),
            return_source_documents=True,
            verbose=self.config.verbose,
        )

        self.chains[f"rag_{store_name}"] = rag_chain
        logger.info(f"[CHECK] RAG chain created for '{store_name}'")

        return rag_chain

    def get_available_models(self) -> dict[str, str]:
        """Get list of available models"""
        available = {}

        for name in self.models:
            available[name] = "LLM"

        for name in self.chat_models:
            available[f"{name}_chat"] = "Chat Model"

        return available

    def get_system_status(self) -> dict[str, Any]:
        """Get system status"""
        return {
            "langchain_available": LANGCHAIN_AVAILABLE,
            "models": self.get_available_models(),
            "embeddings": list(self.embeddings.keys()),
            "memory_types": list(self.memory_stores.keys()),
            "vector_stores": list(self.vector_stores.keys()),
            "chains": list(self.chains.keys()),
            "cache_enabled": self.config.enable_cache,
            "streaming_enabled": self.config.enable_streaming,
            "custom_endpoint": self.config.custom_hf_endpoint[:50] + "..."
            if self.config.custom_hf_endpoint
            else None,
        }


# Singleton instance
_enhanced_service = None


def get_enhanced_langchain_service() -> EnhancedLangChainLLMService:
    """Get or create enhanced LangChain service"""
    global _enhanced_service

    if _enhanced_service is None:
        _enhanced_service = EnhancedLangChainLLMService()

    return _enhanced_service


# Test function
async def test_enhanced_service():
    """Test the enhanced service"""

    service = get_enhanced_langchain_service()

    print("\n[MAG] System Status:")
    status = service.get_system_status()
    for key, value in status.items():
        print(f"  {key}: {value}")

    print("\n[MEMO] Testing generation with different models:")

    # Test Anthropic
    result = await service.generate("What is machine learning?", model_type="anthropic")
    print(f"\n🤖 Anthropic: {result}")

    # Test HuggingFace
    result = await service.generate("Explain deep learning", model_type="huggingface")
    print(f"\n🤗 HuggingFace: {result}")

    # Test Custom HF Endpoint
    result = await service.generate(
        "What is natural language processing?", model_type="custom_hf"
    )
    print(f"\n[GLOBE] Custom Endpoint: {result}")

    # Test auto selection
    result = await service.generate("Explain AI", model_type="auto")
    print(f"\n[TARGET] Auto-selected: {result}")

    return True


if __name__ == "__main__":
    asyncio.run(test_enhanced_service())

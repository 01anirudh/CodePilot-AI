from typing import Optional
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.llms import Ollama
from langchain_core.language_models import BaseChatModel
from langchain_core.embeddings import Embeddings
from app.config import settings


def get_llm(temperature: float = 0.1, streaming: bool = False) -> BaseChatModel:
    """Return configured LLM based on settings."""
    provider = settings.LLM_PROVIDER.lower()

    if provider == "openai":
        return ChatOpenAI(
            model=settings.OPENAI_MODEL,
            api_key=settings.OPENAI_API_KEY,
            temperature=temperature,
            streaming=streaming,
        )
    elif provider == "gemini":
        return ChatGoogleGenerativeAI(
            model=settings.GEMINI_MODEL,
            google_api_key=settings.GEMINI_API_KEY,
            temperature=temperature,
        )
    elif provider == "ollama":
        return ChatOpenAI(
            model=settings.OLLAMA_MODEL,
            base_url=f"{settings.OLLAMA_BASE_URL}/v1",
            api_key="ollama",
            temperature=temperature,
            streaming=streaming,
        )
    else:
        raise ValueError(f"Unknown LLM provider: {provider}")


def get_embeddings() -> Embeddings:
    """Return configured embedding model."""
    provider = settings.LLM_PROVIDER.lower()

    if provider == "openai":
        return OpenAIEmbeddings(
            model=settings.EMBEDDING_MODEL,
            api_key=settings.OPENAI_API_KEY,
        )
    elif provider in ("gemini", "ollama"):
        # Fallback to OpenAI embeddings if key present, else mock
        if settings.OPENAI_API_KEY:
            return OpenAIEmbeddings(
                model=settings.EMBEDDING_MODEL,
                api_key=settings.OPENAI_API_KEY,
            )
        # Return a mock for development
        return _MockEmbeddings()
    else:
        return _MockEmbeddings()


class _MockEmbeddings(Embeddings):
    """Mock embeddings for development without API keys."""

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        import random
        return [[random.random() for _ in range(1536)] for _ in texts]

    def embed_query(self, text: str) -> list[float]:
        import random
        return [random.random() for _ in range(1536)]

from typing import Optional

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.llms import Ollama
from langchain_core.language_models import BaseChatModel
from langchain_core.embeddings import Embeddings
from app.config import settings


from langchain_core.language_models.chat_models import SimpleChatModel
from langchain_core.messages import BaseMessage


class _MockChatModel(SimpleChatModel):
    """Mock LLM for test and development environments when API keys are not configured."""

    def _call(self, messages: list[BaseMessage], stop: Optional[list[str]] = None, **kwargs) -> str:
        last_msg = messages[-1].content if messages else ""
        if "Supervisor" in last_msg or "supervisor" in str(messages):
            return '{"next": "finish", "reason": "All tasks completed (mock mode)"}'
        if "execution plan" in last_msg.lower() or "planner" in str(messages).lower():
            return '{"task_summary": "Plan created", "steps": [{"step": 1, "agent": "codegen", "action": "Generate code", "input": "task", "output": "code", "depends_on": []}], "complexity": "low", "estimated_duration_minutes": 5}'
        if "codegen" in last_msg.lower() or "generate" in last_msg.lower():
            return '{"files": [{"path": "main.py", "action": "create", "content": "# Generated code", "description": "Initial scaffold"}], "summary": "Generated files"}'
        return '{"status": "completed", "summary": "Simulated AI response", "files": []}'

    @property
    def _llm_type(self) -> str:
        return "mock"


def get_llm(temperature: float = 0.1, streaming: bool = False) -> BaseChatModel:
    """Return configured LLM based on settings."""
    provider = settings.LLM_PROVIDER.lower()

    if provider == "openai":
        if not settings.OPENAI_API_KEY:
            return _MockChatModel()
        return ChatOpenAI(
            model=settings.OPENAI_MODEL,
            api_key=settings.OPENAI_API_KEY,
            temperature=temperature,
            streaming=streaming,
            request_timeout=30.0,
            max_retries=2,
        )
    elif provider == "gemini":
        if not settings.GEMINI_API_KEY:
            return _MockChatModel()
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
            request_timeout=30.0,
        )
    else:
        return _MockChatModel()



def get_embeddings() -> Embeddings:
    """Return configured embedding model."""
    provider = settings.LLM_PROVIDER.lower()

    if provider == "openai" and settings.OPENAI_API_KEY:
        return OpenAIEmbeddings(
            model=settings.EMBEDDING_MODEL,
            api_key=settings.OPENAI_API_KEY,
        )
    elif provider == "gemini" and settings.GEMINI_API_KEY:
        from langchain_google_genai import GoogleGenerativeAIEmbeddings
        return GoogleGenerativeAIEmbeddings(
            model="models/embedding-001",
            google_api_key=settings.GEMINI_API_KEY,
        )
    # Fallback mock for development without valid API keys
    return _MockEmbeddings()


class _MockEmbeddings(Embeddings):
    """Mock embeddings for development without API keys."""

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        import random
        return [[random.random() for _ in range(1536)] for _ in texts]

    def embed_query(self, text: str) -> list[float]:
        import random
        return [random.random() for _ in range(1536)]

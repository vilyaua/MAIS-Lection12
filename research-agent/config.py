"""Settings for all agents. System prompts loaded from Langfuse."""

from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import BaseSettings

APP_VERSION = (Path(__file__).parent / "VERSION").read_text().strip()


class Settings(BaseSettings):
    """App configuration loaded from .env (via pydantic-settings)."""

    app_name: str = "Multi-Agent Research System L12 (A2A + Langfuse)"
    openai_api_key: SecretStr
    model_powerful: str = "openai:gpt-4.1"
    model_fast: str = "openai:gpt-4.1-mini"

    # Service hosts (localhost for local dev, service names for Docker)
    a2a_host: str = "localhost"
    a2a_port: int = 8904

    # Langfuse
    langfuse_secret_key: SecretStr | None = None
    langfuse_public_key: str | None = None
    langfuse_base_url: str = "https://us.cloud.langfuse.com"

    # Web search
    max_search_results: int = 5
    max_search_content_length: int = 3000
    max_url_content_length: int = 8000

    # RAG
    embedding_model: str = "text-embedding-3-small"
    data_dir: str = "data"
    index_dir: str = "index"
    chunk_size: int = 500
    chunk_overlap: int = 100
    retrieval_top_k: int = 10
    rerank_top_n: int = 3

    # Agent
    output_dir: str = "output"
    max_revision_rounds: int = 2

    model_config = {"env_file": ".env"}

    @property
    def a2a_url(self) -> str:
        return f"http://{self.a2a_host}:{self.a2a_port}"

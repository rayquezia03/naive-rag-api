from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    ollama_base_url: str = "http://localhost:11434"
    chat_model: str = "llama3.2:3b"
    embedding_model: str = "nomic-embed-text"
    chroma_persist_dir: str = "./vector_store"
    chunk_size: int = 500
    chunk_overlap: int = 50
    retriever_k: int = 8
    retriever_k_fetch: int = 13


settings = Settings()

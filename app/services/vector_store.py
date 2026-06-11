from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma

from app.core.config import settings

_store: Chroma | None = None


def get_store() -> Chroma:
    global _store
    if _store is None:
        emb = OllamaEmbeddings(
            model=settings.embedding_model,
            base_url=settings.ollama_base_url,
        )
        _store = Chroma(
            persist_directory=settings.chroma_persist_dir,
            embedding_function=emb,
            collection_name="documents",
        )
    return _store

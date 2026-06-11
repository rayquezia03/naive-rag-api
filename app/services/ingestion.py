import tempfile
import os
import hashlib

from langchain_community.document_loaders import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

from app.core.config import settings
from app.services.vector_store import get_store

# heading boundaries first so chunks stay within a single section
HEADING_SPLITS = ["\n## ", "\n### ", "\n#### ", "\n\n", "\n", " ", ""]


def make_chunk_id(filename: str, idx: int, text: str) -> str:
    return hashlib.sha256(f"{filename}::{idx}::{text}".encode()).hexdigest()


def ingest_markdown(content: bytes, filename: str) -> dict:
    with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as f:
        f.write(content)
        tmp = f.name

    try:
        docs = TextLoader(tmp, encoding="utf-8").load()

        for d in docs:
            d.metadata["source"] = filename

        splitter = RecursiveCharacterTextSplitter(
            separators=HEADING_SPLITS,
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
        )
        chunks = splitter.split_documents(docs)

        if not chunks:
            return {"chunks_stored": 0, "message": "empty document or no content found"}

        ids = [make_chunk_id(filename, i, c.page_content) for i, c in enumerate(chunks)]
        get_store().add_documents(chunks, ids=ids)

        return {"chunks_stored": len(chunks), "filename": filename}
    finally:
        os.unlink(tmp)

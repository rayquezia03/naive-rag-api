from langchain_ollama import OllamaLLM
from langchain_core.prompts import PromptTemplate
from langchain_community.document_compressors import FlashrankRerank

from app.core.config import settings
from app.services.vector_store import get_store

PROMPT = PromptTemplate(
    input_variables=["context", "question"],
    template="""Answer using only the context below. Do not make anything up.
If the answer is spread across multiple excerpts, combine them before responding.
If the information is not in the context, say you could not find it.

Context:
{context}

Question: {question}

Complete answer (include every item found):""",
)

_llm: OllamaLLM | None = None
_reranker: FlashrankRerank | None = None


def _get_llm() -> OllamaLLM:
    global _llm
    if _llm is None:
        _llm = OllamaLLM(model=settings.chat_model, base_url=settings.ollama_base_url)
    return _llm


def _get_reranker() -> FlashrankRerank:
    global _reranker
    if _reranker is None:
        _reranker = FlashrankRerank(top_n=settings.retriever_k)
    return _reranker


def answer_question(question: str) -> dict:
    store = get_store()
    candidates = store.similarity_search(question, k=settings.retriever_k_fetch)

    if not candidates:
        return {
            "answer": "No relevant information found in the indexed documents.",
            "sources": [],
        }

    reranked = _get_reranker().compress_documents(candidates, question)

    context = "\n\n".join(
        f"[Trecho {i + 1}]\n{doc.page_content}"
        for i, doc in enumerate(reranked)
    )

    sources = [
        {
            "chunk": doc.page_content,
            "score": round(float(doc.metadata.get("relevance_score", 0)), 4),
            "source": doc.metadata.get("source", ""),
        }
        for doc in reranked
    ]

    answer = _get_llm().invoke(PROMPT.format(context=context, question=question))

    return {"answer": answer, "sources": sources}

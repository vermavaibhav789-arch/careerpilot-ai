"""
RAG knowledge base: a curated bank of interview questions + ideal answers per
skill, embedded and stored in Chroma so we can retrieve relevant entries to
ground question generation and answer evaluation.

Embeddings use Voyage AI, Anthropic's recommended embeddings partner (see
https://docs.claude.com/en/docs/build-with-claude/embeddings) — Anthropic
doesn't serve its own embedding model. This needs a VOYAGE_API_KEY (Voyage
offers a free tier that's more than enough for this project). If you'd
rather avoid a second API key, swap in
chromadb.utils.embedding_functions.SentenceTransformerEmbeddingFunction()
for a fully local/offline alternative — same retrieval code either way,
just a different embedding_function passed to get_or_create_collection.
"""

import chromadb
from chromadb.utils import embedding_functions

from app.config import get_settings

settings = get_settings()

_embedding_fn = embedding_functions.VoyageAIEmbeddingFunction(
    api_key=settings.voyage_api_key,
    model_name=settings.voyage_model,
)

_client = chromadb.PersistentClient(path=settings.chroma_persist_dir)
_collection = _client.get_or_create_collection(
    name=settings.chroma_collection_name,
    embedding_function=_embedding_fn,
)


def add_entries(ids: list[str], documents: list[str], metadatas: list[dict]) -> None:
    """Add (or upsert) knowledge base entries. Called by seed_vector_db.py."""
    _collection.upsert(ids=ids, documents=documents, metadatas=metadatas)


def query(query_text: str, n_results: int = 2, skill_filter: str | None = None) -> list[dict]:
    """
    Retrieve the most relevant knowledge base entries for a query string.
    Returns a list of {skill, question, ideal_answer, key_concepts} dicts.
    """
    where = {"skill": skill_filter} if skill_filter else None
    results = _collection.query(
        query_texts=[query_text],
        n_results=n_results,
        where=where,
    )
    metadatas = results.get("metadatas", [[]])[0]
    return [
        {
            "skill": m.get("skill", ""),
            "question": m.get("question", ""),
            "ideal_answer": m.get("ideal_answer", ""),
            "key_concepts": m.get("key_concepts", ""),
        }
        for m in metadatas
    ]


def count() -> int:
    return _collection.count()

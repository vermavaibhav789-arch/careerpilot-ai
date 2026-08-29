"""
Populate the Chroma vector store from app/data/interview_bank.json.

Run this once before starting the server (and again any time you edit the
interview bank):

    python seed_vector_db.py
"""

import json
from pathlib import Path

from app.services import vector_store

BANK_PATH = Path(__file__).parent / "app" / "data" / "interview_bank.json"


def main() -> None:
    entries = json.loads(BANK_PATH.read_text())

    ids = [f"bank_{i}" for i in range(len(entries))]
    # Embed skill + question + key_concepts together so semantic search
    # matches on topic, not just exact wording of the question.
    documents = [
        f"{e['skill']}: {e['question']} Key concepts: {e['key_concepts']}"
        for e in entries
    ]
    metadatas = [
        {
            "skill": e["skill"],
            "question": e["question"],
            "ideal_answer": e["ideal_answer"],
            "key_concepts": e["key_concepts"],
        }
        for e in entries
    ]

    vector_store.add_entries(ids=ids, documents=documents, metadatas=metadatas)
    print(f"Seeded {len(entries)} entries into the vector store.")
    print(f"Collection now has {vector_store.count()} total entries.")


if __name__ == "__main__":
    main()

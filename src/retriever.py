

import json
import sqlite3
import math

from src.embedding import create_embeddings



DATABASE_NAME = "localDB.db"
TOP_K = 3


def cosine_similarity(vector1, vector2):
    """
    Returns the cosine similarity between two embedding vectors.
    """

    dot_product = sum(a * b for a, b in zip(vector1, vector2))   

    magnitude1 = math.sqrt(sum(a * a for a in vector1))
    magnitude2 = math.sqrt(sum(b * b for b in vector2))

    return dot_product / (magnitude1 * magnitude2)



CACHED_DOCUMENTS = []


def load_documents():
    connection = sqlite3.connect(DATABASE_NAME)
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT id, document_name, page_number, chunk_index, chunk, embedding
        FROM documents
        ORDER BY document_name, chunk_index
        """
    )

    rows = cursor.fetchall()
    connection.close()

    documents = []

    for document_id, document_name, page_number, chunk_index, chunk, embedding_json in rows:
        try:
            embedding = json.loads(embedding_json)
        except (TypeError, json.JSONDecodeError):
            continue

        documents.append({
            "id": document_id,
            "document_name": document_name,
            "page_number": page_number,
            "chunk_index": chunk_index,
            "chunk": chunk,
            "embedding": embedding
        })

    return documents


def refresh_cache_from_database():
    global CACHED_DOCUMENTS

    CACHED_DOCUMENTS = load_documents()

    print(f"Loaded {len(CACHED_DOCUMENTS)} chunks from SQLite.")

    return CACHED_DOCUMENTS


def set_cached_documents(chunks, embeddings, document_name=""):
    # Database is already updated before this is called; just reload.
    refresh_cache_from_database()


def clear_cached_documents():
    global CACHED_DOCUMENTS
    CACHED_DOCUMENTS = []


def get_documents():
    if CACHED_DOCUMENTS:
        return CACHED_DOCUMENTS

    return refresh_cache_from_database()


def retrieve_best_chunk(question):
    """
    Returns: (context, context_embeddings, best_score, selected_sources)
    """

    question_embedding = create_embeddings([question])[0]

    documents = get_documents()

    if not documents:
        return None, [], 0.0, []

    scored = [
        (cosine_similarity(question_embedding, doc["embedding"]), doc)
        for doc in documents
    ]

    scored.sort(key=lambda item: item[0], reverse=True)

    best_score = scored[0][0]

    RELEVANCE_MARGIN = 0.08

    top_results = [
        item for item in scored[:TOP_K]
        if item[0] >= best_score - RELEVANCE_MARGIN
    ]

    print("\nTop Retrieved Chunks:")
    for rank, (score, doc) in enumerate(top_results, start=1):
        print(f"\n{rank}. Score: {score:.4f} | {doc['document_name']} | Page {doc['page_number']}")
        print(doc["chunk"][:300])

    context = "\n\n".join(doc["chunk"] for _, doc in top_results)
    context_embeddings = [doc["embedding"] for _, doc in top_results]

    selected_sources = [
        {"document_name": doc["document_name"], "page_number": doc["page_number"]}
        for _, doc in top_results
    ]

    return context, context_embeddings, top_results[0][0], selected_sources

    
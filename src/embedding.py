
"""
Creates vector embeddings for text chunks using Foundry Local.
"""

from src.foundry import manager

EMBEDDING_MODEL_ALIAS = "qwen3-embedding-0.6b"

print("Loading embedding model...")

embedding_model = manager.catalog.get_model(EMBEDDING_MODEL_ALIAS)
embedding_model.download()
embedding_model.load()

embedding_client = embedding_model.get_embedding_client()

print("Embedding model ready!")


def create_embeddings(chunks):
    """
    Generates a vector embedding for each text chunk.
    """

    if not chunks:
        return []

    response = embedding_client.generate_embeddings(chunks)

    return [item.embedding for item in response.data]


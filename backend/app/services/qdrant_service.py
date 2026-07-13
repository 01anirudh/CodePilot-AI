from typing import Optional
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import (
    Distance, VectorParams, PointStruct,
    Filter, FieldCondition, MatchValue,
)
import uuid
from app.config import settings


_client: Optional[AsyncQdrantClient] = None


def get_qdrant_client() -> AsyncQdrantClient:
    global _client
    if _client is None:
        _client = AsyncQdrantClient(
            url=settings.QDRANT_URL,
            api_key=settings.QDRANT_API_KEY,
        )
    return _client


async def ensure_collection():
    """Create Qdrant collection if it doesn't exist."""
    client = get_qdrant_client()
    collections = await client.get_collections()
    names = [c.name for c in collections.collections]
    if settings.QDRANT_COLLECTION_NAME not in names:
        await client.create_collection(
            collection_name=settings.QDRANT_COLLECTION_NAME,
            vectors_config=VectorParams(
                size=settings.EMBEDDING_DIMENSION,
                distance=Distance.COSINE,
            ),
        )


async def upsert_embeddings(
    embeddings: list[list[float]],
    payloads: list[dict],
) -> int:
    """Upsert embeddings into Qdrant."""
    client = get_qdrant_client()
    points = [
        PointStruct(
            id=str(uuid.uuid4()),
            vector=embedding,
            payload=payload,
        )
        for embedding, payload in zip(embeddings, payloads)
    ]
    await client.upsert(
        collection_name=settings.QDRANT_COLLECTION_NAME,
        points=points,
    )
    return len(points)


async def search_similar(
    query_vector: list[float],
    repository_id: Optional[str] = None,
    limit: int = 10,
) -> list[dict]:
    """Search for similar code snippets."""
    client = get_qdrant_client()
    query_filter = None
    if repository_id:
        query_filter = Filter(
            must=[
                FieldCondition(
                    key="repository_id",
                    match=MatchValue(value=repository_id),
                )
            ]
        )
    results = await client.search(
        collection_name=settings.QDRANT_COLLECTION_NAME,
        query_vector=query_vector,
        query_filter=query_filter,
        limit=limit,
    )
    return [
        {
            "id": str(r.id),
            "score": r.score,
            "payload": r.payload,
        }
        for r in results
    ]

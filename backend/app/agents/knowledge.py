"""
Knowledge Agent — chunks code files, generates embeddings, and stores them in Qdrant.
Also handles semantic search over the codebase.
"""
import re
from typing import Any
from app.services.llm_service import get_embeddings
from app.services import qdrant_service


CODE_EXTENSIONS = {
    ".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".go", ".rs", ".cpp",
    ".c", ".h", ".cs", ".rb", ".php", ".swift", ".kt", ".scala",
    ".yaml", ".yml", ".json", ".toml", ".md",
}

MAX_CHUNK_SIZE = 1000  # tokens approx
CHUNK_OVERLAP = 100


def chunk_code(content: str, chunk_size: int = MAX_CHUNK_SIZE) -> list[str]:
    """Split code into overlapping chunks by lines."""
    lines = content.split("\n")
    chunks = []
    i = 0
    while i < len(lines):
        chunk = "\n".join(lines[i : i + chunk_size])
        if chunk.strip():
            chunks.append(chunk)
        i += chunk_size - CHUNK_OVERLAP
    return chunks


def is_code_file(path: str) -> bool:
    return any(path.endswith(ext) for ext in CODE_EXTENSIONS)


async def run_knowledge_agent(
    repository_id: str,
    files: list[dict[str, str]],  # [{"path": ..., "content": ...}]
    on_progress: Any = None,
) -> dict[str, Any]:
    """
    Generate embeddings for repository files and store in Qdrant.

    Args:
        repository_id: UUID of the repository
        files: List of {path, content} dicts
        on_progress: Optional callback(current, total)

    Returns:
        Summary dict with embedding counts
    """
    await qdrant_service.ensure_collection()
    embedder = get_embeddings()

    total_chunks = 0
    total_files = 0
    batch_embeddings = []
    batch_payloads = []
    batch_size = 20

    code_files = [f for f in files if is_code_file(f["path"])]
    total = len(code_files)

    for idx, file_data in enumerate(code_files):
        path = file_data["path"]
        content = file_data.get("content", "")
        if not content.strip():
            continue

        chunks = chunk_code(content)
        for chunk_idx, chunk in enumerate(chunks):
            batch_embeddings.append(chunk)
            batch_payloads.append({
                "repository_id": repository_id,
                "file_path": path,
                "chunk_index": chunk_idx,
                "content": chunk[:500],  # Store preview
                "file_extension": path.rsplit(".", 1)[-1] if "." in path else "",
            })

        total_files += 1
        if on_progress:
            on_progress(idx + 1, total)

        # Flush batch
        if len(batch_embeddings) >= batch_size:
            vectors = embedder.embed_documents(batch_embeddings)
            await qdrant_service.upsert_embeddings(vectors, batch_payloads)
            total_chunks += len(batch_embeddings)
            batch_embeddings = []
            batch_payloads = []

    # Flush remainder
    if batch_embeddings:
        vectors = embedder.embed_documents(batch_embeddings)
        await qdrant_service.upsert_embeddings(vectors, batch_payloads)
        total_chunks += len(batch_embeddings)

    return {
        "files_processed": total_files,
        "chunks_embedded": total_chunks,
        "repository_id": repository_id,
    }


async def semantic_search(query: str, repository_id: str, limit: int = 5) -> list[dict]:
    """Search the knowledge base for relevant code."""
    embedder = get_embeddings()
    query_vector = embedder.embed_query(query)
    results = await qdrant_service.search_similar(query_vector, repository_id, limit)
    return results

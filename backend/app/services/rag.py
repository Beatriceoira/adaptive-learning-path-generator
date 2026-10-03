"""
RAG knowledge base: chunk source text, embed it, store it per topic in
`knowledge_chunks` (pgvector), and retrieve the most relevant chunks for a
given topic + query. Used by roadmap generation (rationale grounding) and
study material generation (content grounding).
"""

from sqlalchemy.orm import Session

from app.models import KnowledgeChunk, Topic
from app.services.llm import get_embedding, get_embeddings

CHUNK_SIZE = 800  # characters, not tokens -- simple and dependency-free
CHUNK_OVERLAP = 100
DEFAULT_TOP_K = 5


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """
    Simple sliding-window character chunker. Good enough for phase 4; swap
    for a token-aware / semantic chunker later without touching callers.
    """
    text = text.strip()
    if len(text) <= chunk_size:
        return [text] if text else []

    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start = end - overlap  # step forward, keeping `overlap` chars of context
    return chunks


def ingest_topic_content(db: Session, topic_id: str, raw_text: str, source: str | None = None) -> int:
    """
    Chunks raw_text, embeds every chunk in one batched call, and stores them
    against topic_id. Returns the number of chunks created. Does not commit
    -- caller controls the transaction.
    """
    topic = db.query(Topic).filter(Topic.id == topic_id).first()
    if topic is None:
        raise ValueError(f"Topic {topic_id} does not exist")

    pieces = chunk_text(raw_text)
    if not pieces:
        return 0

    embeddings = get_embeddings(pieces)

    for content, embedding in zip(pieces, embeddings):
        db.add(
            KnowledgeChunk(
                topic_id=topic_id,
                content=content,
                embedding=embedding,
                source=source,
            )
        )
    return len(pieces)


def retrieve_relevant_chunks(
    db: Session, topic_id: str, query: str, k: int = DEFAULT_TOP_K
) -> list[KnowledgeChunk]:
    """
    Returns up to k chunks for topic_id, nearest to query by cosine distance.
    Empty list means no knowledge has been ingested for this topic yet --
    callers should handle that (e.g. fall back to the LLM's general
    knowledge, clearly labeled as ungrounded).
    """
    query_embedding = get_embedding(query)
    return (
        db.query(KnowledgeChunk)
        .filter(KnowledgeChunk.topic_id == topic_id)
        .order_by(KnowledgeChunk.embedding.cosine_distance(query_embedding))
        .limit(k)
        .all()
    )

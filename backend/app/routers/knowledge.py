from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.database import get_db
from app.models import User
from app.schemas.knowledge import KnowledgeIngestRequest, KnowledgeIngestResponse
from app.services.rag import ingest_topic_content

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])


@router.post("/ingest", response_model=KnowledgeIngestResponse, status_code=201)
def ingest_content(
    payload: KnowledgeIngestRequest,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    """
    Adds source material to the RAG knowledge base for a topic (e.g. a
    textbook section, docs page, or course notes). Chunks + embeds it so
    later study-material and roadmap-rationale generation can retrieve and
    ground on it. Requires OPENAI_API_KEY to be set (embedding call).
    """
    try:
        chunks_created = ingest_topic_content(db, payload.topic_id, payload.content, payload.source)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Embedding call failed: {e}")

    db.commit()
    return KnowledgeIngestResponse(topic_id=payload.topic_id, chunks_created=chunks_created)

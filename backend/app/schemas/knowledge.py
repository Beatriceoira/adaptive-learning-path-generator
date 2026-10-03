from pydantic import BaseModel


class KnowledgeIngestRequest(BaseModel):
    topic_id: str
    content: str
    source: str | None = None


class KnowledgeIngestResponse(BaseModel):
    topic_id: str
    chunks_created: int

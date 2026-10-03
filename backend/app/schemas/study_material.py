from datetime import datetime

from pydantic import BaseModel


class StudyMaterialGenerateRequest(BaseModel):
    topic_id: str
    difficulty_level: int = 1
    force_regenerate: bool = False


class StudyMaterialOut(BaseModel):
    id: str
    topic_id: str
    difficulty_level: int
    content_markdown: str
    generated_at: datetime

    model_config = {"from_attributes": True}

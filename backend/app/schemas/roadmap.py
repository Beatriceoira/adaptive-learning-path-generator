from datetime import datetime

from pydantic import BaseModel


class RoadmapGenerateRequest(BaseModel):
    subject_id: str


class RoadmapStepOut(BaseModel):
    topic_id: str
    topic_name: str
    sequence_order: int
    status: str

    model_config = {"from_attributes": True}


class RoadmapOut(BaseModel):
    id: str
    subject_id: str
    created_at: datetime
    is_active: bool
    rationale: str | None = None
    steps: list[RoadmapStepOut]

    model_config = {"from_attributes": True}

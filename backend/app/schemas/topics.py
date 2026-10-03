from pydantic import BaseModel


class SubjectCreate(BaseModel):
    name: str
    description: str | None = None


class SubjectOut(BaseModel):
    id: str
    name: str
    description: str | None = None

    model_config = {"from_attributes": True}


class TopicCreate(BaseModel):
    subject_id: str
    name: str
    description: str | None = None
    difficulty_level: int = 1
    prerequisite_ids: list[str] = []


class TopicOut(BaseModel):
    id: str
    subject_id: str
    name: str
    description: str | None = None
    difficulty_level: int

    model_config = {"from_attributes": True}

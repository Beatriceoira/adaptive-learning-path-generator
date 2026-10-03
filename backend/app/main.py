from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import ensure_pgvector_extension
from app.routers import (
    assessments,
    auth,
    knowledge,
    progress,
    quiz,
    recommendations,
    roadmap,
    study_material,
    topics,
    users,
)

app = FastAPI(title="Personalized Learning Path Generator API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(topics.router)
app.include_router(assessments.router)
app.include_router(knowledge.router)
app.include_router(roadmap.router)
app.include_router(study_material.router)
app.include_router(quiz.router)
app.include_router(recommendations.router)
app.include_router(progress.router)


@app.on_event("startup")
def on_startup():
    # The knowledge_chunks table's embedding column needs the pgvector
    # extension present before Base.metadata.create_all() (or an alembic
    # migration) runs against a fresh database.
    ensure_pgvector_extension()


@app.get("/api/health")
def health_check():
    return {"status": "ok"}

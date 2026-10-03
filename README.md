# Personalized Learning Path Generator

An AI-powered adaptive learning platform that assesses a learner's current knowledge, generates a personalized learning roadmap, delivers RAG-grounded study material, and continuously adapts quiz difficulty based on performance.

The system combines **Bayesian Knowledge Tracing (BKT)**, **Retrieval-Augmented Generation (RAG)**, **LLMs**, and **PostgreSQL + pgvector** to create an adaptive learning experience rather than a static course sequence.

## Features

*  **JWT Authentication** — secure signup, login, and protected API routes
*  **Diagnostic Skill Assessment** — establishes baseline topic mastery
*  **Bayesian Knowledge Tracing** — continuously estimates mastery probability
*  **Personalized Learning Roadmaps** — prerequisite-aware topic ordering
* **RAG-Grounded Study Material** — generates topic-specific content from an indexed knowledge base
*  **Adaptive Quizzes** — automatically adjusts difficulty based on mastery
*  **AI-Generated Questions** — generates additional questions when the question bank is exhausted
*  **Weak-Topic Detection** — identifies topics where the learner needs additional practice
*  **Personalized Recommendations** — recommends what to study next
*  **Progress Dashboard** — tracks mastery, accuracy, weak topics, and activity history
*  **Semantic Retrieval** — pgvector-powered cosine similarity search
*  **Study Material Caching** — avoids unnecessary LLM calls for previously generated material
*  **OpenAI-Compatible LLM Providers** — configurable LLM endpoint through `LLM_BASE_URL`
*  **Next.js Frontend** — responsive learner-facing interface

## Architecture

```text
┌──────────────────────────────────────────────────────────────┐
│                       Next.js Frontend                       │
│                                                              │
│  Auth → Subjects → Assessment → Roadmap → Study → Quiz      │
│                         ↓                                    │
│                    Progress Dashboard                        │
└──────────────────────────┬───────────────────────────────────┘
                           │ REST API
                           ▼
┌──────────────────────────────────────────────────────────────┐
│                       FastAPI Backend                        │
│                                                              │
│  Auth │ Assessments │ Roadmaps │ Study Material │ Quizzes   │
│       │             │          │                │           │
│       └─────────────┴──────────┴────────────────┘           │
│                           │                                  │
│                     Service Layer                           │
│                           │                                  │
│       ┌───────────────────┼────────────────────┐             │
│       ▼                   ▼                    ▼             │
│      BKT                 RAG                  LLM            │
│  Mastery Tracking    Retrieval          Generation          │
└───────────┬───────────────┬────────────────────┬─────────────┘
            │               │                    │
            ▼               ▼                    ▼
       PostgreSQL        pgvector         LLM / Embeddings
```

### Technology Stack

| Layer              | Technology                                  |
| ------------------ | ------------------------------------------- |
| Frontend           | Next.js 14, React, TypeScript, Tailwind CSS |
| Backend            | Python, FastAPI                             |
| Database           | PostgreSQL                                  |
| Vector Search      | pgvector                                    |
| ORM                | SQLAlchemy                                  |
| Migrations         | Alembic                                     |
| Authentication     | JWT + OAuth2 Password Flow                  |
| AI                 | OpenAI-compatible LLM API                   |
| Retrieval          | RAG + cosine similarity                     |
| Knowledge Model    | Bayesian Knowledge Tracing                  |
| Validation         | Pydantic                                    |
| Package Management | npm / pip                                   |

#  Getting Started

## Prerequisites

Install the following:

* Python **3.13**
* Node.js **18+**
* npm
* Docker
* Docker Compose
* PostgreSQL with the **pgvector** extension

Using Docker for PostgreSQL is recommended for local development.

---

## 1. Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/adaptive-learning-path-generator.git
cd adaptive-learning-path-generator
```

## 2. Start PostgreSQL + pgvector

The project can use the official pgvector PostgreSQL image.

```yaml
services:
  postgres:
    image: pgvector/pgvector:pg16
    container_name: learning-path-postgres
    restart: unless-stopped
    environment:
      POSTGRES_USER: learnpath
      POSTGRES_PASSWORD: learnpath
      POSTGRES_DB: learnpath
    ports:
      - "5432:5432"
    volumes:
      - learning_path_postgres_data:/var/lib/postgresql/data

volumes:
  learning_path_postgres_data:
```

Start the database:

```bash
docker compose up -d
```

Verify that it is running:

```bash
docker ps
```

Enable pgvector:

```bash
docker exec -it learning-path-postgres \
  psql -U learnpath -d learnpath
```

Then:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

Verify:

```sql
\dx
```

Exit:

```sql
\q
```

#  Backend Setup

Open a terminal:

```bash
cd backend
```

Create the virtual environment:

```bash
python3.13 -m venv venv
```

Activate it:

```bash
source venv/bin/activate
```

Verify Python:

```bash
python --version
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Verify dependencies:

```bash
pip check
```

## Backend Environment Variables

Copy the example environment file:

```bash
cp .env.example .env
```

Configure:

```env
DATABASE_URL=postgresql://learnpath:learnpath@localhost:5432/learnpath

SECRET_KEY=your-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=60

OPENAI_API_KEY=your-api-key

LLM_MODEL=gpt-4o-mini
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_DIM=1536
```

### Optional OpenAI-Compatible Endpoint

The LLM service supports OpenAI-compatible providers through:

```env
LLM_BASE_URL=https://your-provider.example/v1
```

This allows the underlying LLM provider to be changed without modifying the service callers.

> Never commit `.env` or API keys to Git.

## Seed the Database

From the `backend/` directory:

```bash
python -m scripts.seed
```

The seed script creates a sample:

```text
Python Programming
├── Python Basics
├── Control Flow
├── Functions
├── Data Structures
└── Object-Oriented Programming
```

along with sample quiz questions and prerequisite relationships.

## Start the API

From `backend/`:

```bash
uvicorn app.main:app --reload
```

The API will be available at:

```text
http://localhost:8000
```

Interactive API documentation:

```text
http://localhost:8000/docs
```

Alternative OpenAPI documentation:

```text
http://localhost:8000/redoc
```

Health/connectivity can be checked through:

```bash
curl http://localhost:8000/openapi.json
```

# Frontend Setup

Open a second terminal:

```bash
cd frontend
```

Install dependencies:

```bash
npm install
```

Create the environment file:

```bash
cp .env.local.example .env.local
```

Configure:

```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

Start the development server:

```bash
npm run dev
```

The frontend will be available at:

```text
http://localhost:3000
```

# Learning Pipeline

The learner experience follows this general flow:

```text
Sign Up
   │
   ▼
Select Subject
   │
   ▼
Diagnostic Assessment
   │
   ▼
Initial Mastery Estimation
   │
   ▼
Generate Personalized Roadmap
   │
   ▼
Study Topic
   │
   ▼
Adaptive Quiz
   │
   ▼
Update Mastery
   │
   ├───────────────┐
   ▼               ▼
Weak Topic?     Mastered?
   │               │
   ▼               ▼
Practice More   Advance
   │               │
   └───────┬───────┘
           ▼
   Updated Recommendations
           │
           ▼
      Repeat Learning Loop
```

The key design principle is that **learner performance continuously influences what happens next**.

---

# Adaptive Learning Engine

## Bayesian Knowledge Tracing

Each `(user, topic)` pair maintains a mastery probability between `0` and `1`.

```text
0.0 ─────────────────────────────── 1.0
      Low mastery       High mastery
```

The system updates mastery after each answer using:

```python
bkt_update(
    prior,
    is_correct,
    slip,
    guess,
    p_learn
)
```

Diagnostic assessments use:

```text
p_learn = 0
```

Practice questions use:

```text
p_learn = 0.15
```

This allows diagnostic assessments to primarily measure knowledge while practice can increase the learner's estimated mastery.

# Adaptive Quiz Difficulty

Quiz difficulty is derived directly from the current mastery probability:

|  Mastery | Difficulty |
| -------: | ---------: |
| `< 0.30` |          1 |
| `< 0.50` |          2 |
| `< 0.70` |          3 |
| `< 0.85` |          4 |
| `≥ 0.85` |          5 |

The difficulty is recalculated whenever the learner requests another question.

```text
Answer Question
      │
      ▼
Update Mastery
      │
      ▼
Calculate Difficulty
      │
      ▼
Find Unseen Question
      │
      ├── Available → Return Question
      │
      └── Exhausted
             │
             ▼
       Generate AI Questions
             │
             ├── Success → Store + Return
             │
             └── Failure → Reuse Existing Question
```

This creates a continuous adaptive loop without requiring a separate "adjust difficulty" operation.

# Personalized Roadmaps

Roadmaps are generated from the subject's prerequisite graph.

Topics are ordered using **Kahn's topological sorting algorithm**.

For example:

```text
Python Basics
      │
      ▼
Control Flow
      │
      ▼
Functions
      │
      ▼
Data Structures
      │
      ▼
Object-Oriented Programming
```

A topic cannot be placed before its prerequisites.

Topics with:

```text
mastery_probability >= 0.70
```

are automatically marked as completed when a roadmap is generated.

Only one active roadmap exists per:

```text
(user, subject)
```

Generating a new roadmap deactivates the previous one.

# RAG Pipeline

The system uses Retrieval-Augmented Generation to ground AI-generated content in topic-specific source material.

```text
Source Material
      │
      ▼
Text Chunking
      │
      ▼
Embeddings
      │
      ▼
PostgreSQL + pgvector
      │
      ▼
Cosine Similarity Search
      │
      ▼
Relevant Chunks
      │
      ▼
LLM Prompt
      │
      ▼
Generated Content
```

## Chunking

The current chunker uses:

```text
Chunk size: 800 characters
Overlap:    100 characters
```

The implementation is dependency-free and can later be replaced with a token-aware splitter.

## Retrieval

Relevant chunks are retrieved using pgvector cosine distance and scoped to the requested topic.

Study material retrieval uses up to **6 relevant chunks**.

# AI-Generated Study Material

Study material is generated according to the learner's requested difficulty.

Generated content is cached by:

```text
(topic_id, difficulty_level)
```

A repeated request returns the cached material unless:

```text
force_regenerate = true
```

The system also records the RAG chunks used to ground the generated material.

# Diagnostic Assessment

The initial assessment selects questions from **entry topics** — topics with no prerequisites.

The current selection strategy supports up to:

```text
5 topics × 3 questions
```

Answers are graded using exact, case-insensitive matching.

Code questions are currently not automatically executed or evaluated. They are intentionally left for a future sandboxed execution or LLM-rubric grading implementation.

# Weak Topic Detection

A topic becomes weak when:

```text
attempts_count >= 5
AND
mastery_probability < 0.50
```

The flag is recalculated whenever mastery changes.

Therefore, weak-topic status is **not sticky**.

If mastery later rises above the threshold, the topic automatically stops being classified as weak.

# Recommendations

The recommendation engine combines:

1. Currently weak topics
2. Recommended difficulty for those topics
3. Upcoming `not_started` roadmap steps

The LLM can generate a short personalized recommendation based only on those signals.

If AI generation fails, the API falls back to a deterministic message rather than failing the entire recommendation request.

# Progress Dashboard

The dashboard exposes:

* Per-topic mastery
* Number of mastered topics
* Overall accuracy
* Weak-topic count
* Roadmap completion percentage
* Daily quiz activity
* Daily accuracy

Activity history is zero-filled so the chart contains every day in the requested time window.

The frontend uses a lightweight inline SVG chart rather than introducing a charting dependency.

# Authentication

Authentication uses:

```text
OAuth2 Password Flow
        │
        ▼
JWT Access Token
        │
        ▼
Bearer Authentication
```

The frontend stores the JWT in `localStorage`.

Protected API requests include:

```http
Authorization: Bearer <token>
```

The frontend also handles `401 Unauthorized` responses globally by clearing the local session and redirecting the user to login.

The default access-token lifetime is:

```text
60 minutes
```

# API Reference

## Authentication

| Method | Endpoint           | Description                  |
| ------ | ------------------ | ---------------------------- |
| POST   | `/api/auth/signup` | Create account               |
| POST   | `/api/auth/login`  | Authenticate and receive JWT |
| GET    | `/api/users/me`    | Get current user             |

## Subjects & Topics

| Method | Endpoint                    | Description         |
| ------ | --------------------------- | ------------------- |
| POST   | `/api/subjects`             | Create subject      |
| GET    | `/api/subjects`             | List subjects       |
| POST   | `/api/topics`               | Create topic        |
| GET    | `/api/subjects/{id}/topics` | List subject topics |
| GET    | `/api/topics/{id}`          | Get topic           |

## Assessment

| Method | Endpoint                       | Description       |
| ------ | ------------------------------ | ----------------- |
| POST   | `/api/assessments/start`       | Start diagnostic  |
| POST   | `/api/assessments/{id}/submit` | Submit assessment |
| GET    | `/api/assessments/{id}`        | Get assessment    |

## Knowledge / RAG

| Method | Endpoint                | Description                |
| ------ | ----------------------- | -------------------------- |
| POST   | `/api/knowledge/ingest` | Ingest and embed knowledge |

## Roadmap

| Method | Endpoint                           | Description        |
| ------ | ---------------------------------- | ------------------ |
| POST   | `/api/roadmap/generate`            | Generate roadmap   |
| GET    | `/api/roadmap/active/{subject_id}` | Get active roadmap |

## Study Material

| Method | Endpoint                         | Description                   |
| ------ | -------------------------------- | ----------------------------- |
| POST   | `/api/study-material/generate`   | Generate or retrieve material |
| GET    | `/api/study-material/{topic_id}` | Retrieve cached material      |

## Adaptive Quiz

| Method | Endpoint           | Description                      |
| ------ | ------------------ | -------------------------------- |
| POST   | `/api/quiz/next`   | Get next adaptive question       |
| POST   | `/api/quiz/submit` | Submit answer and update mastery |

## Recommendations

| Method | Endpoint                            | Description                      |
| ------ | ----------------------------------- | -------------------------------- |
| GET    | `/api/recommendations/{subject_id}` | Get personalized recommendations |

## Progress

| Method | Endpoint                             | Description           |
| ------ | ------------------------------------ | --------------------- |
| GET    | `/api/progress/{subject_id}`         | Get progress overview |
| GET    | `/api/progress/{subject_id}/history` | Get activity history  |

Interactive documentation is available at:

```text
http://localhost:8000/docs
```

# Project Structure

```text
adaptive-learning-path-generator/
│
├── backend/
│   ├── app/
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── security.py
│   │   │   └── dependencies.py
│   │   │
│   │   ├── models/
│   │   │   └── ...
│   │   │
│   │   ├── schemas/
│   │   │   └── ...
│   │   │
│   │   ├── routers/
│   │   │   ├── auth.py
│   │   │   ├── users.py
│   │   │   ├── topics.py
│   │   │   ├── assessments.py
│   │   │   ├── knowledge.py
│   │   │   ├── roadmap.py
│   │   │   ├── study_material.py
│   │   │   ├── quiz.py
│   │   │   ├── recommendations.py
│   │   │   └── progress.py
│   │   │
│   │   ├── services/
│   │   │   ├── mastery.py
│   │   │   ├── grading.py
│   │   │   ├── llm.py
│   │   │   ├── rag.py
│   │   │   ├── roadmap.py
│   │   │   ├── study_material.py
│   │   │   ├── quiz_generation.py
│   │   │   ├── adaptive_quiz.py
│   │   │   ├── recommendations.py
│   │   │   └── progress.py
│   │   │
│   │   ├── database.py
│   │   └── main.py
│   │
│   ├── alembic/
│   ├── scripts/
│   │   └── seed.py
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/
│   ├── app/
│   │   ├── login/
│   │   ├── signup/
│   │   ├── subjects/
│   │   └── topics/
│   │
│   ├── components/
│   │   ├── NavBar.tsx
│   │   ├── ui.tsx
│   │   └── ActivityChart.tsx
│   │
│   ├── lib/
│   │   ├── api.ts
│   │   ├── auth-context.tsx
│   │   ├── types.ts
│   │   └── constants.ts
│   │
│   ├── package.json
│   ├── tsconfig.json
│   ├── tailwind.config.ts
│   ├── next.config.mjs
│   └── .env.local.example
│
├── docker-compose.yml
├── .gitignore
└── README.md
```

# Database Schema

The primary entities are:

```text
users
  │
  └── mastery_scores ── topics
          │                │
          │                └── topic_prerequisites
          │
          ├── quiz_attempts ── quiz_questions
          │
          └── skill_assessments

subjects
  │
  ├── topics
  ├── learning_paths
  │      └── learning_path_steps
  │
  └── knowledge_chunks
         │
         └── pgvector embeddings

topics
  │
  └── study_materials
```

### Core tables

* `users`
* `subjects`
* `topics`
* `topic_prerequisites`
* `skill_assessments`
* `mastery_scores`
* `learning_paths`
* `learning_path_steps`
* `study_materials`
* `quiz_questions`
* `quiz_attempts`
* `knowledge_chunks`

# Testing & Verification

The project has undergone extensive functional verification across the implemented phases.

Verified areas include:

* Authentication flow
* Diagnostic assessment
* BKT mastery calculations
* Roadmap prerequisite ordering
* Cyclic prerequisite fallback
* Adaptive difficulty boundaries
* Adaptive question selection
* AI question validation
* Question exhaustion fallback
* Weak-topic detection
* Recommendation fallback behavior
* Progress aggregation
* Activity history boundaries
* Frontend navigation
* Session expiration handling
* Out-of-order study-material responses
* API contract compatibility

The application was also exercised through real browser automation against a contract-accurate backend simulation.

### Important limitation

The verification described above was development-time verification rather than a committed automated regression suite.

A production-ready continuation should add:

```text
pytest
├── unit tests
├── API tests
└── database integration tests

Playwright
├── authentication flows
├── assessment flow
├── adaptive quiz flow
├── roadmap flow
└── progress dashboard
```

# Roadmap

The core eight-phase implementation is complete.

### Planned improvements

#### Content Management

* Larger subject/topic library
* Instructor content authoring
* PDF/document ingestion
* Source management
* Better chunking and metadata
* Multiple knowledge sources per topic

#### Assessment

* LLM-based code grading
* Sandboxed code execution
* More question types
* Difficulty calibration
* Item-response analysis

#### Adaptive Learning

* More sophisticated mastery models
* Spaced repetition
* Learning velocity
* Forgetting curves
* Personalized review scheduling
* Per-concept confidence intervals

#### AI

* Provider abstraction
* Streaming responses
* Structured LLM outputs
* AI tutoring conversations
* Explain-my-mistake functionality
* Socratic tutoring mode

#### Backend

* Complete Alembic migration history
* Background jobs
* Redis caching
* Rate limiting
* Observability
* Structured logging
* API versioning

#### Frontend

* Richer analytics
* Mobile-responsive improvements
* Accessibility improvements
* Dark mode
* Interactive roadmap visualization
* Study streaks
* Gamification

#### Testing

* Committed pytest suite
* API integration tests
* Playwright E2E tests
* LLM response evaluation
* RAG retrieval evaluation
* Performance/load testing

#### Deployment

* Dockerized backend
* Production PostgreSQL + pgvector
* CI/CD
* HTTPS
* Secrets management
* Monitoring
* Production logging

# Development Notes

### PostgreSQL + pgvector

The application can create the PostgreSQL `vector` extension if it already exists on the server:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

However, the application cannot install the extension at the operating-system level. Use a PostgreSQL installation that already provides pgvector, such as the Docker image used in local development.

### LLM Provider

The application intentionally wraps LLM functionality in:

```text
backend/app/services/llm.py
```

The rest of the application interacts with:

```text
get_embedding()
get_embeddings()
generate_text()
```

This keeps provider-specific implementation isolated and makes future provider changes easier.

### Frontend API Configuration

The frontend uses:

```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

Do not confuse this with arbitrary API environment-variable names; the frontend's API client reads this specific variable.

# Security Considerations

This project is intended for development and portfolio use and should receive additional hardening before production deployment.

Important production considerations include:

* Never commit API keys or secrets
* Use a strong randomly generated JWT secret
* Use HTTPS
* Secure token storage
* Add rate limiting
* Validate and sanitize user-provided content
* Restrict knowledge ingestion permissions
* Protect administrative/content-authoring endpoints
* Add database least-privilege roles
* Configure CORS explicitly
* Add request-size limits
* Add audit logging
* Add production-grade secret management
* Sandbox any future executable-code grading system
* Avoid exposing internal LLM/provider errors to clients


import type {
  AssessmentStartResponse,
  AssessmentSubmitResponse,
  ProgressHistory,
  ProgressOverview,
  QuizNextResponse,
  QuizSubmitResponse,
  Recommendations,
  Roadmap,
  StudyMaterial,
  Subject,
  Topic,
  User,
} from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

// Called when an *authenticated* request comes back 401 (expired or revoked
// token). AuthProvider registers a handler that clears the session so
// useRequireAuth bounces the learner to /login instead of leaving them on a
// page full of "Could not validate credentials" errors. A 401 from the login
// form itself (wrong password) carries no token, so it never triggers this.
let unauthorizedHandler: (() => void) | null = null;

export function setUnauthorizedHandler(handler: (() => void) | null): void {
  unauthorizedHandler = handler;
}

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
    this.name = "ApiError";
  }
}

// FastAPI validation errors come back as {"detail": [{"msg": "...", ...}, ...]};
// HTTPException errors come back as {"detail": "some string"}. Handle both.
function extractErrorMessage(body: unknown, fallback: string): string {
  if (body && typeof body === "object" && "detail" in body) {
    const detail = (body as { detail: unknown }).detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail)) {
      const messages = detail
        .map((item) => (item && typeof item === "object" && "msg" in item ? String((item as { msg: unknown }).msg) : null))
        .filter((m): m is string => Boolean(m));
      if (messages.length) return messages.join("; ");
    }
  }
  return fallback;
}

interface RequestOptions {
  method?: string;
  token?: string | null;
  body?: unknown;
  isForm?: boolean;
}

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { method = "GET", token, body, isForm = false } = options;

  const headers: Record<string, string> = {};
  if (token) headers.Authorization = `Bearer ${token}`;
  if (body !== undefined) headers["Content-Type"] = isForm ? "application/x-www-form-urlencoded" : "application/json";

  let res: Response;
  try {
    res = await fetch(`${API_BASE}${path}`, {
      method,
      headers,
      body: body === undefined ? undefined : isForm ? (body as string) : JSON.stringify(body),
    });
  } catch {
    throw new ApiError(0, "Could not reach the API. Is the backend running?");
  }

  if (!res.ok) {
    let parsed: unknown = null;
    try {
      parsed = await res.json();
    } catch {
      // response body wasn't JSON -- fall through to generic message below
    }
    if (res.status === 401 && token && unauthorizedHandler) unauthorizedHandler();
    throw new ApiError(res.status, extractErrorMessage(parsed, `Request failed (${res.status})`));
  }

  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

// Like `request`, but treats a 404 as a valid "nothing here yet" result
// instead of an error -- used for optional/cached resources (an active
// roadmap that hasn't been generated yet, study material that hasn't been
// generated at this difficulty yet).
async function requestOrNull<T>(path: string, options: RequestOptions = {}): Promise<T | null> {
  try {
    return await request<T>(path, options);
  } catch (err) {
    if (err instanceof ApiError && err.status === 404) return null;
    throw err;
  }
}

// --- Auth ---

export async function signup(email: string, password: string, fullName?: string): Promise<User> {
  return request<User>("/api/auth/signup", {
    method: "POST",
    body: { email, password, full_name: fullName || null },
  });
}

export async function login(email: string, password: string): Promise<{ access_token: string; token_type: string }> {
  // The backend uses FastAPI's OAuth2PasswordRequestForm, which expects a
  // form-encoded body with a `username` field (not JSON, and not `email`).
  const form = new URLSearchParams();
  form.set("username", email);
  form.set("password", password);
  return request("/api/auth/login", { method: "POST", body: form.toString(), isForm: true });
}

export async function getMe(token: string): Promise<User> {
  return request<User>("/api/users/me", { token });
}

// --- Subjects / topics ---

export async function getSubjects(): Promise<Subject[]> {
  return request<Subject[]>("/api/subjects");
}

export async function getTopicsForSubject(subjectId: string): Promise<Topic[]> {
  return request<Topic[]>(`/api/subjects/${subjectId}/topics`);
}

export async function getTopic(topicId: string): Promise<Topic> {
  return request<Topic>(`/api/topics/${topicId}`);
}

// --- Assessments ---

export async function startAssessment(token: string, subjectId: string): Promise<AssessmentStartResponse> {
  return request<AssessmentStartResponse>("/api/assessments/start", {
    method: "POST",
    token,
    body: { subject_id: subjectId },
  });
}

export interface AssessmentAnswerInput {
  question_id: string;
  user_answer: string;
  response_time_seconds?: number;
}

export async function submitAssessment(
  token: string,
  assessmentId: string,
  answers: AssessmentAnswerInput[]
): Promise<AssessmentSubmitResponse> {
  return request<AssessmentSubmitResponse>(`/api/assessments/${assessmentId}/submit`, {
    method: "POST",
    token,
    body: { answers },
  });
}

// --- Roadmap ---

export async function generateRoadmap(token: string, subjectId: string): Promise<Roadmap> {
  return request<Roadmap>("/api/roadmap/generate", {
    method: "POST",
    token,
    body: { subject_id: subjectId },
  });
}

export async function getActiveRoadmap(token: string, subjectId: string): Promise<Roadmap | null> {
  return requestOrNull<Roadmap>(`/api/roadmap/active/${subjectId}`, { token });
}

// --- Study material ---

export async function generateStudyMaterial(
  token: string,
  topicId: string,
  difficultyLevel: number,
  forceRegenerate = false
): Promise<StudyMaterial> {
  return request<StudyMaterial>("/api/study-material/generate", {
    method: "POST",
    token,
    body: { topic_id: topicId, difficulty_level: difficultyLevel, force_regenerate: forceRegenerate },
  });
}

export async function getCachedStudyMaterial(
  token: string,
  topicId: string,
  difficultyLevel: number
): Promise<StudyMaterial | null> {
  return requestOrNull<StudyMaterial>(`/api/study-material/${topicId}?difficulty_level=${difficultyLevel}`, {
    token,
  });
}

// --- Adaptive quiz ---

export async function getNextQuizQuestion(token: string, topicId: string): Promise<QuizNextResponse> {
  return request<QuizNextResponse>("/api/quiz/next", {
    method: "POST",
    token,
    body: { topic_id: topicId },
  });
}

export async function submitQuizAnswer(
  token: string,
  questionId: string,
  userAnswer: string,
  responseTimeSeconds?: number
): Promise<QuizSubmitResponse> {
  return request<QuizSubmitResponse>("/api/quiz/submit", {
    method: "POST",
    token,
    body: { question_id: questionId, user_answer: userAnswer, response_time_seconds: responseTimeSeconds },
  });
}

// --- Recommendations ---

export async function getRecommendations(token: string, subjectId: string): Promise<Recommendations> {
  return request<Recommendations>(`/api/recommendations/${subjectId}`, { token });
}

// --- Progress dashboard ---

export async function getProgressOverview(token: string, subjectId: string): Promise<ProgressOverview> {
  return request<ProgressOverview>(`/api/progress/${subjectId}`, { token });
}

export async function getProgressHistory(token: string, subjectId: string, days = 30): Promise<ProgressHistory> {
  return request<ProgressHistory>(`/api/progress/${subjectId}/history?days=${days}`, { token });
}

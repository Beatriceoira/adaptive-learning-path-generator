// Mirrors backend/app/schemas/*.py field-for-field. Keep these in sync if the
// backend response models change -- FastAPI's default JSON key casing matches
// the Python attribute names 1:1 (no camelCase conversion), so these interfaces
// use the same snake_case field names the API actually returns.

export interface User {
  id: string;
  email: string;
  full_name: string | null;
  is_active: boolean;
}

export interface Subject {
  id: string;
  name: string;
  description: string | null;
}

export interface Topic {
  id: string;
  subject_id: string;
  name: string;
  description: string | null;
  difficulty_level: number;
}

// --- Assessments (phase 3) ---

export interface AssessmentQuestion {
  id: string;
  topic_id: string;
  difficulty_level: number;
  question_type: string;
  prompt: string;
  choices: string[] | null;
}

export interface AssessmentStartResponse {
  assessment_id: string;
  subject_id: string;
  questions: AssessmentQuestion[];
}

export interface TopicMasteryResult {
  topic_id: string;
  topic_name: string;
  correct: number;
  total: number;
  mastery_probability: number;
}

export interface AssessmentSubmitResponse {
  assessment_id: string;
  status: string;
  overall_score: number;
  topic_results: TopicMasteryResult[];
}

// --- Roadmap (phase 4) ---

export interface RoadmapStep {
  topic_id: string;
  topic_name: string;
  sequence_order: number;
  status: string; // "not_started" | "in_progress" | "completed"
}

export interface Roadmap {
  id: string;
  subject_id: string;
  created_at: string;
  is_active: boolean;
  rationale: string | null;
  steps: RoadmapStep[];
}

// --- Study material (phase 4) ---

export interface StudyMaterial {
  id: string;
  topic_id: string;
  difficulty_level: number;
  content_markdown: string;
  generated_at: string;
}

// --- Adaptive quiz (phase 5) ---

export interface QuizNextResponse {
  question_id: string;
  topic_id: string;
  difficulty_level: number;
  question_type: string;
  prompt: string;
  choices: string[] | null;
  freshly_generated: boolean;
}

export interface QuizSubmitResponse {
  is_correct: boolean;
  correct_answer: string;
  explanation: string | null;
  mastery_probability: number;
  attempts_count: number;
  correct_count: number;
  next_difficulty_level: number;
}

// --- Recommendations (phase 6) ---

export interface WeakTopic {
  topic_id: string;
  topic_name: string;
  mastery_probability: number;
  attempts_count: number;
  recommended_difficulty: number;
}

export interface NextUpTopic {
  topic_id: string;
  topic_name: string;
  sequence_order: number;
}

export interface Recommendations {
  subject_id: string;
  weak_topics: WeakTopic[];
  next_up: NextUpTopic[];
  message: string;
}

// --- Progress dashboard (phase 8) ---

export interface TopicMasterySnapshot {
  topic_id: string;
  topic_name: string;
  mastery_probability: number;
  attempts_count: number;
  correct_count: number;
  is_weak_topic: boolean;
}

export interface ProgressOverview {
  subject_id: string;
  topics_total: number;
  topics_mastered: number;
  overall_accuracy: number | null;
  total_attempts: number;
  total_correct: number;
  weak_topic_count: number;
  roadmap_completion_pct: number | null;
  topic_mastery: TopicMasterySnapshot[];
}

export interface DailyActivity {
  date: string;
  attempts: number;
  correct: number;
}

export interface ProgressHistory {
  subject_id: string;
  days: number;
  daily_activity: DailyActivity[];
}

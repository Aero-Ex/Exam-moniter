export enum UserRole {
  STUDENT = 'student',
  TEACHER = 'teacher',
  ADMIN = 'admin',
}

export enum QuestionType {
  MCQ = 'mcq',
  SHORT_ANSWER = 'short_answer',
  LONG_ANSWER = 'long_answer',
  CODING = 'coding',
}

export enum AlertType {
  LOOKING_AWAY = 'looking_away',
  MULTIPLE_PEOPLE = 'multiple_people',
  PHONE_DETECTED = 'phone_detected',
  READING_FROM_MATERIAL = 'reading_from_material',
  TAB_SWITCH = 'tab_switch',
  SUSPICIOUS_ACTIVITY = 'suspicious_activity',
}

export interface User {
  id: number;
  email: string;
  username: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;
}

export interface Question {
  id: number;
  exam_id: number;
  question_text: string;
  question_type: QuestionType;
  points: number;
  order: number | null;
  options?: Record<string, string>;
  correct_answer?: string;
  test_cases?: Array<{ input: string; expected_output: string }>;
  created_at: string;
}

export interface Exam {
  id: number;
  title: string;
  description: string | null;
  duration_minutes: number;
  start_time: string;
  end_time: string;
  creator_id: number;
  passing_score: number;
  allow_review: boolean;
  shuffle_questions: boolean;
  proctoring_enabled: boolean;
  cheating_threshold: number;
  created_at: string;
  questions?: Question[];
  total_questions?: number;
}

export interface ExamSession {
  id: number;
  exam_id: number;
  student_id: number;
  start_time: string;
  end_time: string | null;
  is_submitted: boolean;
  auto_submitted: boolean;
  cheating_score: number;
  total_alerts: number;
  video_recording_url: string | null;
  screen_recording_url: string | null;
}

export interface Answer {
  id: number;
  question_id: number;
  answer_text: string;
  is_correct: boolean | null;
  points_earned: number;
}

export interface Submission {
  id: number;
  session_id: number;
  student_id: number;
  exam_id: number;
  submitted_at: string;
  total_score: number;
  max_score: number | null;
  percentage: number | null;
  is_passed: boolean | null;
  graded: boolean;
  answers: Answer[];
}

export interface MonitoringEvent {
  id: number;
  session_id: number;
  event_type: AlertType;
  timestamp: string;
  confidence: number;
  description: string;
  evidence_url: string | null;
  ai_analysis: Record<string, any> | null;
  severity: number;
}

export interface BehaviorAnalysisReport {
  session_id: number;
  total_alerts: number;
  alert_breakdown: Record<string, number>;
  timeline: MonitoringEvent[];
  risk_score: number;
  summary: string;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  username: string;
  full_name: string;
  password: string;
  role?: UserRole;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

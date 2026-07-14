export type Role = "student" | "instructor" | "admin";

export interface AuthToken {
  access_token: string;
  token_type: string;
  role: Role;
  user_id: number;
  full_name: string;
  is_platform_admin?: boolean;
}

export interface Activity {
  id: number;
  sequence: number;
  activity_type: "socratic" | "retrieval" | "debugging" | "explanation" | "practice";
  prompt: string;
  payload?: { focus?: string; hint?: string } | null;
}

export type RemediationStatus = "pending" | "in_progress" | "completed" | "dismissed";

export interface RemediationModule {
  id: number;
  student_id: number;
  course_id: number;
  concept_id: number;
  strategy: string;
  status: RemediationStatus;
  title: string;
  rationale?: string | null;
  generated_by_model?: string | null;
  grounded_on?: string[] | null;
  completed_at?: string | null;
  activities: Activity[];
}

export interface Mastery {
  concept_id: number;
  concept_key?: string | null;
  concept_name?: string | null;
  mastery_score: number;
  status: "at_risk" | "developing" | "mastered";
  evidence_count: number;
}

export interface StudentDashboard {
  student_id: number;
  full_name: string;
  masteries: Mastery[];
  open_modules: RemediationModule[];
  completed_modules: number;
}

export interface ResponseFeedback {
  id: number;
  activity_id: number;
  response_text: string;
  is_correct?: boolean | null;
  feedback?: string | null;
  resolves_misconception?: boolean | null;
}

export interface ClassBrief {
  health_pct?: number | null;
  students_total: number;
  needs_attention: number;
  top_concept?: string | null;
  top_concept_mastery?: number | null;
  top_concept_affected?: number | null;
  top_misconception?: string | null;
  ai_sessions: number;
  ai_completed: number;
  not_started: number;
  brief: string;
  recommendation: string;
}

export interface ConceptRisk {
  concept_id: number;
  concept_key: string;
  concept_name: string;
  avg_mastery: number;
  at_risk_count: number;
  total_students: number;
}

export interface InstructorAnalytics {
  course_id: number;
  course_title: string;
  enrolled_students: number;
  concept_risks: ConceptRisk[];
  modules_generated: number;
  modules_completed: number;
}

export interface Course {
  id: number;
  code: string;
  title: string;
  term: string;
  brightspace_course_id?: string | null;
}

export interface ConceptOut {
  id: number;
  key: string;
  name: string;
  description?: string | null;
  sequence: number;
  common_misconceptions?: string | null;
  prerequisite_keys?: string[];
}

export interface CourseDetail extends Course {
  concepts: ConceptOut[];
}

// ---- Course materials ----
export interface Material {
  id: number;
  course_id: number;
  concept_id?: number | null;
  title: string;
  filename: string;
  content_type: string;
  size_bytes: number;
  has_text: boolean;
  created_at: string;
}

// ---- Instructor detail views ----
export interface RosterEntry {
  student_id: number;
  full_name: string;
  email: string;
  avg_mastery: number;
  at_risk_concepts: number;
  open_modules: number;
  completed_modules: number;
}

export interface ResultDetail {
  id: number;
  assessment_id: number;
  assessment_title: string;
  assessment_type: string;
  score: number;
  attempts?: number | null;
  time_on_task_minutes?: number | null;
  submitted_late?: boolean | null;
  rubric_feedback?: string | null;
  item_scores: Array<{
    concept_key: string; earned: number; max: number; question?: string;
    choices?: string[]; selected?: string; correct?: string;
    is_correct?: boolean; misconception?: string | null;
  }>;
  rubric_criteria: Array<{
    criterion: string; concept_key: string; level: string;
    points: number; max_points: number; comment?: string;
  }>;
  created_at: string;
}

export interface ModuleSummary {
  id: number;
  concept_id: number;
  concept_name?: string | null;
  title: string;
  status: RemediationStatus;
  strategy: string;
  grounded_on?: string[] | null;
  activity_count: number;
  response_count: number;
  created_at: string;
}

export interface StudentDetailData {
  student_id: number;
  full_name: string;
  email: string;
  masteries: Mastery[];
  results: ResultDetail[];
  modules: ModuleSummary[];
}

export interface ConceptStat {
  concept_key: string;
  concept_name: string;
  avg: number;
  n: number;
}

export interface AssessmentBreakdown {
  assessment_id: number;
  title: string;
  type: string;
  adaptive_enabled: boolean;
  submissions: number;
  avg_score: number;
  concept_stats: ConceptStat[];
  sample_rubric_feedback: string[];
}

export interface ResponseDetail {
  id: number;
  response_text: string;
  is_correct?: boolean | null;
  resolves_misconception?: boolean | null;
  feedback?: string | null;
}

export interface ActivityWithResponses {
  id: number;
  sequence: number;
  activity_type: string;
  prompt: string;
  responses: ResponseDetail[];
}

export interface ModuleWithStudent {
  id: number;
  student_id: number;
  student_name: string;
  concept_name?: string | null;
  title: string;
  status: RemediationStatus;
  strategy: string;
  rationale?: string | null;
  grounded_on?: string[] | null;
  created_at: string;
  activities: ActivityWithResponses[];
  transcript: { role: string; content: string }[];
}

// ---- Institution usage (institution / IT admin) ----
export interface InstitutionCourseRow {
  course_id: number;
  code: string;
  title: string;
  students: number;
  modules_completed: number;
  avg_mastery: number;
}

export interface InstitutionUsage {
  tenant_name: string;
  lms_connected: boolean;
  courses: number;
  students: number;
  instructors: number;
  sessions_started: number;
  modules_generated: number;
  modules_completed: number;
  completion_rate: number;
  course_rows: InstitutionCourseRow[];
}

// ---- Sales leads (platform admin) ----
export interface Lead {
  id: number;
  kind: string;
  name: string;
  email: string;
  organization?: string | null;
  role?: string | null;
  plan?: string | null;
  message?: string | null;
  status: string;
  created_at: string;
}

// ---- LTI tool config + LMS registrations ----
export interface LtiToolConfig {
  title: string;
  deployment_mode?: "community" | "hosted";
  lms_connected?: boolean;
  oidc_initiation_url: string;
  target_link_uri: string;
  redirect_uris: string[];
  public_jwks_url: string;
  deep_linking_url: string;
  dynamic_registration_url: string;
  scopes: string[];
}

export interface LtiDeploymentView {
  id: number;
  deployment_id: string;
  label?: string | null;
}

export interface LtiRegistrationView {
  id: number;
  name: string;
  issuer: string;
  client_id: string;
  auth_login_url: string;
  auth_token_url: string;
  key_set_url: string;
  audience?: string | null;
  active: boolean;
  auto_register_deployments: boolean;
  deployments: LtiDeploymentView[];
}

// ---- Institution (tenant) AI + privacy settings ----
export interface TenantSettings {
  id: number;
  name: string;
  slug: string;
  ai_provider?: string | null;
  ai_model?: string | null;
  ai_endpoint?: string | null;
  ai_deployment?: string | null;
  external_ai_allowed: boolean;
  pii_minimization: boolean;
  ai_key_set: boolean;
  subscription_status: string;
  plan: string;
  seat_limit?: number | null;
  license_expires_at?: string | null;
}

// ---- Licensing ----
export interface TenantLicenseRow {
  id: number;
  name: string;
  slug: string;
  subscription_status: string;
  plan: string;
  seat_limit?: number | null;
  seats_used: number;
  license_expires_at?: string | null;
}

export interface LicenseStatus {
  deployment_mode?: "community" | "hosted";
  enforcement_active?: boolean;
  mode: "saas" | "self_hosted";
  enforcement_disabled: boolean;
  self_hosted?: {
    ok: boolean; reason: string; detail: string;
    customer?: string | null; plan?: string | null;
    seats?: number | null; expires_at?: string | null;
  };
  tenant?: {
    subscription_status: string; plan: string;
    seat_limit?: number | null; seats_used: number;
    license_expires_at?: string | null;
  };
}

// ---- Interactive AI-tutor session ----
export interface TutorMessage {
  id: number;
  sequence: number;
  role: "tutor" | "student";
  content: string;
  choices?: string[] | null;
}

export interface SessionEvidence {
  question?: string | null;
  chosen?: string | null;
  correct?: string | null;
  misconception?: string | null;
}

export interface SessionState {
  module_id: number;
  title: string;
  concept_id: number;
  status: RemediationStatus;
  rationale?: string | null;
  grounded_on?: string[] | null;
  messages: TutorMessage[];
  concept_name?: string | null;
  goal?: string | null;
  objectives?: string[];
  mastery_score?: number | null;
  focus_misconception?: string | null;
  evidence?: SessionEvidence | null;
}

export interface SessionTurn {
  reply: string;
  complete: boolean;
  status: RemediationStatus;
  choices?: string[] | null;
}

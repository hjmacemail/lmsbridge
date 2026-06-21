import type {
  AssessmentBreakdown,
  AuthToken,
  ConceptOut,
  Course,
  CourseDetail,
  InstitutionUsage,
  InstructorAnalytics,
  Lead,
  LicenseStatus,
  LtiRegistrationView,
  LtiToolConfig,
  Material,
  ModuleWithStudent,
  RemediationModule,
  ResponseFeedback,
  RosterEntry,
  SessionState,
  SessionTurn,
  StudentDashboard,
  StudentDetailData,
  TenantLicenseRow,
  TenantSettings,
} from "../types";

// Resolution order: runtime config (window, written by the container from API_BASE_URL),
// then build-time Vite env, then a sensible default. This lets one built image be pointed
// at any backend without rebuilding.
declare global {
  interface Window { __LMSBRIDGE_API__?: string }
}
const BASE =
  (typeof window !== "undefined" && window.__LMSBRIDGE_API__) ||
  import.meta.env.VITE_API_BASE_URL ||
  "/api/v1";
const TOKEN_KEY = "lmsbridge_token";

export function saveToken(t: AuthToken) {
  sessionStorage.setItem(TOKEN_KEY, JSON.stringify(t));
}
export function loadToken(): AuthToken | null {
  const raw = sessionStorage.getItem(TOKEN_KEY);
  return raw ? (JSON.parse(raw) as AuthToken) : null;
}
export function clearToken() {
  sessionStorage.removeItem(TOKEN_KEY);
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const token = loadToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(init.headers as Record<string, string>),
  };
  if (token) headers["Authorization"] = `Bearer ${token.access_token}`;
  const res = await fetch(`${BASE}${path}`, { ...init, headers });
  if (!res.ok) {
    const detail = await res.json().catch(() => ({}));
    throw new Error(detail.detail || `Request failed (${res.status})`);
  }
  return res.status === 204 ? (undefined as T) : ((await res.json()) as T);
}

export const api = {
  async login(email: string, password: string): Promise<AuthToken> {
    const body = new URLSearchParams({ username: email, password });
    const res = await fetch(`${BASE}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body,
    });
    if (!res.ok) throw new Error("Invalid email or password");
    return (await res.json()) as AuthToken;
  },
  me: () => request<{
    id: number; full_name: string; role: AuthToken["role"]; is_platform_admin?: boolean;
  }>("/auth/me"),
  demoLogin: (role: "student" | "instructor") =>
    request<AuthToken>("/auth/demo-login", {
      method: "POST", body: JSON.stringify({ role }),
    }),
  demoReset: () =>
    request<{ courses_reset: number; modules_regenerated: number }>(
      "/auth/demo-reset", { method: "POST" }),
  myCourses: () => request<Course[]>("/students/me/courses"),
  myDashboard: (courseId?: number) =>
    request<StudentDashboard>(
      `/students/me/dashboard${courseId != null ? `?course_id=${courseId}` : ""}`,
    ),
  myModules: () => request<RemediationModule[]>("/remediation/modules"),
  getModule: (id: number) => request<RemediationModule>(`/remediation/modules/${id}`),
  startSession: (id: number, lang?: string) =>
    request<SessionState>(
      `/remediation/modules/${id}/session/start${lang ? `?lang=${encodeURIComponent(lang)}` : ""}`,
      { method: "POST" }),
  sendSessionMessage: (id: number, text: string, lang?: string) =>
    request<SessionTurn>(`/remediation/modules/${id}/session/message`, {
      method: "POST", body: JSON.stringify({ text, lang }),
    }),
  startModule: (id: number) =>
    request<RemediationModule>(`/remediation/modules/${id}/start`, { method: "POST" }),
  completeModule: (id: number) =>
    request<RemediationModule>(`/remediation/modules/${id}/complete`, { method: "POST" }),
  respond: (activityId: number, text: string) =>
    request<ResponseFeedback>(`/remediation/activities/${activityId}/respond`, {
      method: "POST",
      body: JSON.stringify({ response_text: text }),
    }),
  courses: () => request<Course[]>("/courses"),
  course: (courseId: number) => request<CourseDetail>(`/courses/${courseId}`),
  createCourse: (payload: { code: string; title: string; term: string }) =>
    request<Course>("/courses", { method: "POST", body: JSON.stringify(payload) }),
  addConcept: (courseId: number, payload: {
    key: string; name: string; description?: string; sequence?: number;
    common_misconceptions?: string; prerequisite_keys?: string[];
  }) => request<ConceptOut>(`/courses/${courseId}/concepts`, {
    method: "POST", body: JSON.stringify(payload),
  }),
  deleteConcept: (courseId: number, conceptId: number) =>
    request<void>(`/courses/${courseId}/concepts/${conceptId}`, { method: "DELETE" }),
  createAssessment: (courseId: number, payload: {
    title: string; type: string; max_score: number;
  }) => request<{ id: number; title: string }>(`/courses/${courseId}/assessments`, {
    method: "POST", body: JSON.stringify(payload),
  }),
  analytics: (courseId: number) =>
    request<InstructorAnalytics>(`/analytics/courses/${courseId}`),
  syncCourse: (courseId: number) =>
    request<Record<string, unknown>>(`/assessments/sync?course_id=${courseId}`, {
      method: "POST",
    }),

  // ---- LMS sync (LTI Advantage services) ----
  syncRoster: (courseId: number) =>
    request<{ synced: number; members: number }>(
      `/lti/courses/${courseId}/sync-roster`, { method: "POST" }),
  syncAssessments: (courseId: number) =>
    request<{ assessments: number; ingested: number; modules: number }>(
      `/lti/courses/${courseId}/sync-assessments`, { method: "POST" }),
  lmsContext: (courseId: number) =>
    request<{
      provider: string | null; lms_course_ref: string | null;
      has_roster_link: boolean; has_gradebook_link: boolean;
    }>(`/lti/courses/${courseId}/lms-context`),
  importLmsFiles: (
    courseId: number, provider: string, baseUrl: string, accessToken: string, lmsCourseId: string,
  ) =>
    request<{ imported: number; skipped: number; total: number }>(
      `/materials/import/lms`,
      { method: "POST", body: JSON.stringify({
        course_id: courseId, provider, base_url: baseUrl,
        access_token: accessToken, lms_course_id: lmsCourseId,
      }) },
    ),

  // ---- Instructor detail views ----
  roster: (courseId: number) =>
    request<RosterEntry[]>(`/analytics/courses/${courseId}/roster`),
  studentDetail: (courseId: number, studentId: number) =>
    request<StudentDetailData>(`/analytics/courses/${courseId}/students/${studentId}`),
  assessmentBreakdown: (courseId: number) =>
    request<AssessmentBreakdown[]>(`/analytics/courses/${courseId}/assessments`),
  setAdaptive: (assessmentId: number, enabled: boolean) =>
    request<{ adaptive_enabled: boolean }>(
      `/assessments/${assessmentId}/adaptive`,
      { method: "PATCH", body: JSON.stringify({ enabled }) },
    ),
  recompute: (courseId: number) =>
    request<{ results_replayed: number; modules_triggered: number }>(
      `/assessments/recompute?course_id=${courseId}`, { method: "POST" },
    ),

  // ---- Institution usage (institution / IT admin) ----
  institutionUsage: () => request<InstitutionUsage>("/analytics/institution"),

  // ---- Sales leads (platform admin) ----
  leads: () => request<Lead[]>("/leads"),

  // ---- LTI tool config + LMS registrations (admin) ----
  ltiConfig: () => request<LtiToolConfig>("/lti/config"),
  ltiRegistrations: () => request<LtiRegistrationView[]>("/lti/registrations"),
  createLtiRegistration: (payload: {
    name: string; issuer: string; client_id: string; auth_login_url: string;
    auth_token_url: string; key_set_url: string; audience?: string; deployment_id?: string;
  }) => request<LtiRegistrationView>("/lti/registrations", {
    method: "POST", body: JSON.stringify(payload),
  }),
  deleteLtiRegistration: (id: number) =>
    request<void>(`/lti/registrations/${id}`, { method: "DELETE" }),

  // ---- Licensing ----
  licenseStatus: () => request<LicenseStatus>("/tenants/license/status"),
  licenses: () => request<TenantLicenseRow[]>("/tenants/licenses"),
  updateTenantLicense: (id: number, payload: {
    subscription_status?: string; plan?: string;
    seat_limit?: number | null; license_expires_at?: string | null;
  }) => request<TenantLicenseRow>(`/tenants/${id}/license`, {
    method: "PUT", body: JSON.stringify(payload),
  }),

  // ---- Institution (tenant) AI + privacy settings (admin) ----
  getTenant: () => request<TenantSettings>("/tenants/me"),
  updateTenantAi: (payload: Partial<TenantSettings> & { ai_api_key?: string }) =>
    request<TenantSettings>("/tenants/me/ai", {
      method: "PUT", body: JSON.stringify(payload),
    }),
  courseRemediation: (courseId: number) =>
    request<ModuleWithStudent[]>(`/analytics/courses/${courseId}/remediation`),

  // ---- Course materials ----
  materials: (courseId: number) =>
    request<Material[]>(`/materials?course_id=${courseId}`),
  uploadMaterial: async (
    courseId: number, file: File, title: string, conceptId?: number | null
  ): Promise<Material> => {
    const token = loadToken();
    const form = new FormData();
    form.append("course_id", String(courseId));
    form.append("title", title);
    if (conceptId != null) form.append("concept_id", String(conceptId));
    form.append("file", file);
    const res = await fetch(`${BASE}/materials`, {
      method: "POST",
      headers: token ? { Authorization: `Bearer ${token.access_token}` } : {},
      body: form,
    });
    if (!res.ok) {
      const d = await res.json().catch(() => ({}));
      throw new Error(d.detail || `Upload failed (${res.status})`);
    }
    return (await res.json()) as Material;
  },
  deleteMaterial: (id: number) =>
    request<void>(`/materials/${id}`, { method: "DELETE" }),

  // ---- Authenticated file downloads (CSV / material) ----
  downloadUrl: (path: string) => `${BASE}${path}`,
  authedDownload: async (path: string, filename: string): Promise<void> => {
    const token = loadToken();
    const res = await fetch(`${BASE}${path}`, {
      headers: token ? { Authorization: `Bearer ${token.access_token}` } : {},
    });
    if (!res.ok) throw new Error(`Download failed (${res.status})`);
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  },
};

// ---- Sage (standalone AI Q&A board) ----
export interface SageAuth {
  access_token: string; token_type: string; user_id: number; full_name: string; role: string;
}
export interface SageClassSummary {
  id: number; name: string; subject: string | null; role: string;
  join_code: string; member_count: number; post_count: number;
}
export interface SageAnswerItem {
  id: number; body: string; is_ai: boolean; is_instructor: boolean;
  endorsed: boolean; author: string; created_at: string;
}
export interface SagePostDetail {
  id: number; class_id: number; title: string; body: string; tags: string | null;
  anonymous: boolean; resolved: boolean; author: string; answers: SageAnswerItem[];
  ai_misconception?: string | null; created_at: string;
}
export interface SagePostItem {
  id: number; title: string; tags: string | null; anonymous: boolean; resolved: boolean;
  author: string; answer_count: number; has_endorsed: boolean;
  ai_misconception?: string | null; created_at: string;
}
export interface SageInsights {
  members: number; total_posts: number; open_count: number; resolved_count: number;
  unanswered_by_humans: number; top_tags: { tag: string; count: number }[];
  top_misconceptions: { label: string; count: number }[];
}

export const sageApi = {
  signup: (full_name: string, email: string, password: string) =>
    request<SageAuth>(`/sage/signup`, { method: "POST",
      body: JSON.stringify({ full_name, email, password }) }),
  guestJoin: (join_code: string, full_name: string) =>
    request<SageAuth>(`/sage/guest`, { method: "POST",
      body: JSON.stringify({ join_code, full_name }) }),
  joinSignup: (join_code: string, full_name: string, email: string, password: string) =>
    request<SageAuth>(`/sage/join`, { method: "POST",
      body: JSON.stringify({ join_code, full_name, email, password }) }),
  login: (email: string, password: string) => api.login(email, password),
  classes: () => request<SageClassSummary[]>(`/sage/classes`),
  createClass: (name: string, subject: string) =>
    request<SageClassSummary>(`/sage/classes`, { method: "POST",
      body: JSON.stringify({ name, subject }) }),
  joinExisting: (join_code: string) =>
    request<{ class_id: number; name: string }>(`/sage/classes/join`, { method: "POST",
      body: JSON.stringify({ join_code }) }),
  classDetail: (id: number) => request<SageClassSummary>(`/sage/classes/${id}`),
  posts: (classId: number) => request<SagePostItem[]>(`/sage/classes/${classId}/posts`),
  createPost: (classId: number, title: string, body: string, tags: string, anonymous: boolean) =>
    request<SagePostDetail>(`/sage/classes/${classId}/posts`, { method: "POST",
      body: JSON.stringify({ title, body, tags, anonymous }) }),
  post: (postId: number) => request<SagePostDetail>(`/sage/posts/${postId}`),
  answer: (postId: number, body: string) =>
    request<SagePostDetail>(`/sage/posts/${postId}/answers`, { method: "POST",
      body: JSON.stringify({ body }) }),
  endorse: (answerId: number) =>
    request<{ id: number; endorsed: boolean }>(`/sage/answers/${answerId}/endorse`,
      { method: "POST" }),
  resolve: (postId: number) =>
    request<{ id: number; resolved: boolean }>(`/sage/posts/${postId}/resolve`,
      { method: "POST" }),
  insights: (classId: number) => request<SageInsights>(`/sage/classes/${classId}/insights`),
};

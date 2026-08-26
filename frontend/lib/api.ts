const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";
const API_KEY = process.env.NEXT_PUBLIC_API_KEY ?? "";

function authHeaders(extra?: Record<string, string>): Record<string, string> {
  return {
    ...(API_KEY ? { "X-API-Key": API_KEY } : {}),
    ...extra,
  };
}

export type HealthStatus = {
  status: "ok" | "error";
  env?: string;
  detail?: string;
};

export type LeadSearchRequest = {
  business_type: string;
  location: string;
  city?: string;
  country?: string;
  latitude?: number;
  longitude?: number;
  radius_meters?: number;
  keywords?: string;
  source?: string;
  max_results?: number;
};

export type LeadSearchRun = {
  id: string;
  mode: string;
  status: "queued" | "running" | "completed" | "failed";
  new_leads_count: number;
  duplicate_count: number;
  failed_count: number;
  error_message: string | null;
  started_at: string | null;
  completed_at: string | null;
};

export type Lead = {
  id: string;
  business_name: string;
  category: string | null;
  address: string | null;
  city: string | null;
  country: string | null;
  latitude: number | null;
  longitude: number | null;
  phone: string | null;
  email: string | null;
  website: string | null;
  contact_name: string | null;
  source: string;
  source_id: string;
  source_url: string | null;
  rating: number | null;
  review_count: number | null;
  status: string;
  first_seen: string;
  last_seen: string;
  created_at: string;
  updated_at: string;
};

export type LeadSearchResponse = {
  run: LeadSearchRun;
  leads: Lead[];
};

export type SearchConfiguration = {
  id: string;
  name: string;
  business_type: string;
  location: string;
  city: string | null;
  country: string | null;
  latitude: number | null;
  longitude: number | null;
  radius_meters: number | null;
  keywords: string | null;
  source: string;
  max_results: number;
  is_enabled: boolean;
  schedule: string | null;
  created_at: string;
  updated_at: string;
  last_run: LeadSearchRun | null;
};

export type SearchConfigurationCreate = {
  name: string;
  business_type: string;
  location: string;
  latitude?: number;
  longitude?: number;
  radius_meters?: number;
  keywords?: string;
  max_results?: number;
  source?: string;
};

export type SearchConfigurationRunResponse = {
  search_configuration: SearchConfiguration;
  run: LeadSearchRun;
  leads: Lead[];
};

export type LeadListResponse = {
  items: Lead[];
  total: number;
  page: number;
  page_size: number;
};

async function getJson<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE_URL}${path}`, {
    cache: "no-store",
    headers: authHeaders(),
  });
  if (!res.ok) {
    throw new Error(`Request to ${path} failed with status ${res.status}`);
  }
  return res.json() as Promise<T>;
}

async function sendJson<T>(
  path: string,
  method: "POST" | "PATCH" | "DELETE",
  body?: unknown
): Promise<T> {
  const res = await fetch(`${API_BASE_URL}${path}`, {
    method,
    headers: authHeaders(body ? { "Content-Type": "application/json" } : undefined),
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) {
    let detail = "";
    try {
      const data = await res.json();
      detail = data.detail ?? "";
    } catch {
      // response wasn't JSON; fall back to status-only message
    }
    throw new Error(detail || `Request to ${path} failed with status ${res.status}`);
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

export async function getApiHealth(): Promise<HealthStatus> {
  return getJson<HealthStatus>("/api/health");
}

export async function getDbHealth(): Promise<HealthStatus> {
  return getJson<HealthStatus>("/api/health/db");
}

export async function getLeads(params: {
  page?: number;
  page_size?: number;
  search?: string;
  status_filter?: string;
} = {}): Promise<LeadListResponse> {
  const query = new URLSearchParams();
  if (params.page) query.set("page", String(params.page));
  if (params.page_size) query.set("page_size", String(params.page_size));
  if (params.search) query.set("search", params.search);
  if (params.status_filter) query.set("status_filter", params.status_filter);
  return getJson<LeadListResponse>(`/api/leads?${query.toString()}`);
}

export async function searchLeads(
  payload: LeadSearchRequest
): Promise<LeadSearchResponse> {
  return sendJson<LeadSearchResponse>("/api/leads/search", "POST", payload);
}

export async function getSearchConfigurations(): Promise<
  SearchConfiguration[]
> {
  return getJson<SearchConfiguration[]>("/api/search-configurations");
}

export async function createSearchConfiguration(
  payload: SearchConfigurationCreate
): Promise<SearchConfiguration> {
  return sendJson<SearchConfiguration>(
    "/api/search-configurations",
    "POST",
    payload
  );
}

export async function runSearchConfiguration(
  id: string
): Promise<SearchConfigurationRunResponse> {
  return sendJson<SearchConfigurationRunResponse>(
    `/api/search-configurations/${id}/run`,
    "POST"
  );
}

export async function enableAutomation(
  id: string,
  schedule: string
): Promise<SearchConfiguration> {
  return sendJson<SearchConfiguration>(
    `/api/search-configurations/${id}/enable`,
    "POST",
    { schedule }
  );
}

export async function disableAutomation(
  id: string
): Promise<SearchConfiguration> {
  return sendJson<SearchConfiguration>(
    `/api/search-configurations/${id}/disable`,
    "POST"
  );
}

export type QualificationFields = Record<string, string[]>;

export type QualificationRule = {
  id: string;
  name: string;
  description: string | null;
  field: string;
  operator: string;
  expected_value: string | null;
  enabled: boolean;
  priority: number;
  created_at: string;
  updated_at: string;
};

export type QualificationRuleInput = {
  name: string;
  description?: string;
  field: string;
  operator: string;
  expected_value?: string;
  enabled?: boolean;
  priority?: number;
};

export type RuleReference = { id: string; name: string };

export type LeadQualificationResult = {
  id: string;
  lead_id: string;
  result: "qualified" | "not_qualified" | "needs_review";
  score: number;
  passed_rules: RuleReference[];
  failed_rules: RuleReference[];
  run_at: string;
  is_override: boolean;
  previous_result: string | null;
  override_reason: string | null;
  overridden_by: string | null;
};

export async function getQualificationFields(): Promise<QualificationFields> {
  return getJson<QualificationFields>("/api/qualification-rules/fields");
}

export async function getQualificationRules(): Promise<QualificationRule[]> {
  return getJson<QualificationRule[]>("/api/qualification-rules");
}

export async function createQualificationRule(
  payload: QualificationRuleInput
): Promise<QualificationRule> {
  return sendJson<QualificationRule>("/api/qualification-rules", "POST", payload);
}

export async function updateQualificationRule(
  id: string,
  payload: Partial<QualificationRuleInput>
): Promise<QualificationRule> {
  return sendJson<QualificationRule>(
    `/api/qualification-rules/${id}`,
    "PATCH",
    payload
  );
}

export async function deleteQualificationRule(id: string): Promise<void> {
  return sendJson<void>(`/api/qualification-rules/${id}`, "DELETE");
}

export async function qualifyLead(
  leadId: string
): Promise<LeadQualificationResult> {
  return sendJson<LeadQualificationResult>(
    `/api/leads/${leadId}/qualify`,
    "POST"
  );
}

export async function getLeadQualificationHistory(
  leadId: string
): Promise<LeadQualificationResult[]> {
  return getJson<LeadQualificationResult[]>(
    `/api/leads/${leadId}/qualification`
  );
}

export async function overrideQualification(
  leadId: string,
  payload: { result: string; reason: string; overridden_by?: string }
): Promise<LeadQualificationResult> {
  return sendJson<LeadQualificationResult>(
    `/api/leads/${leadId}/qualification`,
    "PATCH",
    payload
  );
}

export type Service = {
  id: string;
  name: string;
  description: string | null;
  category: string | null;
  enabled: boolean;
  created_at: string;
  updated_at: string;
};

export type ServiceInput = {
  name: string;
  description?: string;
  category?: string;
  enabled?: boolean;
};

export type AnalysisRule = {
  id: string;
  name: string;
  description: string;
  enabled: boolean;
  ai_suggested: boolean;
  created_at: string;
  updated_at: string;
};

export type AnalysisRuleInput = {
  name: string;
  description: string;
  enabled?: boolean;
};

export type ServiceRecommendation = {
  id: string;
  lead_id: string;
  analysis_id: string;
  recommended_service_id: string;
  recommended_service_name: string;
  secondary_service_ids: string[];
  reasoning: string;
  human_decision: "approved" | "rejected" | null;
  decision_reason: string | null;
  decided_at: string | null;
  created_at: string;
};

export type LeadAnalysisResult = {
  id: string;
  lead_id: string;
  summary: string;
  opportunities: string[];
  score: number;
  confidence: number;
  evidence: string[];
  missing_information: string[];
  next_action: string;
  needs_review: boolean;
  created_at: string;
  recommendation: ServiceRecommendation | null;
};

export async function getServices(): Promise<Service[]> {
  return getJson<Service[]>("/api/services");
}

export async function createService(payload: ServiceInput): Promise<Service> {
  return sendJson<Service>("/api/services", "POST", payload);
}

export async function updateService(
  id: string,
  payload: Partial<ServiceInput>
): Promise<Service> {
  return sendJson<Service>(`/api/services/${id}`, "PATCH", payload);
}

export async function getAnalysisRules(): Promise<AnalysisRule[]> {
  return getJson<AnalysisRule[]>("/api/analysis-rules");
}

export async function createAnalysisRule(
  payload: AnalysisRuleInput
): Promise<AnalysisRule> {
  return sendJson<AnalysisRule>("/api/analysis-rules", "POST", payload);
}

export async function updateAnalysisRule(
  id: string,
  payload: Partial<AnalysisRuleInput>
): Promise<AnalysisRule> {
  return sendJson<AnalysisRule>(`/api/analysis-rules/${id}`, "PATCH", payload);
}

export async function deleteAnalysisRule(id: string): Promise<void> {
  return sendJson<void>(`/api/analysis-rules/${id}`, "DELETE");
}

export async function analyzeLead(leadId: string): Promise<LeadAnalysisResult> {
  return sendJson<LeadAnalysisResult>(`/api/leads/${leadId}/analyze`, "POST");
}

export async function getLeadAnalysisHistory(
  leadId: string
): Promise<LeadAnalysisResult[]> {
  return getJson<LeadAnalysisResult[]>(`/api/leads/${leadId}/analysis`);
}

export type Template = {
  id: string;
  name: string;
  subject: string;
  body: string;
  is_ai_generated: boolean;
  created_at: string;
  updated_at: string;
};

export type TemplateInput = {
  name: string;
  subject: string;
  body: string;
  is_ai_generated?: boolean;
};

export type Message = {
  id: string;
  lead_id: string;
  template_id: string | null;
  to_email: string;
  subject: string;
  body: string;
  status: string;
  provider_response: string | null;
  is_test: boolean;
  sent_at: string | null;
  created_at: string;
};

export async function getTemplates(): Promise<Template[]> {
  return getJson<Template[]>("/api/templates");
}

export async function createTemplate(payload: TemplateInput): Promise<Template> {
  return sendJson<Template>("/api/templates", "POST", payload);
}

export async function updateLead(
  leadId: string,
  payload: { email?: string | null; phone?: string; website?: string }
): Promise<Lead> {
  return sendJson<Lead>(`/api/leads/${leadId}`, "PATCH", payload);
}

export async function getLeadMessages(leadId: string): Promise<Message[]> {
  return getJson<Message[]>(`/api/leads/${leadId}/messages`);
}

export async function generateAIDraft(
  leadId: string
): Promise<{ subject: string; body: string }> {
  return sendJson<{ subject: string; body: string }>("/api/outreach/draft", "POST", {
    lead_id: leadId,
  });
}

export async function previewOutreach(
  leadId: string,
  subject: string,
  body: string
): Promise<{ to_email: string | null; subject: string; body: string }> {
  return sendJson("/api/outreach/preview", "POST", {
    lead_id: leadId,
    subject,
    body,
  });
}

export async function sendOutreach(payload: {
  lead_id: string;
  subject: string;
  body: string;
  template_id?: string;
  is_test?: boolean;
  test_email_override?: string;
}): Promise<Message> {
  return sendJson<Message>("/api/outreach/send", "POST", payload);
}

export type InboundMessage = {
  id: string;
  lead_id: string;
  template_id: string | null;
  direction: "outbound" | "inbound";
  to_email: string | null;
  from_email: string | null;
  subject: string;
  body: string;
  status: string;
  provider_response: string | null;
  is_test: boolean;
  category: string | null;
  classification_confidence: number | null;
  classification_summary: string | null;
  suggested_action: string | null;
  review_required: boolean;
  sent_at: string | null;
  created_at: string;
};

export async function getMessages(params: {
  direction?: string;
  limit?: number;
} = {}): Promise<InboundMessage[]> {
  const query = new URLSearchParams();
  if (params.direction) query.set("direction", params.direction);
  if (params.limit) query.set("limit", String(params.limit));
  return getJson<InboundMessage[]>(`/api/messages?${query.toString()}`);
}

export async function recordReply(
  leadId: string,
  payload: { from_email: string; subject: string; body: string }
): Promise<InboundMessage> {
  return sendJson<InboundMessage>(`/api/leads/${leadId}/replies`, "POST", payload);
}

export async function classifyReplyMessage(
  messageId: string
): Promise<InboundMessage> {
  return sendJson<InboundMessage>(`/api/messages/${messageId}/classify`, "POST");
}

export async function fetchInboundReplies(): Promise<{
  fetched: number;
  matched: number;
  unmatched: number;
  unmatched_senders: string[];
  classified: number;
  classification_errors: number;
}> {
  return sendJson("/api/messages/fetch-inbound", "POST");
}

export type Call = {
  id: string;
  lead_id: string;
  reason_for_calling: string | null;
  call_objective: string | null;
  script: string | null;
  notes: string | null;
  outcome: string | null;
  follow_up_date: string | null;
  created_at: string;
  updated_at: string;
};

export type CallWorkspace = {
  lead: Lead;
  latest_analysis: LeadAnalysisResult | null;
  calls: Call[];
};

export type CallScript = {
  opening: string;
  reason_for_calling: string;
  business_observation: string;
  value_statement: string;
  discovery_questions: string[];
  objection_prompts: string[];
  next_step: string;
  full_text: string;
};

export async function getCallWorkspace(leadId: string): Promise<CallWorkspace> {
  return getJson<CallWorkspace>(`/api/leads/${leadId}/call-workspace`);
}

export async function generateCallScript(leadId: string): Promise<CallScript> {
  return sendJson<CallScript>(`/api/leads/${leadId}/call-script`, "POST");
}

export async function createCall(payload: {
  lead_id: string;
  reason_for_calling?: string;
  call_objective?: string;
  script?: string;
  notes?: string;
  outcome?: string;
}): Promise<Call> {
  return sendJson<Call>("/api/calls", "POST", payload);
}

export async function updateCall(
  callId: string,
  payload: Partial<{
    reason_for_calling: string;
    call_objective: string;
    script: string;
    notes: string;
    outcome: string;
    follow_up_date: string;
  }>
): Promise<Call> {
  return sendJson<Call>(`/api/calls/${callId}`, "PATCH", payload);
}

export type TimelineEvent = {
  type: string;
  timestamp: string;
  summary: string;
  detail: Record<string, unknown> | null;
};

export type Task = {
  id: string;
  lead_id: string;
  title: string;
  owner: string | null;
  due_date: string | null;
  priority: "low" | "medium" | "high";
  status: "pending" | "in_progress" | "done";
  notes: string | null;
  created_at: string;
  updated_at: string;
};

export type TaskInput = {
  lead_id: string;
  title: string;
  owner?: string;
  due_date?: string;
  priority?: "low" | "medium" | "high";
  status?: "pending" | "in_progress" | "done";
  notes?: string;
};

export async function getLeadTimeline(leadId: string): Promise<TimelineEvent[]> {
  return getJson<TimelineEvent[]>(`/api/leads/${leadId}/timeline`);
}

export async function changeLeadStage(
  leadId: string,
  newStage: string,
  reason?: string
): Promise<Lead> {
  return sendJson<Lead>(`/api/leads/${leadId}/stage`, "PATCH", {
    new_stage: newStage,
    reason,
  });
}

export async function getTasks(statusFilter?: string): Promise<Task[]> {
  const query = statusFilter ? `?status_filter=${statusFilter}` : "";
  return getJson<Task[]>(`/api/tasks${query}`);
}

export async function createTask(payload: TaskInput): Promise<Task> {
  return sendJson<Task>("/api/tasks", "POST", payload);
}

export async function updateTask(
  taskId: string,
  payload: Partial<TaskInput>
): Promise<Task> {
  return sendJson<Task>(`/api/tasks/${taskId}`, "PATCH", payload);
}

export async function deleteTask(taskId: string): Promise<void> {
  return sendJson<void>(`/api/tasks/${taskId}`, "DELETE");
}

export type DashboardStats = {
  total_leads: number;
  new_leads: number;
  qualified: number;
  needs_review: number;
  contacted: number;
  replies: number;
  meetings: number;
  won: number;
  lost: number;
  due_tasks: number;
  active_automation_runs: number;
};

export async function getDashboardStats(): Promise<DashboardStats> {
  return getJson<DashboardStats>("/api/dashboard/stats");
}

export async function decideRecommendation(
  leadId: string,
  recommendationId: string,
  payload: { decision: "approved" | "rejected"; reason?: string }
): Promise<ServiceRecommendation> {
  return sendJson<ServiceRecommendation>(
    `/api/leads/${leadId}/recommendation/${recommendationId}/decision`,
    "POST",
    payload
  );
}

export type Settings = {
  google_places_api_key_set: boolean;
  openai_api_key_set: boolean;
  anthropic_api_key_set: boolean;
  gemini_api_key_set: boolean;
  smtp_host: string;
  smtp_port: number;
  smtp_user: string;
  smtp_password_set: boolean;
  smtp_from_name: string;
  imap_host: string;
  imap_port: number;
};

export type SettingsUpdate = Partial<{
  google_places_api_key: string;
  openai_api_key: string;
  anthropic_api_key: string;
  gemini_api_key: string;
  smtp_host: string;
  smtp_port: number;
  smtp_user: string;
  smtp_password: string;
  smtp_from_name: string;
  imap_host: string;
  imap_port: number;
}>;

export async function getSettings(): Promise<Settings> {
  return getJson<Settings>("/api/settings");
}

export async function updateSettings(payload: SettingsUpdate): Promise<Settings> {
  return sendJson<Settings>("/api/settings", "PATCH", payload);
}

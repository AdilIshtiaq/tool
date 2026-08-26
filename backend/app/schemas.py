import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class LeadSearchRequest(BaseModel):
    business_type: str = Field(min_length=1)
    location: str = Field(min_length=1)
    city: str | None = None
    country: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    radius_meters: int | None = Field(default=None, ge=1)
    keywords: str | None = None
    source: str = "google_places"
    max_results: int = Field(default=20, ge=1, le=100)


class LeadUpdate(BaseModel):
    contact_name: str | None = None
    email: str | None = None
    phone: str | None = None
    website: str | None = None
    status: str | None = None


class LeadSearchRunOut(BaseModel):
    id: uuid.UUID
    mode: str
    status: str
    new_leads_count: int
    duplicate_count: int
    failed_count: int
    error_message: str | None
    started_at: datetime | None
    completed_at: datetime | None

    model_config = {"from_attributes": True}


class LeadOut(BaseModel):
    id: uuid.UUID
    business_name: str
    category: str | None
    address: str | None
    city: str | None
    country: str | None
    latitude: float | None
    longitude: float | None
    contact_name: str | None
    phone: str | None
    email: str | None
    website: str | None
    source: str
    source_id: str
    source_url: str | None
    rating: float | None
    review_count: int | None
    status: str
    first_seen: datetime
    last_seen: datetime
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class LeadListResponse(BaseModel):
    items: list[LeadOut]
    total: int
    page: int
    page_size: int


class LeadSearchResponse(BaseModel):
    run: LeadSearchRunOut
    leads: list[LeadOut]


class SearchConfigurationCreate(BaseModel):
    name: str = Field(min_length=1)
    business_type: str = Field(min_length=1)
    location: str = Field(min_length=1)
    city: str | None = None
    country: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    radius_meters: int | None = Field(default=None, ge=1)
    keywords: str | None = None
    source: str = "google_places"
    max_results: int = Field(default=20, ge=1, le=100)


class SearchConfigurationUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1)
    business_type: str | None = Field(default=None, min_length=1)
    location: str | None = Field(default=None, min_length=1)
    city: str | None = None
    country: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    radius_meters: int | None = Field(default=None, ge=1)
    keywords: str | None = None
    max_results: int | None = Field(default=None, ge=1, le=100)


class SearchConfigurationOut(BaseModel):
    id: uuid.UUID
    name: str
    business_type: str
    location: str
    city: str | None
    country: str | None
    latitude: float | None
    longitude: float | None
    radius_meters: int | None
    keywords: str | None
    source: str
    max_results: int
    is_enabled: bool
    schedule: str | None
    created_at: datetime
    updated_at: datetime
    last_run: LeadSearchRunOut | None = None

    model_config = {"from_attributes": True}


class SearchConfigurationRunResponse(BaseModel):
    search_configuration: SearchConfigurationOut
    run: LeadSearchRunOut
    leads: list[LeadOut]


class EnableAutomationRequest(BaseModel):
    schedule: str


class RunDueResult(BaseModel):
    search_configuration_id: uuid.UUID
    search_configuration_name: str
    run: LeadSearchRunOut


class RunDueResponse(BaseModel):
    checked: int
    executed: list[RunDueResult]


class QualificationRuleCreate(BaseModel):
    name: str = Field(min_length=1)
    description: str | None = None
    field: str = Field(min_length=1)
    operator: str = Field(min_length=1)
    expected_value: str | None = None
    enabled: bool = True
    priority: int = 0


class QualificationRuleUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1)
    description: str | None = None
    field: str | None = None
    operator: str | None = None
    expected_value: str | None = None
    enabled: bool | None = None
    priority: int | None = None


class QualificationRuleOut(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    field: str
    operator: str
    expected_value: str | None
    enabled: bool
    priority: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class RuleReference(BaseModel):
    id: str
    name: str


class LeadQualificationOut(BaseModel):
    id: uuid.UUID
    lead_id: uuid.UUID
    result: str
    score: float
    passed_rules: list[RuleReference]
    failed_rules: list[RuleReference]
    run_at: datetime
    is_override: bool
    previous_result: str | None
    override_reason: str | None
    overridden_by: str | None

    model_config = {"from_attributes": True}


class QualificationOverrideRequest(BaseModel):
    result: str = Field(pattern="^(qualified|not_qualified|needs_review)$")
    reason: str = Field(min_length=1)
    overridden_by: str | None = None


class ServiceCreate(BaseModel):
    name: str = Field(min_length=1)
    description: str | None = None
    category: str | None = None
    enabled: bool = True


class ServiceUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1)
    description: str | None = None
    category: str | None = None
    enabled: bool | None = None


class ServiceOut(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    category: str | None
    enabled: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AnalysisRuleCreate(BaseModel):
    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    enabled: bool = True


class AnalysisRuleUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1)
    description: str | None = Field(default=None, min_length=1)
    enabled: bool | None = None


class AnalysisRuleOut(BaseModel):
    id: uuid.UUID
    name: str
    description: str
    enabled: bool
    ai_suggested: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ServiceRecommendationOut(BaseModel):
    id: uuid.UUID
    lead_id: uuid.UUID
    analysis_id: uuid.UUID
    recommended_service_id: uuid.UUID
    recommended_service_name: str
    secondary_service_ids: list[str]
    reasoning: str
    human_decision: str | None
    decision_reason: str | None
    decided_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class LeadAnalysisOut(BaseModel):
    id: uuid.UUID
    lead_id: uuid.UUID
    summary: str
    opportunities: list[str]
    score: float
    confidence: float
    evidence: list[str]
    missing_information: list[str]
    next_action: str
    needs_review: bool
    created_at: datetime
    recommendation: ServiceRecommendationOut | None = None

    model_config = {"from_attributes": True}


class RecommendationDecisionRequest(BaseModel):
    decision: str = Field(pattern="^(approved|rejected)$")
    reason: str | None = None


class TemplateCreate(BaseModel):
    name: str = Field(min_length=1)
    subject: str = Field(min_length=1)
    body: str = Field(min_length=1)
    is_ai_generated: bool = False


class TemplateUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1)
    subject: str | None = Field(default=None, min_length=1)
    body: str | None = Field(default=None, min_length=1)


class TemplateOut(BaseModel):
    id: uuid.UUID
    name: str
    subject: str
    body: str
    is_ai_generated: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AIEmailDraftRequest(BaseModel):
    lead_id: uuid.UUID
    template_id: uuid.UUID | None = None


class AIEmailDraftResponse(BaseModel):
    subject: str
    body: str


class OutreachPreviewRequest(BaseModel):
    lead_id: uuid.UUID
    subject: str
    body: str


class OutreachPreviewResponse(BaseModel):
    to_email: str | None
    subject: str
    body: str


class OutreachSendRequest(BaseModel):
    lead_id: uuid.UUID
    subject: str
    body: str
    template_id: uuid.UUID | None = None
    is_test: bool = False
    test_email_override: str | None = None


class MessageOut(BaseModel):
    id: uuid.UUID
    lead_id: uuid.UUID
    template_id: uuid.UUID | None
    direction: str
    to_email: str | None
    from_email: str | None
    subject: str
    body: str
    status: str
    provider_response: str | None
    is_test: bool
    category: str | None
    classification_confidence: float | None
    classification_summary: str | None
    suggested_action: str | None
    review_required: bool
    sent_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class InboundMessageCreate(BaseModel):
    from_email: str = Field(min_length=1)
    subject: str = Field(min_length=1)
    body: str = Field(min_length=1)


class ReplyClassificationOut(BaseModel):
    category: str
    confidence: float
    summary: str
    suggested_action: str
    review_required: bool


CALL_OUTCOMES = [
    "no_answer",
    "connected",
    "interested",
    "follow_up",
    "meeting_booked",
    "not_interested",
    "wrong_number",
]


class CallCreate(BaseModel):
    lead_id: uuid.UUID
    reason_for_calling: str | None = None
    call_objective: str | None = None
    script: str | None = None
    notes: str | None = None
    outcome: str | None = Field(default=None, pattern="^(" + "|".join(CALL_OUTCOMES) + ")$")
    follow_up_date: datetime | None = None


class CallUpdate(BaseModel):
    reason_for_calling: str | None = None
    call_objective: str | None = None
    script: str | None = None
    notes: str | None = None
    outcome: str | None = Field(default=None, pattern="^(" + "|".join(CALL_OUTCOMES) + ")$")
    follow_up_date: datetime | None = None


class CallOut(BaseModel):
    id: uuid.UUID
    lead_id: uuid.UUID
    reason_for_calling: str | None
    call_objective: str | None
    script: str | None
    notes: str | None
    outcome: str | None
    follow_up_date: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CallScriptOut(BaseModel):
    opening: str
    reason_for_calling: str
    business_observation: str
    value_statement: str
    discovery_questions: list[str]
    objection_prompts: list[str]
    next_step: str
    full_text: str


class CallWorkspaceOut(BaseModel):
    lead: LeadOut
    latest_analysis: LeadAnalysisOut | None
    calls: list[CallOut]


class StageChangeRequest(BaseModel):
    new_stage: str = Field(min_length=1)
    reason: str | None = None


class TimelineEvent(BaseModel):
    type: str
    timestamp: datetime
    summary: str
    detail: dict | None = None


class TaskCreate(BaseModel):
    lead_id: uuid.UUID
    title: str = Field(min_length=1)
    owner: str | None = None
    due_date: datetime | None = None
    priority: str = Field(default="medium", pattern="^(low|medium|high)$")
    status: str = Field(default="pending", pattern="^(pending|in_progress|done)$")
    notes: str | None = None


class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1)
    owner: str | None = None
    due_date: datetime | None = None
    priority: str | None = Field(default=None, pattern="^(low|medium|high)$")
    status: str | None = Field(default=None, pattern="^(pending|in_progress|done)$")
    notes: str | None = None


class DashboardStatsOut(BaseModel):
    total_leads: int
    new_leads: int
    qualified: int
    needs_review: int
    contacted: int
    replies: int
    meetings: int
    won: int
    lost: int
    due_tasks: int
    active_automation_runs: int


class TaskOut(BaseModel):
    id: uuid.UUID
    lead_id: uuid.UUID
    title: str
    owner: str | None
    due_date: datetime | None
    priority: str
    status: str
    notes: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SettingsOut(BaseModel):
    google_places_api_key_set: bool
    openai_api_key_set: bool
    anthropic_api_key_set: bool
    gemini_api_key_set: bool
    smtp_host: str
    smtp_port: int
    smtp_user: str
    smtp_password_set: bool
    smtp_from_name: str
    imap_host: str
    imap_port: int


class EnrichEmailsResponse(BaseModel):
    checked: int
    found: int


class CampaignCreate(BaseModel):
    name: str = Field(min_length=1)
    template_id: uuid.UUID
    daily_limit: int | None = Field(default=None, ge=1)


class CampaignUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1)
    template_id: uuid.UUID | None = None
    daily_limit: int | None = Field(default=None, ge=1)


class CampaignOut(BaseModel):
    id: uuid.UUID
    name: str
    template_id: uuid.UUID | None
    daily_limit: int | None
    is_enabled: bool
    schedule: str | None
    last_run_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CampaignRunResult(BaseModel):
    campaign_id: uuid.UUID
    campaign_name: str
    sent_count: int
    skipped_count: int
    skipped_reasons: list[str]


class CampaignRunDueResponse(BaseModel):
    checked: int
    executed: list[CampaignRunResult]


class SettingsUpdate(BaseModel):
    google_places_api_key: str | None = None
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    gemini_api_key: str | None = None
    smtp_host: str | None = None
    smtp_port: int | None = None
    smtp_user: str | None = None
    smtp_password: str | None = None
    smtp_from_name: str | None = None
    imap_host: str | None = None
    imap_port: int | None = None

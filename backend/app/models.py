import uuid
from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


def _uuid() -> uuid.UUID:
    return uuid.uuid4()


class Lead(Base):
    __tablename__ = "leads"
    __table_args__ = (
        UniqueConstraint("source", "source_id", name="uq_leads_source_source_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)

    business_name: Mapped[str] = mapped_column(String(255))
    category: Mapped[str | None] = mapped_column(String(255), nullable=True)
    address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    city: Mapped[str | None] = mapped_column(String(255), nullable=True)
    country: Mapped[str | None] = mapped_column(String(255), nullable=True)
    latitude: Mapped[float | None] = mapped_column(Numeric(9, 6), nullable=True)
    longitude: Mapped[float | None] = mapped_column(Numeric(9, 6), nullable=True)

    contact_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    normalized_phone: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    website: Mapped[str | None] = mapped_column(String(500), nullable=True)
    normalized_website: Mapped[str | None] = mapped_column(String(500), nullable=True, index=True)
    social_links: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    source: Mapped[str] = mapped_column(String(100))
    source_id: Mapped[str] = mapped_column(String(255))
    source_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    rating: Mapped[float | None] = mapped_column(Numeric(3, 2), nullable=True)
    review_count: Mapped[int | None] = mapped_column(nullable=True)

    status: Mapped[str] = mapped_column(String(50), default="new", index=True)

    first_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    last_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )

    raw_records: Mapped[list["LeadSourceRecord"]] = relationship(
        back_populates="lead", cascade="all, delete-orphan"
    )


class LeadSourceRecord(Base):
    """Raw, untouched data as received from the source. Never overwritten by normalized/AI data."""

    __tablename__ = "lead_sources"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    lead_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("leads.id", ondelete="CASCADE"), index=True)

    source: Mapped[str] = mapped_column(String(100))
    source_id: Mapped[str] = mapped_column(String(255))
    raw_data: Mapped[dict] = mapped_column(JSON)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    lead: Mapped[Lead] = relationship(back_populates="raw_records")


class SearchConfiguration(Base):
    """A saved search the user can re-run on demand (Semi-Automatic) or schedule (Automatic)."""

    __tablename__ = "search_configurations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)

    name: Mapped[str] = mapped_column(String(255))
    business_type: Mapped[str] = mapped_column(String(255))
    location: Mapped[str] = mapped_column(String(255))
    city: Mapped[str | None] = mapped_column(String(255), nullable=True)
    country: Mapped[str | None] = mapped_column(String(255), nullable=True)
    latitude: Mapped[float | None] = mapped_column(Numeric(9, 6), nullable=True)
    longitude: Mapped[float | None] = mapped_column(Numeric(9, 6), nullable=True)
    radius_meters: Mapped[int | None] = mapped_column(nullable=True)
    keywords: Mapped[str | None] = mapped_column(String(500), nullable=True)
    source: Mapped[str] = mapped_column(String(100), default="google_places")
    max_results: Mapped[int] = mapped_column(default=20)

    # Reserved for Stage 1C (Fully Automatic) — not wired up yet.
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    schedule: Mapped[str | None] = mapped_column(String(50), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )

    runs: Mapped[list["LeadSearchRun"]] = relationship(back_populates="search_configuration")

    def to_search_params(self) -> dict:
        return {
            "business_type": self.business_type,
            "location": self.location,
            "city": self.city,
            "country": self.country,
            "latitude": float(self.latitude) if self.latitude is not None else None,
            "longitude": float(self.longitude) if self.longitude is not None else None,
            "radius_meters": self.radius_meters,
            "keywords": self.keywords,
            "source": self.source,
            "max_results": self.max_results,
        }


class QualificationRule(Base):
    """Admin-defined rule used to decide whether a lead should move to AI analysis."""

    __tablename__ = "qualification_rules"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)

    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    field: Mapped[str] = mapped_column(String(100))
    operator: Mapped[str] = mapped_column(String(50))
    expected_value: Mapped[str | None] = mapped_column(String(500), nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    priority: Mapped[int] = mapped_column(default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )


class LeadQualification(Base):
    """Result of running the qualification rule engine against a lead."""

    __tablename__ = "lead_qualification"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    lead_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("leads.id", ondelete="CASCADE"), index=True)

    result: Mapped[str] = mapped_column(String(20))  # qualified | not_qualified | needs_review
    score: Mapped[float] = mapped_column(Numeric(5, 2))
    passed_rules: Mapped[list] = mapped_column(JSON)
    failed_rules: Mapped[list] = mapped_column(JSON)
    run_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    is_override: Mapped[bool] = mapped_column(Boolean, default=False)
    previous_result: Mapped[str | None] = mapped_column(String(20), nullable=True)
    override_reason: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    overridden_by: Mapped[str | None] = mapped_column(String(255), nullable=True)

    lead: Mapped[Lead] = relationship()


class Service(Base):
    """Admin-managed service catalog. AI may only recommend enabled services from here."""

    __tablename__ = "services"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)

    name: Mapped[str] = mapped_column(String(255), unique=True)
    description: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    category: Mapped[str | None] = mapped_column(String(255), nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )


class AnalysisRule(Base):
    """Admin-defined guidance fed to the AI when analyzing a lead (not a deterministic check)."""

    __tablename__ = "analysis_rules"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)

    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(String(2000))
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    ai_suggested: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )


class LeadAnalysis(Base):
    """AI's understanding of the business and the opportunity it represents."""

    __tablename__ = "lead_analysis"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    lead_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("leads.id", ondelete="CASCADE"), index=True)

    summary: Mapped[str] = mapped_column(String(4000))
    opportunities: Mapped[list] = mapped_column(JSON)
    score: Mapped[float] = mapped_column(Numeric(5, 2))
    confidence: Mapped[float] = mapped_column(Numeric(3, 2))
    evidence: Mapped[list] = mapped_column(JSON)
    missing_information: Mapped[list] = mapped_column(JSON)
    next_action: Mapped[str] = mapped_column(String(1000))
    needs_review: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    lead: Mapped[Lead] = relationship()
    recommendation: Mapped["ServiceRecommendation | None"] = relationship(
        back_populates="analysis", uselist=False
    )


class ServiceRecommendation(Base):
    """AI's recommended service for a lead, with the human decision tracked for accuracy measurement."""

    __tablename__ = "service_recommendations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    lead_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("leads.id", ondelete="CASCADE"), index=True)
    analysis_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("lead_analysis.id", ondelete="CASCADE")
    )

    recommended_service_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("services.id"))
    secondary_service_ids: Mapped[list] = mapped_column(JSON, default=list)
    reasoning: Mapped[str] = mapped_column(String(2000))

    human_decision: Mapped[str | None] = mapped_column(String(20), nullable=True)  # approved | rejected
    decision_reason: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    lead: Mapped[Lead] = relationship()
    analysis: Mapped[LeadAnalysis] = relationship(back_populates="recommendation")
    recommended_service: Mapped[Service] = relationship()


class Template(Base):
    """A reusable email template — created by a user or generated by AI."""

    __tablename__ = "templates"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)

    name: Mapped[str] = mapped_column(String(255))
    subject: Mapped[str] = mapped_column(String(500))
    body: Mapped[str] = mapped_column(String(8000))
    is_ai_generated: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )


class SuppressedEmail(Base):
    """Emails that must never receive outreach again (opted out, bounced, etc.)."""

    __tablename__ = "suppressed_emails"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    reason: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class Campaign(Base):
    """Outreach campaign settings. Automatic sending is a later stage — reserved here, not wired yet."""

    __tablename__ = "campaigns"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)

    name: Mapped[str] = mapped_column(String(255))
    template_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("templates.id", ondelete="SET NULL"), nullable=True
    )
    daily_limit: Mapped[int | None] = mapped_column(nullable=True)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )


class Message(Base):
    """A sent (or attempted) outreach message. The message log."""

    __tablename__ = "messages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    lead_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("leads.id", ondelete="CASCADE"), index=True)
    template_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("templates.id", ondelete="SET NULL"), nullable=True
    )
    campaign_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("campaigns.id", ondelete="SET NULL"), nullable=True
    )

    direction: Mapped[str] = mapped_column(String(10), default="outbound")  # outbound | inbound
    to_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    from_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    subject: Mapped[str] = mapped_column(String(500))
    body: Mapped[str] = mapped_column(String(8000))

    status: Mapped[str] = mapped_column(String(20), default="draft")
    # outbound: draft | sending | accepted_by_provider | failed | bounced
    # inbound: received
    provider_response: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    is_test: Mapped[bool] = mapped_column(Boolean, default=False)

    # Reply classification (inbound only) — per Module 5 AI output spec.
    category: Mapped[str | None] = mapped_column(String(30), nullable=True)
    classification_confidence: Mapped[float | None] = mapped_column(Numeric(3, 2), nullable=True)
    classification_summary: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    suggested_action: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    review_required: Mapped[bool] = mapped_column(Boolean, default=False)

    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    lead: Mapped[Lead] = relationship()


class AuditLog(Base):
    """Record of important actions across the system, per the security/compliance spec."""

    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)

    action: Mapped[str] = mapped_column(String(100))
    entity_type: Mapped[str] = mapped_column(String(100))
    entity_id: Mapped[str] = mapped_column(String(255))
    detail: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class Call(Base):
    """A manual call record. The user places the call themselves — this only tracks it."""

    __tablename__ = "calls"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    lead_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("leads.id", ondelete="CASCADE"), index=True)

    reason_for_calling: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    call_objective: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    script: Mapped[str | None] = mapped_column(String(4000), nullable=True)
    notes: Mapped[str | None] = mapped_column(String(4000), nullable=True)
    outcome: Mapped[str | None] = mapped_column(String(30), nullable=True)
    follow_up_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )

    lead: Mapped[Lead] = relationship()


class Task(Base):
    """A follow-up or sales task tied to a lead."""

    __tablename__ = "tasks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    lead_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("leads.id", ondelete="CASCADE"), index=True)

    title: Mapped[str] = mapped_column(String(500))
    owner: Mapped[str | None] = mapped_column(String(255), nullable=True)
    due_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    priority: Mapped[str] = mapped_column(String(20), default="medium")  # low | medium | high
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True)  # pending | in_progress | done
    notes: Mapped[str | None] = mapped_column(String(2000), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )

    lead: Mapped[Lead] = relationship()


class CRMStageHistory(Base):
    """Every pipeline stage transition for a lead, per the CRM/Timeline spec."""

    __tablename__ = "crm_stage_history"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    lead_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("leads.id", ondelete="CASCADE"), index=True)

    old_stage: Mapped[str | None] = mapped_column(String(50), nullable=True)
    new_stage: Mapped[str] = mapped_column(String(50))
    reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    lead: Mapped[Lead] = relationship()


class LeadSearchRun(Base):
    """One execution of a lead search — manual, semi-automatic, or automatic."""

    __tablename__ = "lead_search_runs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)

    mode: Mapped[str] = mapped_column(String(20))  # manual | semi_auto | auto
    search_configuration_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("search_configurations.id", ondelete="SET NULL"), nullable=True
    )
    search_config: Mapped[dict] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(20), default="queued")  # queued|running|completed|failed

    new_leads_count: Mapped[int] = mapped_column(default=0)
    duplicate_count: Mapped[int] = mapped_column(default=0)
    failed_count: Mapped[int] = mapped_column(default=0)
    error_message: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    search_configuration: Mapped[SearchConfiguration | None] = relationship(back_populates="runs")

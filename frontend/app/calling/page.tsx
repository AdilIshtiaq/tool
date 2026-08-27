"use client";

import { useCallback, useEffect, useState } from "react";
import { AppHeader } from "@/components/layout/app-header";
import { PageContainer } from "@/components/layout/page-container";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { SectionIcon } from "@/components/ui/section-icon";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Spinner } from "@/components/ui/spinner";
import { Separator } from "@/components/ui/separator";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  createCall,
  generateCallScript,
  getCallWorkspace,
  getLeads,
  updateCall,
  type Call,
  type CallWorkspace,
  type Lead,
} from "@/lib/api";
import { LeadStatusBadge } from "@/components/lead-status-badge";
import {
  AlertCircle,
  Building2,
  History,
  Mail,
  MapPin,
  NotebookPen,
  Phone,
  Sparkles,
  User,
  Globe,
} from "lucide-react";

const OUTCOME_OPTIONS = [
  { value: "no_answer", label: "No answer" },
  { value: "connected", label: "Connected" },
  { value: "interested", label: "Interested" },
  { value: "follow_up", label: "Follow-up" },
  { value: "meeting_booked", label: "Meeting booked" },
  { value: "not_interested", label: "Not interested" },
  { value: "wrong_number", label: "Wrong number" },
];
const OUTCOME_LABELS: Record<string, string> = Object.fromEntries(
  OUTCOME_OPTIONS.map((o) => [o.value, o.label])
);

function InfoRow({
  icon: Icon,
  label,
  value,
}: {
  icon: typeof Phone;
  label: string;
  value: string | null;
}) {
  return (
    <div className="flex items-start gap-2 text-sm">
      <Icon className="mt-0.5 size-4 shrink-0 text-muted-foreground" />
      <div>
        <span className="text-muted-foreground">{label}: </span>
        {value ?? <span className="text-muted-foreground">—</span>}
      </div>
    </div>
  );
}

export default function CallingWorkspacePage() {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [selectedLeadId, setSelectedLeadId] = useState("");
  const [workspace, setWorkspace] = useState<CallWorkspace | null>(null);
  const [loading, setLoading] = useState(false);

  const [reason, setReason] = useState("");
  const [objective, setObjective] = useState("");
  const [script, setScript] = useState("");
  const [notes, setNotes] = useState("");
  const [outcome, setOutcome] = useState("");
  const [followUpDate, setFollowUpDate] = useState("");

  const [generating, setGenerating] = useState(false);
  const [saving, setSaving] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);

  useEffect(() => {
    getLeads({ page: 1, page_size: 100 }).then((res) => setLeads(res.items));
  }, []);

  const loadWorkspace = useCallback(async (leadId: string) => {
    if (!leadId) {
      setWorkspace(null);
      return;
    }
    setLoading(true);
    try {
      setWorkspace(await getCallWorkspace(leadId));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadWorkspace(selectedLeadId);
    setReason("");
    setObjective("");
    setScript("");
    setNotes("");
    setOutcome("");
    setFollowUpDate("");
    setActionError(null);
  }, [selectedLeadId, loadWorkspace]);

  async function handleGenerateScript() {
    if (!selectedLeadId) return;
    setGenerating(true);
    setActionError(null);
    try {
      const result = await generateCallScript(selectedLeadId);
      setScript(result.full_text);
      if (!reason) setReason(result.reason_for_calling);
    } catch (error) {
      setActionError((error as Error).message);
    } finally {
      setGenerating(false);
    }
  }

  async function handleSaveCall() {
    if (!selectedLeadId) return;
    setSaving(true);
    setActionError(null);
    try {
      await createCall({
        lead_id: selectedLeadId,
        reason_for_calling: reason || undefined,
        call_objective: objective || undefined,
        script: script || undefined,
        notes: notes || undefined,
        outcome: outcome || undefined,
      });
      await loadWorkspace(selectedLeadId);
      setNotes("");
      setOutcome("");
    } catch (error) {
      setActionError((error as Error).message);
    } finally {
      setSaving(false);
    }
  }

  async function handleUpdateOutcome(call: Call, newOutcome: string) {
    try {
      await updateCall(call.id, { outcome: newOutcome });
      await loadWorkspace(selectedLeadId);
    } catch (error) {
      setActionError((error as Error).message);
    }
  }

  const lead = workspace?.lead;
  const analysis = workspace?.latest_analysis;
  const recommendation = analysis?.recommendation;

  return (
    <>
      <AppHeader
        title="Calling Workspace"
        description="Everything needed for a manual call"
      />
      <PageContainer>
        <Card>
          <CardContent className="pt-6">
            <div className="space-y-1.5">
              <Label>Lead</Label>
              <Select value={selectedLeadId} onValueChange={(v) => setSelectedLeadId(v ?? "")}>
                <SelectTrigger className="w-full sm:w-[320px]">
                  <SelectValue placeholder="Choose a lead to call">
                    {(value: string) =>
                      leads.find((l) => l.id === value)?.business_name ??
                      "Choose a lead to call"
                    }
                  </SelectValue>
                </SelectTrigger>
                <SelectContent>
                  {leads.map((l) => (
                    <SelectItem key={l.id} value={l.id}>
                      {l.business_name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <p className="text-sm text-muted-foreground">
                Everything you need for the call — contact details, AI
                intelligence, and a script — appears once you pick a lead.
              </p>
            </div>
          </CardContent>
        </Card>

        {loading ? (
          <div className="flex justify-center py-10">
            <Spinner className="size-5" />
          </div>
        ) : lead ? (
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
            <Card>
              <CardHeader className="flex-row items-center gap-3 space-y-0">
                <SectionIcon icon={Building2} color="indigo" />
                <div className="flex items-center gap-2">
                  <CardTitle className="text-base font-semibold">
                    {lead.business_name}
                  </CardTitle>
                  <LeadStatusBadge status={lead.status} />
                </div>
              </CardHeader>
              <CardContent className="space-y-2">
                <InfoRow icon={User} label="Contact" value={lead.contact_name} />
                <InfoRow icon={Phone} label="Phone" value={lead.phone} />
                <InfoRow
                  icon={MapPin}
                  label="Address"
                  value={[lead.address, lead.city, lead.country]
                    .filter(Boolean)
                    .join(", ") || null}
                />
                <InfoRow icon={Globe} label="Website" value={lead.website} />
                <InfoRow icon={Mail} label="Email" value={lead.email} />
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex-row items-center gap-3 space-y-0">
                <SectionIcon icon={Sparkles} color="violet" />
                <div>
                  <CardTitle className="text-base font-semibold">
                    Intelligence
                  </CardTitle>
                  <p className="text-sm text-muted-foreground">
                    What the AI knows about this business.
                  </p>
                </div>
              </CardHeader>
              <CardContent className="space-y-2 text-sm">
                {analysis ? (
                  <>
                    <p>{analysis.summary}</p>
                    <div className="flex gap-2">
                      <Badge variant="outline">Score: {analysis.score}</Badge>
                      <Badge variant="outline">
                        Confidence: {Math.round(analysis.confidence * 100)}%
                      </Badge>
                    </div>
                    {recommendation ? (
                      <>
                        <Separator />
                        <p className="font-medium">
                          Recommended: {recommendation.recommended_service_name}
                        </p>
                        <p className="text-muted-foreground">
                          {recommendation.reasoning}
                        </p>
                      </>
                    ) : null}
                  </>
                ) : (
                  <p className="text-muted-foreground">
                    No AI analysis yet for this lead. Run it from the AI
                    Analysis page for richer intelligence here.
                  </p>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex-row items-center gap-3 space-y-0">
                <SectionIcon icon={History} color="slate" />
                <div>
                  <CardTitle className="text-base font-semibold">
                    Call History
                  </CardTitle>
                  <p className="text-sm text-muted-foreground">
                    Every past call and its outcome, most recent first.
                  </p>
                </div>
              </CardHeader>
              <CardContent className="space-y-2">
                {workspace && workspace.calls.length === 0 ? (
                  <p className="text-sm text-muted-foreground">
                    No calls logged yet.
                  </p>
                ) : (
                  workspace?.calls.map((call) => (
                    <div key={call.id} className="rounded-md border p-2 text-sm">
                      <div className="flex items-center justify-between gap-2">
                        <span className="text-xs text-muted-foreground">
                          {new Date(call.created_at).toLocaleString()}
                        </span>
                        {call.outcome ? (
                          <Badge variant="secondary">
                            {OUTCOME_LABELS[call.outcome] ?? call.outcome}
                          </Badge>
                        ) : (
                          <Select
                            onValueChange={(v) =>
                              typeof v === "string" && handleUpdateOutcome(call, v)
                            }
                          >
                            <SelectTrigger size="sm" className="w-[140px]">
                              <SelectValue placeholder="Set outcome" />
                            </SelectTrigger>
                            <SelectContent>
                              {OUTCOME_OPTIONS.map((o) => (
                                <SelectItem key={o.value} value={o.value}>
                                  {o.label}
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        )}
                      </div>
                      {call.notes ? (
                        <p className="mt-1 text-muted-foreground">{call.notes}</p>
                      ) : null}
                    </div>
                  ))
                )}
              </CardContent>
            </Card>
          </div>
        ) : null}

        {lead ? (
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0">
              <div className="flex items-center gap-3">
                <SectionIcon icon={NotebookPen} color="amber" />
                <div>
                  <CardTitle className="text-base font-semibold">
                    Call Script &amp; Notes
                  </CardTitle>
                  <p className="text-sm text-muted-foreground">
                    Fully editable — use the AI draft as a starting point, not a
                    script to read verbatim.
                  </p>
                </div>
              </div>
              <Button
                size="sm"
                variant="outline"
                disabled={generating}
                onClick={handleGenerateScript}
                className="gap-2"
              >
                {generating ? (
                  <Spinner className="size-4" />
                ) : (
                  <Sparkles className="size-4" />
                )}
                Generate Script with AI
              </Button>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <div className="space-y-1.5">
                  <Label htmlFor="reason">Reason for calling</Label>
                  <Input
                    id="reason"
                    value={reason}
                    onChange={(e) => setReason(e.target.value)}
                  />
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="objective">Call objective</Label>
                  <Input
                    id="objective"
                    value={objective}
                    onChange={(e) => setObjective(e.target.value)}
                  />
                </div>
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="script">Script (editable)</Label>
                <Textarea
                  id="script"
                  rows={10}
                  value={script}
                  onChange={(e) => setScript(e.target.value)}
                />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="notes">Notes</Label>
                <Textarea
                  id="notes"
                  rows={4}
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                />
              </div>
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <div className="space-y-1.5">
                  <Label>Outcome</Label>
                  <Select value={outcome} onValueChange={(v) => setOutcome(v ?? "")}>
                    <SelectTrigger className="w-full">
                      <SelectValue placeholder="Select outcome">
                        {(value: string) => OUTCOME_LABELS[value] ?? "Select outcome"}
                      </SelectValue>
                    </SelectTrigger>
                    <SelectContent>
                      {OUTCOME_OPTIONS.map((o) => (
                        <SelectItem key={o.value} value={o.value}>
                          {o.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="follow-up">Follow-up date</Label>
                  <Input
                    id="follow-up"
                    type="date"
                    value={followUpDate}
                    onChange={(e) => setFollowUpDate(e.target.value)}
                  />
                </div>
              </div>

              {actionError ? (
                <Alert variant="destructive">
                  <AlertCircle className="size-4" />
                  <AlertTitle>Action failed</AlertTitle>
                  <AlertDescription>{actionError}</AlertDescription>
                </Alert>
              ) : null}

              <Button disabled={saving} onClick={handleSaveCall} className="gap-2">
                {saving ? <Spinner className="size-4" /> : null}
                Save Call
              </Button>
            </CardContent>
          </Card>
        ) : null}
      </PageContainer>
    </>
  );
}

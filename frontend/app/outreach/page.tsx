"use client";

import { useCallback, useEffect, useState } from "react";
import { AppHeader } from "@/components/layout/app-header";
import { PageContainer } from "@/components/layout/page-container";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Spinner } from "@/components/ui/spinner";
import { Separator } from "@/components/ui/separator";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  createCampaign,
  createTemplate,
  disableCampaign,
  enableCampaign,
  generateAIDraft,
  getCampaigns,
  getLeadMessages,
  getLeads,
  getTemplates,
  previewOutreach,
  runCampaignNow,
  sendOutreach,
  updateLead,
  type Campaign,
  type CampaignRunResult,
  type Lead,
  type Message,
  type Template,
} from "@/lib/api";
import { humanize } from "@/lib/lead-status";
import {
  AlertCircle,
  CheckCircle2,
  Eye,
  Mail,
  Megaphone,
  Pause,
  Play,
  Plus,
  Send,
  Sparkles,
  TestTube,
  XCircle,
  Zap,
} from "lucide-react";

const SCHEDULE_OPTIONS = [
  { value: "hourly", label: "Every hour" },
  { value: "every_2_hours", label: "Every 2 hours" },
  { value: "every_6_hours", label: "Every 6 hours" },
  { value: "daily", label: "Daily" },
];

const SCHEDULE_LABELS: Record<string, string> = Object.fromEntries(
  SCHEDULE_OPTIONS.map((o) => [o.value, o.label])
);

export default function OutreachPage() {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [templates, setTemplates] = useState<Template[]>([]);
  const [loadingMeta, setLoadingMeta] = useState(true);

  const [selectedLeadId, setSelectedLeadId] = useState("");
  const [selectedTemplateId, setSelectedTemplateId] = useState("");
  const [emailDraft, setEmailDraft] = useState("");
  const [savingEmail, setSavingEmail] = useState(false);

  const [subject, setSubject] = useState("");
  const [body, setBody] = useState("");
  const [preview, setPreview] = useState<{ to_email: string | null; subject: string; body: string } | null>(
    null
  );
  const [previewing, setPreviewing] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);

  const [testEmail, setTestEmail] = useState("");
  const [testDialogOpen, setTestDialogOpen] = useState(false);
  const [sendingTest, setSendingTest] = useState(false);
  const [sendingReal, setSendingReal] = useState(false);
  const [lastMessage, setLastMessage] = useState<Message | null>(null);

  const [templateDialogOpen, setTemplateDialogOpen] = useState(false);
  const [newTemplateName, setNewTemplateName] = useState("");
  const [savingTemplate, setSavingTemplate] = useState(false);

  const [messages, setMessages] = useState<Message[]>([]);
  const [loadingMessages, setLoadingMessages] = useState(false);

  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [campaignDialogOpen, setCampaignDialogOpen] = useState(false);
  const [newCampaignName, setNewCampaignName] = useState("");
  const [newCampaignTemplateId, setNewCampaignTemplateId] = useState("");
  const [newCampaignDailyLimit, setNewCampaignDailyLimit] = useState("");
  const [savingCampaign, setSavingCampaign] = useState(false);
  const [campaignBusyId, setCampaignBusyId] = useState<string | null>(null);
  const [campaignScheduleChoice, setCampaignScheduleChoice] = useState<Record<string, string>>({});
  const [campaignResults, setCampaignResults] = useState<Record<string, CampaignRunResult>>({});
  const [campaignError, setCampaignError] = useState<string | null>(null);

  const loadMeta = useCallback(async () => {
    setLoadingMeta(true);
    try {
      const [leadRes, templateRes, campaignRes] = await Promise.all([
        getLeads({ page: 1, page_size: 100 }),
        getTemplates(),
        getCampaigns(),
      ]);
      setLeads(leadRes.items);
      setTemplates(templateRes);
      setCampaigns(campaignRes);
    } finally {
      setLoadingMeta(false);
    }
  }, []);

  useEffect(() => {
    loadMeta();
  }, [loadMeta]);

  const loadMessages = useCallback(async (leadId: string) => {
    if (!leadId) {
      setMessages([]);
      return;
    }
    setLoadingMessages(true);
    try {
      setMessages(await getLeadMessages(leadId));
    } finally {
      setLoadingMessages(false);
    }
  }, []);

  useEffect(() => {
    const lead = leads.find((l) => l.id === selectedLeadId);
    setEmailDraft(lead?.email ?? "");
    setPreview(null);
    setLastMessage(null);
    loadMessages(selectedLeadId);
  }, [selectedLeadId, leads, loadMessages]);

  function applyTemplate(templateId: string) {
    setSelectedTemplateId(templateId);
    const template = templates.find((t) => t.id === templateId);
    if (template) {
      setSubject(template.subject);
      setBody(template.body);
    }
  }

  async function handleSaveEmail() {
    if (!selectedLeadId) return;
    setSavingEmail(true);
    try {
      const updated = await updateLead(selectedLeadId, {
        email: emailDraft.trim() || null,
      });
      setLeads((ls) => ls.map((l) => (l.id === updated.id ? updated : l)));
    } finally {
      setSavingEmail(false);
    }
  }

  async function handleGenerateAI() {
    if (!selectedLeadId) return;
    setGenerating(true);
    setActionError(null);
    try {
      const draft = await generateAIDraft(selectedLeadId);
      setSubject(draft.subject);
      setBody(draft.body);
    } catch (error) {
      setActionError((error as Error).message);
    } finally {
      setGenerating(false);
    }
  }

  async function handlePreview() {
    if (!selectedLeadId || !subject.trim() || !body.trim()) return;
    setPreviewing(true);
    setActionError(null);
    try {
      setPreview(await previewOutreach(selectedLeadId, subject, body));
    } catch (error) {
      setActionError((error as Error).message);
    } finally {
      setPreviewing(false);
    }
  }

  async function handleSendTest() {
    if (!selectedLeadId || !testEmail.trim()) return;
    setSendingTest(true);
    setActionError(null);
    try {
      const message = await sendOutreach({
        lead_id: selectedLeadId,
        subject,
        body,
        is_test: true,
        test_email_override: testEmail.trim(),
      });
      setLastMessage(message);
      setTestDialogOpen(false);
      await loadMessages(selectedLeadId);
    } catch (error) {
      setActionError((error as Error).message);
    } finally {
      setSendingTest(false);
    }
  }

  async function handleSend() {
    if (!selectedLeadId) return;
    setSendingReal(true);
    setActionError(null);
    try {
      const message = await sendOutreach({
        lead_id: selectedLeadId,
        subject,
        body,
      });
      setLastMessage(message);
      await loadMessages(selectedLeadId);
    } catch (error) {
      setActionError((error as Error).message);
    } finally {
      setSendingReal(false);
    }
  }

  async function handleSaveTemplate() {
    if (!newTemplateName.trim() || !subject.trim() || !body.trim()) return;
    setSavingTemplate(true);
    try {
      const template = await createTemplate({
        name: newTemplateName.trim(),
        subject,
        body,
      });
      setTemplates((t) => [template, ...t]);
      setTemplateDialogOpen(false);
      setNewTemplateName("");
    } finally {
      setSavingTemplate(false);
    }
  }

  async function handleCreateCampaign() {
    if (!newCampaignName.trim() || !newCampaignTemplateId) return;
    setSavingCampaign(true);
    setCampaignError(null);
    try {
      const campaign = await createCampaign({
        name: newCampaignName.trim(),
        template_id: newCampaignTemplateId,
        daily_limit: newCampaignDailyLimit ? Number(newCampaignDailyLimit) : undefined,
      });
      setCampaigns((c) => [campaign, ...c]);
      setCampaignDialogOpen(false);
      setNewCampaignName("");
      setNewCampaignTemplateId("");
      setNewCampaignDailyLimit("");
    } catch (error) {
      setCampaignError((error as Error).message);
    } finally {
      setSavingCampaign(false);
    }
  }

  async function handleRunCampaign(campaignId: string) {
    setCampaignBusyId(campaignId);
    setCampaignError(null);
    try {
      const result = await runCampaignNow(campaignId);
      setCampaignResults((r) => ({ ...r, [campaignId]: result }));
      const updated = await getCampaigns();
      setCampaigns(updated);
    } catch (error) {
      setCampaignError((error as Error).message);
    } finally {
      setCampaignBusyId(null);
    }
  }

  async function handleEnableCampaign(campaignId: string) {
    const schedule = campaignScheduleChoice[campaignId] ?? "hourly";
    setCampaignBusyId(campaignId);
    setCampaignError(null);
    try {
      const updated = await enableCampaign(campaignId, schedule);
      setCampaigns((cs) => cs.map((c) => (c.id === updated.id ? updated : c)));
    } catch (error) {
      setCampaignError((error as Error).message);
    } finally {
      setCampaignBusyId(null);
    }
  }

  async function handleDisableCampaign(campaignId: string) {
    setCampaignBusyId(campaignId);
    setCampaignError(null);
    try {
      const updated = await disableCampaign(campaignId);
      setCampaigns((cs) => cs.map((c) => (c.id === updated.id ? updated : c)));
    } catch (error) {
      setCampaignError((error as Error).message);
    } finally {
      setCampaignBusyId(null);
    }
  }

  const selectedLead = leads.find((l) => l.id === selectedLeadId);
  const canCompose = Boolean(selectedLeadId);

  return (
    <>
      <AppHeader
        title="Outreach"
        description="Email outreach campaigns and templates"
      />
      <PageContainer>
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium">Compose</CardTitle>
            <p className="text-sm text-muted-foreground">
              Write an email yourself, start from a template, or generate a
              draft with AI — then preview and approve before sending.
            </p>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div className="space-y-1.5">
                <Label>Lead</Label>
                <Select value={selectedLeadId} onValueChange={(v) => setSelectedLeadId(v ?? "")}>
                  <SelectTrigger className="w-full">
                    <SelectValue placeholder="Choose a lead">
                      {(value: string) =>
                        leads.find((l) => l.id === value)?.business_name ??
                        "Choose a lead"
                      }
                    </SelectValue>
                  </SelectTrigger>
                  <SelectContent>
                    {leads.map((lead) => (
                      <SelectItem key={lead.id} value={lead.id}>
                        {lead.business_name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-1.5">
                <Label>Start from template</Label>
                <Select
                  value={selectedTemplateId}
                  onValueChange={(v) => v && applyTemplate(v)}
                  disabled={!canCompose}
                >
                  <SelectTrigger className="w-full">
                    <SelectValue placeholder="Optional">
                      {(value: string) =>
                        templates.find((t) => t.id === value)?.name ?? "Optional"
                      }
                    </SelectValue>
                  </SelectTrigger>
                  <SelectContent>
                    {templates.map((t) => (
                      <SelectItem key={t.id} value={t.id}>
                        {t.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            {selectedLead ? (
              <div className="flex items-end gap-2 rounded-lg border p-3">
                <div className="flex-1 space-y-1.5">
                  <Label htmlFor="lead-email">
                    Email for {selectedLead.business_name}
                  </Label>
                  <Input
                    id="lead-email"
                    placeholder="No email on file — add one to enable outreach"
                    value={emailDraft}
                    onChange={(e) => setEmailDraft(e.target.value)}
                  />
                </div>
                <Button
                  variant="outline"
                  disabled={savingEmail}
                  onClick={handleSaveEmail}
                  className="gap-2"
                >
                  {savingEmail ? <Spinner className="size-4" /> : null}
                  Save
                </Button>
              </div>
            ) : null}

            <div className="space-y-1.5">
              <Label htmlFor="subject">Subject</Label>
              <Input
                id="subject"
                value={subject}
                onChange={(e) => setSubject(e.target.value)}
                disabled={!canCompose}
                placeholder="Use {{business_name}}, {{recommended_service}}, {{city}}, {{country}}, {{website}}, {{category}}"
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="body">Body</Label>
              <Textarea
                id="body"
                rows={8}
                value={body}
                onChange={(e) => setBody(e.target.value)}
                disabled={!canCompose}
              />
            </div>

            <div className="flex flex-wrap gap-2">
              <Button
                variant="outline"
                disabled={!canCompose || generating}
                onClick={handleGenerateAI}
                className="gap-2"
              >
                {generating ? <Spinner className="size-4" /> : <Sparkles className="size-4" />}
                Generate with AI
              </Button>
              <Button
                variant="outline"
                disabled={!canCompose || !subject.trim() || !body.trim() || previewing}
                onClick={handlePreview}
                className="gap-2"
              >
                {previewing ? <Spinner className="size-4" /> : <Eye className="size-4" />}
                Preview
              </Button>
              <Button
                variant="outline"
                disabled={!canCompose || !subject.trim() || !body.trim()}
                onClick={() => setTemplateDialogOpen(true)}
                className="gap-2"
              >
                <Plus className="size-4" />
                Save as Template
              </Button>
              <Button
                variant="outline"
                disabled={!canCompose || !subject.trim() || !body.trim()}
                onClick={() => setTestDialogOpen(true)}
                className="gap-2"
              >
                <TestTube className="size-4" />
                Send Test
              </Button>
              <Button
                disabled={!canCompose || !subject.trim() || !body.trim() || sendingReal}
                onClick={handleSend}
                className="gap-2"
              >
                {sendingReal ? <Spinner className="size-4" /> : <Send className="size-4" />}
                Send
              </Button>
            </div>

            {actionError ? (
              <Alert variant="destructive">
                <AlertCircle className="size-4" />
                <AlertTitle>Action failed</AlertTitle>
                <AlertDescription>{actionError}</AlertDescription>
              </Alert>
            ) : null}

            {preview ? (
              <div className="rounded-lg border bg-muted/40 p-3">
                <p className="text-xs font-medium text-muted-foreground">
                  Preview — to: {preview.to_email ?? "no email on file"}
                </p>
                <p className="mt-1 font-medium">{preview.subject}</p>
                <p className="mt-1 whitespace-pre-wrap text-sm">{preview.body}</p>
              </div>
            ) : null}

            {lastMessage ? (
              <Alert
                variant={
                  lastMessage.status === "accepted_by_provider" ? "default" : "destructive"
                }
              >
                {lastMessage.status === "accepted_by_provider" ? (
                  <CheckCircle2 className="size-4" />
                ) : (
                  <XCircle className="size-4" />
                )}
                <AlertTitle>
                  {lastMessage.is_test ? "Test send" : "Send"} —{" "}
                  {humanize(lastMessage.status)}
                </AlertTitle>
                <AlertDescription>
                  {lastMessage.provider_response ?? "No provider response recorded."}
                </AlertDescription>
              </Alert>
            ) : null}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium">
              Templates {templates.length > 0 ? `(${templates.length})` : ""}
            </CardTitle>
            <p className="text-sm text-muted-foreground">
              Reusable email templates, ready to personalize for any lead.
            </p>
          </CardHeader>
          <CardContent>
            {loadingMeta ? (
              <div className="flex justify-center py-6">
                <Spinner className="size-5" />
              </div>
            ) : templates.length === 0 ? (
              <p className="py-6 text-center text-sm text-muted-foreground">
                No templates yet. Compose an email above and click "Save as
                Template" to reuse it later.
              </p>
            ) : (
              <div className="space-y-2">
                {templates.map((t) => (
                  <div key={t.id} className="rounded-lg border p-3">
                    <div className="flex items-center gap-2">
                      <p className="font-medium">{t.name}</p>
                      {t.is_ai_generated ? (
                        <Badge variant="secondary">AI-generated</Badge>
                      ) : null}
                    </div>
                    <p className="text-sm text-muted-foreground">{t.subject}</p>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0">
            <div>
              <CardTitle className="text-sm font-medium flex items-center gap-2">
                <Megaphone className="size-4 text-muted-foreground" />
                Campaigns {campaigns.length > 0 ? `(${campaigns.length})` : ""}
              </CardTitle>
              <p className="text-sm text-muted-foreground">
                Automatically email every approved lead using a template — on
                demand, or on a schedule. Runs only while this app is running.
              </p>
            </div>
            <Button
              size="sm"
              variant="outline"
              onClick={() => setCampaignDialogOpen(true)}
              className="gap-2"
              disabled={templates.length === 0}
            >
              <Plus className="size-4" />
              New Campaign
            </Button>
          </CardHeader>
          <CardContent className="space-y-3">
            {campaignError ? (
              <Alert variant="destructive">
                <AlertCircle className="size-4" />
                <AlertTitle>Action failed</AlertTitle>
                <AlertDescription>{campaignError}</AlertDescription>
              </Alert>
            ) : null}
            {templates.length === 0 ? (
              <p className="py-6 text-center text-sm text-muted-foreground">
                Save a template first — campaigns send an existing template to
                approved leads automatically.
              </p>
            ) : campaigns.length === 0 ? (
              <p className="py-6 text-center text-sm text-muted-foreground">
                No campaigns yet. Create one to start auto-sending to approved leads.
              </p>
            ) : (
              campaigns.map((campaign) => {
                const template = templates.find((t) => t.id === campaign.template_id);
                const result = campaignResults[campaign.id];
                const busy = campaignBusyId === campaign.id;
                return (
                  <div key={campaign.id} className="rounded-lg border p-3 space-y-2">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <div>
                        <div className="flex items-center gap-2">
                          <p className="font-medium">{campaign.name}</p>
                          {campaign.is_enabled ? (
                            <Badge variant="default" className="gap-1">
                              <Zap className="size-3" />
                              {SCHEDULE_LABELS[campaign.schedule ?? ""] ?? campaign.schedule}
                            </Badge>
                          ) : (
                            <Badge variant="outline">Manual only</Badge>
                          )}
                        </div>
                        <p className="text-sm text-muted-foreground">
                          Template: {template?.name ?? "—"}
                          {campaign.daily_limit ? ` · up to ${campaign.daily_limit}/day` : ""}
                          {campaign.last_run_at
                            ? ` · last run ${new Date(campaign.last_run_at).toLocaleString()}`
                            : " · never run"}
                        </p>
                      </div>
                      <div className="flex items-center gap-2">
                        <Button
                          size="sm"
                          variant="outline"
                          disabled={busy}
                          onClick={() => handleRunCampaign(campaign.id)}
                          className="gap-2"
                        >
                          {busy ? <Spinner className="size-4" /> : <Send className="size-4" />}
                          Run Now
                        </Button>
                        {campaign.is_enabled ? (
                          <Button
                            size="sm"
                            variant="outline"
                            disabled={busy}
                            onClick={() => handleDisableCampaign(campaign.id)}
                            className="gap-2"
                          >
                            <Pause className="size-4" />
                            Disable
                          </Button>
                        ) : (
                          <>
                            <Select
                              value={campaignScheduleChoice[campaign.id] ?? "hourly"}
                              onValueChange={(v) =>
                                v &&
                                setCampaignScheduleChoice((s) => ({ ...s, [campaign.id]: v }))
                              }
                            >
                              <SelectTrigger size="sm" className="w-[140px]">
                                <SelectValue>
                                  {(value: string) => SCHEDULE_LABELS[value] ?? value}
                                </SelectValue>
                              </SelectTrigger>
                              <SelectContent>
                                {SCHEDULE_OPTIONS.map((opt) => (
                                  <SelectItem key={opt.value} value={opt.value}>
                                    {opt.label}
                                  </SelectItem>
                                ))}
                              </SelectContent>
                            </Select>
                            <Button
                              size="sm"
                              disabled={busy}
                              onClick={() => handleEnableCampaign(campaign.id)}
                              className="gap-2"
                            >
                              <Play className="size-4" />
                              Enable Automation
                            </Button>
                          </>
                        )}
                      </div>
                    </div>
                    {result ? (
                      <p className="text-sm text-muted-foreground">
                        Last run: sent {result.sent_count}, skipped {result.skipped_count}
                        {result.skipped_reasons.length > 0
                          ? ` (${result.skipped_reasons[0]}${result.skipped_reasons.length > 1 ? `, +${result.skipped_reasons.length - 1} more` : ""})`
                          : ""}
                      </p>
                    ) : null}
                  </div>
                );
              })
            )}
          </CardContent>
        </Card>

        {selectedLeadId ? (
          <Card>
            <CardHeader>
              <CardTitle className="text-sm font-medium">
                Message Log — {selectedLead?.business_name}
              </CardTitle>
            </CardHeader>
            <CardContent>
              {loadingMessages ? (
                <div className="flex justify-center py-6">
                  <Spinner className="size-5" />
                </div>
              ) : messages.length === 0 ? (
                <p className="py-6 text-center text-sm text-muted-foreground">
                  No messages sent to this lead yet.
                </p>
              ) : (
                <div className="space-y-2">
                  {messages.map((m) => (
                    <div key={m.id} className="rounded-lg border p-3">
                      <div className="flex flex-wrap items-center gap-2">
                        <Mail className="size-4 text-muted-foreground" />
                        <span className="font-medium">{m.subject}</span>
                        {m.is_test ? <Badge variant="secondary">Test</Badge> : null}
                        <Badge
                          variant={
                            m.status === "accepted_by_provider" ? "default" : "destructive"
                          }
                        >
                          {humanize(m.status)}
                        </Badge>
                      </div>
                      <p className="mt-1 text-sm text-muted-foreground">
                        To: {m.to_email}
                      </p>
                      {m.provider_response ? (
                        <p className="mt-1 text-xs text-muted-foreground">
                          {m.provider_response}
                        </p>
                      ) : null}
                    </div>
                  ))}
                  <Separator />
                </div>
              )}
            </CardContent>
          </Card>
        ) : null}
      </PageContainer>

      <Dialog open={testDialogOpen} onOpenChange={setTestDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Send test email</DialogTitle>
          </DialogHeader>
          <div className="space-y-1.5">
            <Label htmlFor="test-email">Send to</Label>
            <Input
              id="test-email"
              type="email"
              placeholder="you@example.com"
              value={testEmail}
              onChange={(e) => setTestEmail(e.target.value)}
            />
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setTestDialogOpen(false)}
              disabled={sendingTest}
            >
              Cancel
            </Button>
            <Button
              onClick={handleSendTest}
              disabled={sendingTest || !testEmail.trim()}
              className="gap-2"
            >
              {sendingTest ? <Spinner className="size-4" /> : null}
              Send Test
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={templateDialogOpen} onOpenChange={setTemplateDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Save as Template</DialogTitle>
          </DialogHeader>
          <div className="space-y-1.5">
            <Label htmlFor="template-name">Template name</Label>
            <Input
              id="template-name"
              value={newTemplateName}
              onChange={(e) => setNewTemplateName(e.target.value)}
            />
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setTemplateDialogOpen(false)}
              disabled={savingTemplate}
            >
              Cancel
            </Button>
            <Button
              onClick={handleSaveTemplate}
              disabled={savingTemplate || !newTemplateName.trim()}
              className="gap-2"
            >
              {savingTemplate ? <Spinner className="size-4" /> : null}
              Save
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={campaignDialogOpen} onOpenChange={setCampaignDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>New Campaign</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-1.5">
              <Label htmlFor="campaign-name">Campaign name</Label>
              <Input
                id="campaign-name"
                value={newCampaignName}
                onChange={(e) => setNewCampaignName(e.target.value)}
              />
            </div>
            <div className="space-y-1.5">
              <Label>Template to send</Label>
              <Select
                value={newCampaignTemplateId}
                onValueChange={(v) => setNewCampaignTemplateId(v ?? "")}
              >
                <SelectTrigger className="w-full">
                  <SelectValue placeholder="Choose a template">
                    {(value: string) => templates.find((t) => t.id === value)?.name ?? "Choose a template"}
                  </SelectValue>
                </SelectTrigger>
                <SelectContent>
                  {templates.map((t) => (
                    <SelectItem key={t.id} value={t.id}>
                      {t.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="campaign-limit">Daily send limit (optional)</Label>
              <Input
                id="campaign-limit"
                type="number"
                min={1}
                placeholder="No limit"
                value={newCampaignDailyLimit}
                onChange={(e) => setNewCampaignDailyLimit(e.target.value)}
              />
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setCampaignDialogOpen(false)}
              disabled={savingCampaign}
            >
              Cancel
            </Button>
            <Button
              onClick={handleCreateCampaign}
              disabled={savingCampaign || !newCampaignName.trim() || !newCampaignTemplateId}
              className="gap-2"
            >
              {savingCampaign ? <Spinner className="size-4" /> : null}
              Create Campaign
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}

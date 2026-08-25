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
import { Switch } from "@/components/ui/switch";
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
  createAnalysisRule,
  createService,
  deleteAnalysisRule,
  getAnalysisRules,
  getLeadAnalysisHistory,
  getLeads,
  getServices,
  analyzeLead,
  decideRecommendation,
  updateAnalysisRule,
  updateService,
  type AnalysisRule,
  type Lead,
  type LeadAnalysisResult,
  type Service,
} from "@/lib/api";
import { LeadStatusBadge } from "@/components/lead-status-badge";
import {
  AlertCircle,
  CheckCircle2,
  Plus,
  Sparkles,
  ThumbsDown,
  ThumbsUp,
  Trash2,
} from "lucide-react";

export default function AnalysisPage() {
  const [services, setServices] = useState<Service[]>([]);
  const [rules, setRules] = useState<AnalysisRule[]>([]);
  const [loadingMeta, setLoadingMeta] = useState(true);

  const [newServiceName, setNewServiceName] = useState("");
  const [savingService, setSavingService] = useState(false);

  const [ruleDialogOpen, setRuleDialogOpen] = useState(false);
  const [ruleName, setRuleName] = useState("");
  const [ruleDescription, setRuleDescription] = useState("");
  const [savingRule, setSavingRule] = useState(false);
  const [ruleError, setRuleError] = useState<string | null>(null);

  const [leads, setLeads] = useState<Lead[]>([]);
  const [loadingLeads, setLoadingLeads] = useState(true);
  const [analyzingId, setAnalyzingId] = useState<string | null>(null);
  const [analysisResults, setAnalysisResults] = useState<
    Record<string, LeadAnalysisResult>
  >({});
  const [analysisErrors, setAnalysisErrors] = useState<Record<string, string>>(
    {}
  );
  const [decidingId, setDecidingId] = useState<string | null>(null);

  const loadMeta = useCallback(async () => {
    setLoadingMeta(true);
    try {
      const [svc, rul] = await Promise.all([getServices(), getAnalysisRules()]);
      setServices(svc);
      setRules(rul);
    } catch {
      // handled via empty states below
    } finally {
      setLoadingMeta(false);
    }
  }, []);

  const loadLeads = useCallback(async () => {
    setLoadingLeads(true);
    try {
      const res = await getLeads({ page: 1, page_size: 100 });
      setLeads(res.items);
      const histories = await Promise.all(
        res.items.map((l) =>
          getLeadAnalysisHistory(l.id)
            .then((h) => [l.id, h[0]] as const)
            .catch(() => [l.id, undefined] as const)
        )
      );
      setAnalysisResults((prev) => {
        const next = { ...prev };
        for (const [id, latest] of histories) {
          if (latest) next[id] = latest;
        }
        return next;
      });
    } catch {
      // handled via empty state
    } finally {
      setLoadingLeads(false);
    }
  }, []);

  useEffect(() => {
    loadMeta();
    loadLeads();
  }, [loadMeta, loadLeads]);

  async function handleAddService() {
    if (!newServiceName.trim()) return;
    setSavingService(true);
    try {
      await createService({ name: newServiceName.trim() });
      setNewServiceName("");
      await loadMeta();
    } finally {
      setSavingService(false);
    }
  }

  async function handleToggleService(service: Service) {
    await updateService(service.id, { enabled: !service.enabled });
    await loadMeta();
  }

  async function handleSaveRule() {
    if (!ruleName.trim() || !ruleDescription.trim()) return;
    setSavingRule(true);
    setRuleError(null);
    try {
      await createAnalysisRule({
        name: ruleName.trim(),
        description: ruleDescription.trim(),
      });
      setRuleDialogOpen(false);
      setRuleName("");
      setRuleDescription("");
      await loadMeta();
    } catch (error) {
      setRuleError((error as Error).message);
    } finally {
      setSavingRule(false);
    }
  }

  async function handleToggleRule(rule: AnalysisRule) {
    await updateAnalysisRule(rule.id, { enabled: !rule.enabled });
    await loadMeta();
  }

  async function handleDeleteRule(rule: AnalysisRule) {
    await deleteAnalysisRule(rule.id);
    await loadMeta();
  }

  async function handleAnalyze(lead: Lead) {
    setAnalyzingId(lead.id);
    setAnalysisErrors((e) => ({ ...e, [lead.id]: "" }));
    try {
      const result = await analyzeLead(lead.id);
      setAnalysisResults((r) => ({ ...r, [lead.id]: result }));
    } catch (error) {
      setAnalysisErrors((e) => ({ ...e, [lead.id]: (error as Error).message }));
    } finally {
      setAnalyzingId(null);
    }
  }

  async function handleDecision(
    lead: Lead,
    result: LeadAnalysisResult,
    decision: "approved" | "rejected"
  ) {
    if (!result.recommendation) return;
    setDecidingId(lead.id);
    try {
      const updated = await decideRecommendation(
        lead.id,
        result.recommendation.id,
        { decision }
      );
      setAnalysisResults((r) => ({
        ...r,
        [lead.id]: { ...result, recommendation: updated },
      }));
    } finally {
      setDecidingId(null);
    }
  }

  const enabledServiceCount = services.filter((s) => s.enabled).length;

  return (
    <>
      <AppHeader
        title="AI Analysis"
        description="AI business analysis and service recommendation"
      />
      <PageContainer>
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle className="text-sm font-medium">
                Service Catalog
              </CardTitle>
              <p className="text-sm text-muted-foreground">
                The AI can only recommend services enabled here.
              </p>
            </CardHeader>
            <CardContent className="space-y-3">
              {loadingMeta ? (
                <div className="flex justify-center py-6">
                  <Spinner className="size-5" />
                </div>
              ) : (
                <>
                  {services.map((service) => (
                    <div
                      key={service.id}
                      className="flex items-center justify-between gap-3 rounded-lg border p-3"
                    >
                      <div className="flex items-center gap-3">
                        <Switch
                          checked={service.enabled}
                          onCheckedChange={() => handleToggleService(service)}
                        />
                        <span className="font-medium">{service.name}</span>
                      </div>
                    </div>
                  ))}
                  <div className="flex gap-2 pt-1">
                    <Input
                      placeholder="New service name"
                      value={newServiceName}
                      onChange={(e) => setNewServiceName(e.target.value)}
                    />
                    <Button
                      variant="outline"
                      disabled={savingService || !newServiceName.trim()}
                      onClick={handleAddService}
                      className="gap-2"
                    >
                      {savingService ? (
                        <Spinner className="size-4" />
                      ) : (
                        <Plus className="size-4" />
                      )}
                      Add
                    </Button>
                  </div>
                </>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0">
              <div>
                <CardTitle className="text-sm font-medium">
                  Analysis Guidance Rules
                </CardTitle>
                <p className="text-sm text-muted-foreground">
                  Optional instructions that steer how the AI evaluates a lead.
                </p>
              </div>
              <Button
                size="sm"
                onClick={() => setRuleDialogOpen(true)}
                className="gap-2"
              >
                <Plus className="size-4" />
                Add Rule
              </Button>
            </CardHeader>
            <CardContent className="space-y-2">
              {loadingMeta ? (
                <div className="flex justify-center py-6">
                  <Spinner className="size-5" />
                </div>
              ) : rules.length === 0 ? (
                <p className="py-4 text-center text-sm text-muted-foreground">
                  No guidance rules yet. These are optional instructions fed to
                  the AI (e.g. "prioritize businesses without a website").
                </p>
              ) : (
                rules.map((rule) => (
                  <div
                    key={rule.id}
                    className="flex items-start justify-between gap-3 rounded-lg border p-3"
                  >
                    <div className="flex items-start gap-3">
                      <Switch
                        checked={rule.enabled}
                        onCheckedChange={() => handleToggleRule(rule)}
                        className="mt-0.5"
                      />
                      <div>
                        <p className="font-medium">{rule.name}</p>
                        <p className="text-sm text-muted-foreground">
                          {rule.description}
                        </p>
                      </div>
                    </div>
                    <Button
                      size="icon-sm"
                      variant="outline"
                      onClick={() => handleDeleteRule(rule)}
                    >
                      <Trash2 className="size-4" />
                    </Button>
                  </div>
                ))
              )}
            </CardContent>
          </Card>
        </div>

        {enabledServiceCount === 0 && !loadingMeta ? (
          <Alert variant="destructive">
            <AlertCircle className="size-4" />
            <AlertTitle>No enabled services</AlertTitle>
            <AlertDescription>
              Enable at least one service in the catalog above before running
              analysis — the AI can only recommend from enabled services.
            </AlertDescription>
          </Alert>
        ) : null}

        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium">
              Leads {leads.length > 0 ? `(${leads.length})` : ""}
            </CardTitle>
            <p className="text-sm text-muted-foreground">
              Run AI analysis to get an opportunity score, evidence, and a
              recommended service for each lead.
            </p>
          </CardHeader>
          <CardContent>
            {loadingLeads ? (
              <div className="flex items-center justify-center py-10 text-muted-foreground">
                <Spinner className="size-5" />
              </div>
            ) : leads.length === 0 ? (
              <p className="py-10 text-center text-sm text-muted-foreground">
                No leads yet. Find some in Lead Discovery first.
              </p>
            ) : (
              <div className="space-y-3">
                {leads.map((lead) => {
                  const result = analysisResults[lead.id];
                  const error = analysisErrors[lead.id];
                  return (
                    <div key={lead.id} className="rounded-lg border p-4">
                      <div className="flex flex-wrap items-center justify-between gap-3">
                        <div>
                          <div className="flex items-center gap-2">
                            <p className="font-medium">{lead.business_name}</p>
                            <LeadStatusBadge status={lead.status} />
                          </div>
                          <p className="text-sm text-muted-foreground">
                            {lead.category ?? "—"}
                          </p>
                        </div>
                        <Button
                          size="sm"
                          variant="outline"
                          disabled={analyzingId === lead.id}
                          onClick={() => handleAnalyze(lead)}
                          className="gap-2"
                        >
                          {analyzingId === lead.id ? (
                            <Spinner className="size-4" />
                          ) : (
                            <Sparkles className="size-4" />
                          )}
                          Analyze
                        </Button>
                      </div>

                      {error ? (
                        <Alert variant="destructive" className="mt-3">
                          <AlertCircle className="size-4" />
                          <AlertTitle>Analysis failed</AlertTitle>
                          <AlertDescription>{error}</AlertDescription>
                        </Alert>
                      ) : null}

                      {result && !error ? (
                        <div className="mt-3 space-y-3 rounded-md bg-muted/40 p-3">
                          <div className="flex flex-wrap items-center gap-2">
                            <Badge variant={result.needs_review ? "secondary" : "default"}>
                              {result.needs_review ? "Needs Review" : "Ready"}
                            </Badge>
                            <Badge variant="outline">
                              Score: {result.score}
                            </Badge>
                            <Badge variant="outline">
                              Confidence: {Math.round(result.confidence * 100)}%
                            </Badge>
                          </div>
                          <p className="text-sm">{result.summary}</p>
                          {result.opportunities.length > 0 ? (
                            <div>
                              <p className="text-xs font-medium text-muted-foreground">
                                Opportunities
                              </p>
                              <ul className="ml-4 list-disc text-sm">
                                {result.opportunities.map((o, i) => (
                                  <li key={i}>{o}</li>
                                ))}
                              </ul>
                            </div>
                          ) : null}
                          {result.missing_information.length > 0 ? (
                            <div>
                              <p className="text-xs font-medium text-muted-foreground">
                                Missing information
                              </p>
                              <ul className="ml-4 list-disc text-sm text-muted-foreground">
                                {result.missing_information.map((m, i) => (
                                  <li key={i}>{m}</li>
                                ))}
                              </ul>
                            </div>
                          ) : null}
                          <p className="text-sm">
                            <span className="font-medium">Next action: </span>
                            {result.next_action}
                          </p>

                          {result.recommendation ? (
                            <>
                              <Separator />
                              <div>
                                <p className="font-medium">
                                  Recommended: {result.recommendation.recommended_service_name}
                                </p>
                                <p className="mt-1 text-sm text-muted-foreground">
                                  <span className="font-medium text-foreground">
                                    Why this service?{" "}
                                  </span>
                                  {result.recommendation.reasoning}
                                </p>
                                {result.recommendation.human_decision ? (
                                  <Badge
                                    className="mt-2 gap-1"
                                    variant={
                                      result.recommendation.human_decision ===
                                      "approved"
                                        ? "default"
                                        : "destructive"
                                    }
                                  >
                                    {result.recommendation.human_decision ===
                                    "approved" ? (
                                      <CheckCircle2 className="size-3" />
                                    ) : (
                                      <AlertCircle className="size-3" />
                                    )}
                                    {result.recommendation.human_decision}
                                  </Badge>
                                ) : (
                                  <div className="mt-2 flex gap-2">
                                    <Button
                                      size="sm"
                                      variant="outline"
                                      disabled={decidingId === lead.id}
                                      onClick={() =>
                                        handleDecision(lead, result, "approved")
                                      }
                                      className="gap-2"
                                    >
                                      <ThumbsUp className="size-4" />
                                      Approve
                                    </Button>
                                    <Button
                                      size="sm"
                                      variant="outline"
                                      disabled={decidingId === lead.id}
                                      onClick={() =>
                                        handleDecision(lead, result, "rejected")
                                      }
                                      className="gap-2"
                                    >
                                      <ThumbsDown className="size-4" />
                                      Reject
                                    </Button>
                                  </div>
                                )}
                              </div>
                            </>
                          ) : null}
                        </div>
                      ) : null}
                    </div>
                  );
                })}
              </div>
            )}
          </CardContent>
        </Card>
      </PageContainer>

      <Dialog open={ruleDialogOpen} onOpenChange={setRuleDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Add Analysis Guidance Rule</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-1.5">
              <Label htmlFor="analysis-rule-name">Name</Label>
              <Input
                id="analysis-rule-name"
                value={ruleName}
                onChange={(e) => setRuleName(e.target.value)}
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="analysis-rule-description">
                Instruction for the AI
              </Label>
              <Textarea
                id="analysis-rule-description"
                placeholder='e.g. "Prioritize businesses with no website for Website Design"'
                value={ruleDescription}
                onChange={(e) => setRuleDescription(e.target.value)}
              />
            </div>
            {ruleError ? (
              <Alert variant="destructive">
                <AlertCircle className="size-4" />
                <AlertDescription>{ruleError}</AlertDescription>
              </Alert>
            ) : null}
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setRuleDialogOpen(false)}
              disabled={savingRule}
            >
              Cancel
            </Button>
            <Button
              onClick={handleSaveRule}
              disabled={savingRule || !ruleName.trim() || !ruleDescription.trim()}
              className="gap-2"
            >
              {savingRule ? <Spinner className="size-4" /> : null}
              Save
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}

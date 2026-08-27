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
import { Switch } from "@/components/ui/switch";
import { Spinner } from "@/components/ui/spinner";
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
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  createQualificationRule,
  deleteQualificationRule,
  getLeads,
  getQualificationFields,
  getQualificationRules,
  overrideQualification,
  qualifyLead,
  updateQualificationRule,
  type Lead,
  type QualificationFields,
  type QualificationRule,
} from "@/lib/api";
import {
  AlertCircle,
  CheckCircle2,
  HelpCircle,
  ListChecks,
  Pencil,
  Plus,
  ShieldQuestion,
  Trash2,
  Users,
  XCircle,
} from "lucide-react";

const OPERATOR_LABELS: Record<string, string> = {
  equals: "equals",
  not_equals: "does not equal",
  contains: "contains",
  not_contains: "does not contain",
  in: "is one of",
  not_in: "is not one of",
  exists: "is present",
  not_exists: "is missing",
  greater_than: "is greater than",
  less_than: "is less than",
};

const RESULT_META: Record<
  string,
  { label: string; variant: "default" | "destructive" | "secondary"; icon: typeof CheckCircle2 }
> = {
  qualified: { label: "Qualified", variant: "default", icon: CheckCircle2 },
  not_qualified: { label: "Not Qualified", variant: "destructive", icon: XCircle },
  needs_review: { label: "Needs Review", variant: "secondary", icon: HelpCircle },
  new: { label: "Not qualified yet", variant: "secondary", icon: ShieldQuestion },
};

type RuleFormState = {
  id: string | null;
  name: string;
  description: string;
  field: string;
  operator: string;
  expected_value: string;
  priority: string;
};

const emptyRuleForm: RuleFormState = {
  id: null,
  name: "",
  description: "",
  field: "",
  operator: "",
  expected_value: "",
  priority: "0",
};

function needsExpectedValue(operator: string) {
  return operator !== "exists" && operator !== "not_exists" && operator !== "";
}

export default function QualificationPage() {
  const [fields, setFields] = useState<QualificationFields>({});
  const [rules, setRules] = useState<QualificationRule[]>([]);
  const [loadingRules, setLoadingRules] = useState(true);

  const [ruleDialogOpen, setRuleDialogOpen] = useState(false);
  const [ruleForm, setRuleForm] = useState<RuleFormState>(emptyRuleForm);
  const [ruleSaving, setRuleSaving] = useState(false);
  const [ruleError, setRuleError] = useState<string | null>(null);

  const [leads, setLeads] = useState<Lead[]>([]);
  const [loadingLeads, setLoadingLeads] = useState(true);
  const [qualifyingId, setQualifyingId] = useState<string | null>(null);
  const [qualifyError, setQualifyError] = useState<{ id: string; message: string } | null>(
    null
  );

  const [overrideTarget, setOverrideTarget] = useState<Lead | null>(null);
  const [overrideResult, setOverrideResult] = useState("qualified");
  const [overrideReason, setOverrideReason] = useState("");
  const [overrideSaving, setOverrideSaving] = useState(false);
  const [overrideError, setOverrideError] = useState<string | null>(null);

  const loadFields = useCallback(async () => {
    try {
      setFields(await getQualificationFields());
    } catch {
      // field metadata only affects the rule builder dropdowns; page still usable without it
    }
  }, []);

  const loadRules = useCallback(async () => {
    setLoadingRules(true);
    try {
      setRules(await getQualificationRules());
    } catch {
      // handled inline via empty state
    } finally {
      setLoadingRules(false);
    }
  }, []);

  const loadLeads = useCallback(async () => {
    setLoadingLeads(true);
    try {
      const res = await getLeads({ page: 1, page_size: 100 });
      setLeads(res.items);
    } catch {
      // handled inline via empty state
    } finally {
      setLoadingLeads(false);
    }
  }, []);

  useEffect(() => {
    loadFields();
    loadRules();
    loadLeads();
  }, [loadFields, loadRules, loadLeads]);

  function openNewRuleDialog() {
    setRuleForm(emptyRuleForm);
    setRuleError(null);
    setRuleDialogOpen(true);
  }

  function openEditRuleDialog(rule: QualificationRule) {
    setRuleForm({
      id: rule.id,
      name: rule.name,
      description: rule.description ?? "",
      field: rule.field,
      operator: rule.operator,
      expected_value: rule.expected_value ?? "",
      priority: String(rule.priority),
    });
    setRuleError(null);
    setRuleDialogOpen(true);
  }

  async function handleSaveRule() {
    if (!ruleForm.name.trim() || !ruleForm.field || !ruleForm.operator) return;

    setRuleSaving(true);
    setRuleError(null);
    try {
      const payload = {
        name: ruleForm.name.trim(),
        description: ruleForm.description.trim() || undefined,
        field: ruleForm.field,
        operator: ruleForm.operator,
        expected_value: needsExpectedValue(ruleForm.operator)
          ? ruleForm.expected_value.trim()
          : undefined,
        priority: Number(ruleForm.priority) || 0,
      };
      if (ruleForm.id) {
        await updateQualificationRule(ruleForm.id, payload);
      } else {
        await createQualificationRule(payload);
      }
      setRuleDialogOpen(false);
      await loadRules();
    } catch (error) {
      setRuleError((error as Error).message);
    } finally {
      setRuleSaving(false);
    }
  }

  async function handleToggleRule(rule: QualificationRule) {
    await updateQualificationRule(rule.id, { enabled: !rule.enabled });
    await loadRules();
  }

  async function handleDeleteRule(rule: QualificationRule) {
    await deleteQualificationRule(rule.id);
    await loadRules();
  }

  async function handleQualify(lead: Lead) {
    setQualifyingId(lead.id);
    setQualifyError(null);
    try {
      await qualifyLead(lead.id);
      await loadLeads();
    } catch (error) {
      setQualifyError({ id: lead.id, message: (error as Error).message });
    } finally {
      setQualifyingId(null);
    }
  }

  function openOverrideDialog(lead: Lead) {
    setOverrideTarget(lead);
    setOverrideResult("qualified");
    setOverrideReason("");
    setOverrideError(null);
  }

  async function handleSaveOverride() {
    if (!overrideTarget || !overrideReason.trim()) return;
    setOverrideSaving(true);
    setOverrideError(null);
    try {
      await overrideQualification(overrideTarget.id, {
        result: overrideResult,
        reason: overrideReason.trim(),
      });
      setOverrideTarget(null);
      await loadLeads();
    } catch (error) {
      setOverrideError((error as Error).message);
    } finally {
      setOverrideSaving(false);
    }
  }

  const fieldOptions = Object.keys(fields);
  const operatorOptions = ruleForm.field ? fields[ruleForm.field] ?? [] : [];

  return (
    <>
      <AppHeader
        title="Qualification"
        description="Rule-based lead qualification"
      />
      <PageContainer>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0">
            <div className="flex items-center gap-3">
              <SectionIcon icon={ListChecks} color="emerald" />
              <CardTitle className="text-base font-semibold">
                Qualification Rules
              </CardTitle>
            </div>
            <Button size="sm" onClick={openNewRuleDialog} className="gap-2">
              <Plus className="size-4" />
              Add Rule
            </Button>
          </CardHeader>
          <CardContent>
            {loadingRules ? (
              <div className="flex items-center justify-center py-8 text-muted-foreground">
                <Spinner className="size-5" />
              </div>
            ) : rules.length === 0 ? (
              <p className="py-6 text-center text-sm text-muted-foreground">
                No rules yet. Add one to start qualifying leads — for example,
                "Website is present" or "Rating is greater than 4".
              </p>
            ) : (
              <div className="space-y-2">
                {rules.map((rule) => (
                  <div
                    key={rule.id}
                    className="flex flex-wrap items-center justify-between gap-3 rounded-lg border p-3"
                  >
                    <div className="flex items-center gap-3">
                      <Switch
                        checked={rule.enabled}
                        onCheckedChange={() => handleToggleRule(rule)}
                      />
                      <div>
                        <p className="font-medium">{rule.name}</p>
                        <p className="text-sm text-muted-foreground">
                          {rule.field}{" "}
                          {OPERATOR_LABELS[rule.operator] ?? rule.operator}
                          {needsExpectedValue(rule.operator)
                            ? ` "${rule.expected_value}"`
                            : ""}
                          {" · priority "}
                          {rule.priority}
                        </p>
                        {rule.description ? (
                          <p className="mt-0.5 text-xs text-muted-foreground">
                            {rule.description}
                          </p>
                        ) : null}
                      </div>
                    </div>
                    <div className="flex gap-2">
                      <Button
                        size="icon-sm"
                        variant="outline"
                        onClick={() => openEditRuleDialog(rule)}
                      >
                        <Pencil className="size-4" />
                      </Button>
                      <Button
                        size="icon-sm"
                        variant="outline"
                        onClick={() => handleDeleteRule(rule)}
                      >
                        <Trash2 className="size-4" />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex-row items-center gap-3 space-y-0">
            <SectionIcon icon={Users} color="indigo" />
            <CardTitle className="text-base font-semibold">
              Leads {leads.length > 0 ? `(${leads.length})` : ""}
            </CardTitle>
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
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Business</TableHead>
                      <TableHead>Category</TableHead>
                      <TableHead>Website</TableHead>
                      <TableHead>Rating</TableHead>
                      <TableHead>Qualification</TableHead>
                      <TableHead className="text-right">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {leads.map((lead) => {
                      const meta = RESULT_META[lead.status] ?? RESULT_META.new;
                      const Icon = meta.icon;
                      return (
                        <TableRow key={lead.id}>
                          <TableCell className="font-medium">
                            {lead.business_name}
                          </TableCell>
                          <TableCell className="text-muted-foreground">
                            {lead.category ?? "—"}
                          </TableCell>
                          <TableCell className="text-muted-foreground">
                            {lead.website ? "Yes" : "No"}
                          </TableCell>
                          <TableCell className="text-muted-foreground">
                            {lead.rating ?? "—"}
                          </TableCell>
                          <TableCell>
                            <Badge variant={meta.variant} className="gap-1">
                              <Icon className="size-3" />
                              {meta.label}
                            </Badge>
                            {qualifyError && qualifyError.id === lead.id ? (
                              <p className="mt-1 text-xs text-destructive">
                                {qualifyError.message}
                              </p>
                            ) : null}
                          </TableCell>
                          <TableCell className="text-right">
                            <div className="flex justify-end gap-2">
                              <Button
                                size="sm"
                                variant="outline"
                                disabled={qualifyingId === lead.id}
                                onClick={() => handleQualify(lead)}
                              >
                                {qualifyingId === lead.id ? (
                                  <Spinner className="size-4" />
                                ) : (
                                  "Qualify"
                                )}
                              </Button>
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => openOverrideDialog(lead)}
                              >
                                Override
                              </Button>
                            </div>
                          </TableCell>
                        </TableRow>
                      );
                    })}
                  </TableBody>
                </Table>
              </div>
            )}
          </CardContent>
        </Card>
      </PageContainer>

      <Dialog open={ruleDialogOpen} onOpenChange={setRuleDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              {ruleForm.id ? "Edit Rule" : "Add Rule"}
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-1.5">
              <Label htmlFor="rule-name">Name</Label>
              <Input
                id="rule-name"
                placeholder="e.g. Has Website"
                value={ruleForm.name}
                onChange={(e) =>
                  setRuleForm((f) => ({ ...f, name: e.target.value }))
                }
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="rule-description">Description (optional)</Label>
              <Textarea
                id="rule-description"
                value={ruleForm.description}
                onChange={(e) =>
                  setRuleForm((f) => ({ ...f, description: e.target.value }))
                }
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1.5">
                <Label>Field</Label>
                <Select
                  value={ruleForm.field}
                  onValueChange={(value) =>
                    value &&
                    setRuleForm((f) => ({ ...f, field: value, operator: "" }))
                  }
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Choose a field" />
                  </SelectTrigger>
                  <SelectContent>
                    {fieldOptions.map((field) => (
                      <SelectItem key={field} value={field}>
                        {field}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-1.5">
                <Label>Operator</Label>
                <Select
                  value={ruleForm.operator}
                  onValueChange={(value) =>
                    value && setRuleForm((f) => ({ ...f, operator: value }))
                  }
                  disabled={!ruleForm.field}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Choose an operator" />
                  </SelectTrigger>
                  <SelectContent>
                    {operatorOptions.map((op) => (
                      <SelectItem key={op} value={op}>
                        {OPERATOR_LABELS[op] ?? op}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
            {needsExpectedValue(ruleForm.operator) ? (
              <div className="space-y-1.5">
                <Label htmlFor="rule-value">
                  Expected value
                  {ruleForm.operator === "in" || ruleForm.operator === "not_in"
                    ? " (comma-separated)"
                    : ""}
                </Label>
                <Input
                  id="rule-value"
                  value={ruleForm.expected_value}
                  onChange={(e) =>
                    setRuleForm((f) => ({
                      ...f,
                      expected_value: e.target.value,
                    }))
                  }
                />
              </div>
            ) : null}
            <div className="space-y-1.5">
              <Label htmlFor="rule-priority">
                Priority (lower runs first)
              </Label>
              <Input
                id="rule-priority"
                type="number"
                value={ruleForm.priority}
                onChange={(e) =>
                  setRuleForm((f) => ({ ...f, priority: e.target.value }))
                }
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
              disabled={ruleSaving}
            >
              Cancel
            </Button>
            <Button
              onClick={handleSaveRule}
              disabled={
                ruleSaving ||
                !ruleForm.name.trim() ||
                !ruleForm.field ||
                !ruleForm.operator
              }
              className="gap-2"
            >
              {ruleSaving ? <Spinner className="size-4" /> : null}
              Save
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog
        open={overrideTarget !== null}
        onOpenChange={(open) => !open && setOverrideTarget(null)}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              Override qualification — {overrideTarget?.business_name}
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-1.5">
              <Label>New result</Label>
              <Select value={overrideResult} onValueChange={(v) => setOverrideResult(v ?? "")}>
                <SelectTrigger>
                  <SelectValue>
                    {(value: string) =>
                      ({
                        qualified: "Qualified",
                        not_qualified: "Not Qualified",
                        needs_review: "Needs Review",
                      })[value] ?? value
                    }
                  </SelectValue>
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="qualified">Qualified</SelectItem>
                  <SelectItem value="not_qualified">Not Qualified</SelectItem>
                  <SelectItem value="needs_review">Needs Review</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="override-reason">
                Reason <span className="text-destructive">*</span>
              </Label>
              <Textarea
                id="override-reason"
                placeholder="Why are you overriding the automatic result?"
                value={overrideReason}
                onChange={(e) => setOverrideReason(e.target.value)}
              />
            </div>
            {overrideError ? (
              <Alert variant="destructive">
                <AlertCircle className="size-4" />
                <AlertDescription>{overrideError}</AlertDescription>
              </Alert>
            ) : null}
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setOverrideTarget(null)}
              disabled={overrideSaving}
            >
              Cancel
            </Button>
            <Button
              onClick={handleSaveOverride}
              disabled={overrideSaving || !overrideReason.trim()}
              className="gap-2"
            >
              {overrideSaving ? <Spinner className="size-4" /> : null}
              Save Override
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}

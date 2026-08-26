"use client";

import { useEffect, useState, useCallback } from "react";
import { AppHeader } from "@/components/layout/app-header";
import { PageContainer } from "@/components/layout/page-container";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Spinner } from "@/components/ui/spinner";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
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
  createSearchConfiguration,
  disableAutomation,
  enableAutomation,
  getLeads,
  getSearchConfigurations,
  runSearchConfiguration,
  searchLeads,
  type Lead,
  type LeadSearchRun,
  type SearchConfiguration,
} from "@/lib/api";
import { LeadStatusBadge } from "@/components/lead-status-badge";
import {
  AlertCircle,
  Bookmark,
  Building2,
  CheckCircle2,
  ChevronDown,
  ExternalLink,
  MapPin,
  Play,
  Search,
  SlidersHorizontal,
  Zap,
  ZapOff,
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

type FormState = {
  business_type: string;
  location: string;
  latitude: string;
  longitude: string;
  radius_meters: string;
  keywords: string;
  max_results: string;
};

const initialForm: FormState = {
  business_type: "",
  location: "",
  latitude: "",
  longitude: "",
  radius_meters: "",
  keywords: "",
  max_results: "20",
};

function RunSummary({ run }: { run: LeadSearchRun }) {
  return (
    <Alert variant={run.status === "failed" ? "destructive" : "default"}>
      {run.status === "failed" ? (
        <AlertCircle className="size-4" />
      ) : (
        <CheckCircle2 className="size-4" />
      )}
      <AlertTitle>
        {run.status === "failed" ? "Search run failed" : "Search run completed"}
      </AlertTitle>
      <AlertDescription>
        {run.status === "failed"
          ? run.error_message
          : `${run.new_leads_count} new lead${run.new_leads_count === 1 ? "" : "s"}, ${run.duplicate_count} duplicate${run.duplicate_count === 1 ? "" : "s"}, ${run.failed_count} failed`}
      </AlertDescription>
    </Alert>
  );
}

export default function LeadDiscoveryPage() {
  const [form, setForm] = useState<FormState>(initialForm);
  const [advancedOpen, setAdvancedOpen] = useState(false);
  const [searching, setSearching] = useState(false);
  const [lastRun, setLastRun] = useState<LeadSearchRun | null>(null);
  const [searchError, setSearchError] = useState<string | null>(null);

  const [saveOpen, setSaveOpen] = useState(false);
  const [saveName, setSaveName] = useState("");
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);

  const [configs, setConfigs] = useState<SearchConfiguration[]>([]);
  const [loadingConfigs, setLoadingConfigs] = useState(true);
  const [runningConfigId, setRunningConfigId] = useState<string | null>(null);
  const [configRunResult, setConfigRunResult] = useState<{
    id: string;
    run: LeadSearchRun;
  } | null>(null);

  const [scheduleChoice, setScheduleChoice] = useState<Record<string, string>>(
    {}
  );
  const [automationBusyId, setAutomationBusyId] = useState<string | null>(
    null
  );
  const [automationError, setAutomationError] = useState<{
    id: string;
    message: string;
  } | null>(null);

  const [leads, setLeads] = useState<Lead[]>([]);
  const [total, setTotal] = useState(0);
  const [loadingLeads, setLoadingLeads] = useState(true);
  const [listError, setListError] = useState<string | null>(null);

  const loadLeads = useCallback(async () => {
    setLoadingLeads(true);
    setListError(null);
    try {
      const res = await getLeads({ page: 1, page_size: 50 });
      setLeads(res.items);
      setTotal(res.total);
    } catch (error) {
      setListError((error as Error).message);
    } finally {
      setLoadingLeads(false);
    }
  }, []);

  const loadConfigs = useCallback(async () => {
    setLoadingConfigs(true);
    try {
      const res = await getSearchConfigurations();
      setConfigs(res);
    } catch {
      // saved searches are a convenience; a load failure here shouldn't block the page
    } finally {
      setLoadingConfigs(false);
    }
  }, []);

  useEffect(() => {
    loadLeads();
    loadConfigs();
  }, [loadLeads, loadConfigs]);

  function currentFormAsSearchPayload() {
    return {
      business_type: form.business_type.trim(),
      location: form.location.trim(),
      latitude: form.latitude ? Number(form.latitude) : undefined,
      longitude: form.longitude ? Number(form.longitude) : undefined,
      radius_meters: form.radius_meters ? Number(form.radius_meters) : undefined,
      keywords: form.keywords.trim() || undefined,
      max_results: Number(form.max_results) || 20,
      source: "google_places",
    };
  }

  async function handleSearch(event: React.FormEvent) {
    event.preventDefault();
    if (!form.business_type.trim() || !form.location.trim()) return;

    setSearching(true);
    setSearchError(null);
    setLastRun(null);
    setConfigRunResult(null);

    try {
      const response = await searchLeads(currentFormAsSearchPayload());
      setLastRun(response.run);
      await loadLeads();
    } catch (error) {
      setSearchError((error as Error).message);
    } finally {
      setSearching(false);
    }
  }

  async function handleSaveSearch() {
    if (!saveName.trim() || !form.business_type.trim() || !form.location.trim())
      return;

    setSaving(true);
    setSaveError(null);
    try {
      await createSearchConfiguration({
        name: saveName.trim(),
        ...currentFormAsSearchPayload(),
      });
      setSaveOpen(false);
      setSaveName("");
      await loadConfigs();
    } catch (error) {
      setSaveError((error as Error).message);
    } finally {
      setSaving(false);
    }
  }

  async function handleRunConfig(config: SearchConfiguration) {
    setRunningConfigId(config.id);
    setConfigRunResult(null);
    setLastRun(null);
    setSearchError(null);
    try {
      const response = await runSearchConfiguration(config.id);
      setConfigRunResult({ id: config.id, run: response.run });
      await Promise.all([loadConfigs(), loadLeads()]);
    } catch (error) {
      setConfigRunResult({
        id: config.id,
        run: {
          id: "",
          mode: "semi_auto",
          status: "failed",
          new_leads_count: 0,
          duplicate_count: 0,
          failed_count: 0,
          error_message: (error as Error).message,
          started_at: null,
          completed_at: null,
        },
      });
    } finally {
      setRunningConfigId(null);
    }
  }

  async function handleEnableAutomation(config: SearchConfiguration) {
    const schedule = scheduleChoice[config.id] ?? "hourly";
    setAutomationBusyId(config.id);
    setAutomationError(null);
    try {
      await enableAutomation(config.id, schedule);
      await loadConfigs();
    } catch (error) {
      setAutomationError({ id: config.id, message: (error as Error).message });
    } finally {
      setAutomationBusyId(null);
    }
  }

  async function handleDisableAutomation(config: SearchConfiguration) {
    setAutomationBusyId(config.id);
    setAutomationError(null);
    try {
      await disableAutomation(config.id);
      await loadConfigs();
    } catch (error) {
      setAutomationError({ id: config.id, message: (error as Error).message });
    } finally {
      setAutomationBusyId(null);
    }
  }

  const canSave = form.business_type.trim() !== "" && form.location.trim() !== "";

  return (
    <>
      <AppHeader
        title="Lead Discovery"
        description="Find and qualify new business leads from Google Places"
      />
      <PageContainer>
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium">
              Find Leads
            </CardTitle>
            <p className="text-sm text-muted-foreground">
              Search by business type and location, or pin an exact point with
              coordinates for more precise results.
            </p>
          </CardHeader>
          <CardContent className="space-y-4">
            <form onSubmit={handleSearch} className="space-y-4">
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <div className="space-y-1.5">
                  <Label htmlFor="business_type">
                    Business type <span className="text-destructive">*</span>
                  </Label>
                  <div className="relative">
                    <Building2 className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
                    <Input
                      id="business_type"
                      placeholder="e.g. Hotels, Restaurants, Dentists"
                      value={form.business_type}
                      onChange={(e) =>
                        setForm((f) => ({ ...f, business_type: e.target.value }))
                      }
                      className="pl-9"
                      required
                    />
                  </div>
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="location">
                    Location <span className="text-destructive">*</span>
                  </Label>
                  <div className="relative">
                    <MapPin className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
                    <Input
                      id="location"
                      placeholder="e.g. Lahore, Pakistan"
                      value={form.location}
                      onChange={(e) =>
                        setForm((f) => ({ ...f, location: e.target.value }))
                      }
                      className="pl-9"
                      required
                    />
                  </div>
                </div>
              </div>

              <Collapsible open={advancedOpen} onOpenChange={setAdvancedOpen}>
                <CollapsibleTrigger className="flex items-center gap-1.5 text-sm font-medium text-muted-foreground transition-colors hover:text-foreground">
                  <SlidersHorizontal className="size-3.5" />
                  Precise location &amp; advanced options
                  <ChevronDown
                    className={`size-3.5 transition-transform ${
                      advancedOpen ? "rotate-180" : ""
                    }`}
                  />
                </CollapsibleTrigger>
                <CollapsibleContent className="mt-4">
                  <div className="grid grid-cols-1 gap-4 rounded-lg border bg-muted/30 p-4 sm:grid-cols-2 lg:grid-cols-3">
                    <div className="space-y-1.5">
                      <Label htmlFor="latitude">Latitude</Label>
                      <Input
                        id="latitude"
                        type="number"
                        step="any"
                        placeholder="e.g. 31.5497"
                        value={form.latitude}
                        onChange={(e) =>
                          setForm((f) => ({ ...f, latitude: e.target.value }))
                        }
                      />
                    </div>
                    <div className="space-y-1.5">
                      <Label htmlFor="longitude">Longitude</Label>
                      <Input
                        id="longitude"
                        type="number"
                        step="any"
                        placeholder="e.g. 74.3436"
                        value={form.longitude}
                        onChange={(e) =>
                          setForm((f) => ({ ...f, longitude: e.target.value }))
                        }
                      />
                    </div>
                    <div className="space-y-1.5">
                      <Label htmlFor="radius_meters">Search radius (meters)</Label>
                      <Input
                        id="radius_meters"
                        type="number"
                        placeholder="e.g. 5000"
                        value={form.radius_meters}
                        onChange={(e) =>
                          setForm((f) => ({ ...f, radius_meters: e.target.value }))
                        }
                      />
                    </div>
                    <div className="space-y-1.5">
                      <Label htmlFor="keywords">Keywords</Label>
                      <Input
                        id="keywords"
                        placeholder="Optional"
                        value={form.keywords}
                        onChange={(e) =>
                          setForm((f) => ({ ...f, keywords: e.target.value }))
                        }
                      />
                    </div>
                    <div className="space-y-1.5">
                      <Label htmlFor="max_results">Result limit</Label>
                      <Input
                        id="max_results"
                        type="number"
                        min={1}
                        max={20}
                        value={form.max_results}
                        onChange={(e) =>
                          setForm((f) => ({ ...f, max_results: e.target.value }))
                        }
                      />
                    </div>
                  </div>
                  <p className="mt-2 text-xs text-muted-foreground">
                    Latitude and longitude narrow the search to an exact point —
                    useful when a place name is ambiguous. Leave them blank to
                    search by location name alone.
                  </p>
                </CollapsibleContent>
              </Collapsible>

              <div className="flex flex-col gap-2 sm:flex-row">
                <Button type="submit" disabled={searching} className="flex-1 gap-2">
                  {searching ? (
                    <Spinner className="size-4" />
                  ) : (
                    <Search className="size-4" />
                  )}
                  {searching ? "Searching..." : "Search Now"}
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  disabled={!canSave}
                  onClick={() => setSaveOpen(true)}
                  className="flex-1 gap-2"
                >
                  <Bookmark className="size-4" />
                  Save Search
                </Button>
              </div>
            </form>

            {searchError ? (
              <Alert variant="destructive">
                <AlertCircle className="size-4" />
                <AlertTitle>Search failed</AlertTitle>
                <AlertDescription>{searchError}</AlertDescription>
              </Alert>
            ) : null}

            {lastRun && !searchError ? <RunSummary run={lastRun} /> : null}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium">
              Saved Searches
            </CardTitle>
            <p className="text-sm text-muted-foreground">
              Re-run a saved search on demand, or automate it on a schedule.
            </p>
          </CardHeader>
          <CardContent>
            {loadingConfigs ? (
              <div className="flex items-center justify-center py-8 text-muted-foreground">
                <Spinner className="size-5" />
              </div>
            ) : configs.length === 0 ? (
              <p className="py-6 text-center text-sm text-muted-foreground">
                No saved searches yet. Fill in the form above and click{" "}
                <span className="font-medium text-foreground">Save Search</span>{" "}
                to create one you can re-run anytime.
              </p>
            ) : (
              <div className="space-y-3">
                {configs.map((config) => (
                  <div key={config.id} className="rounded-lg border p-4">
                    <div className="flex flex-wrap items-center justify-between gap-3">
                      <div>
                        <div className="flex items-center gap-2">
                          <p className="font-medium">{config.name}</p>
                          {config.is_enabled ? (
                            <Badge className="gap-1">
                              <Zap className="size-3" />
                              Automated ·{" "}
                              {SCHEDULE_LABELS[config.schedule ?? ""] ??
                                config.schedule}
                            </Badge>
                          ) : null}
                        </div>
                        <p className="text-sm text-muted-foreground">
                          {config.business_type} in {config.location}
                          {config.radius_meters
                            ? ` · ${config.radius_meters}m radius`
                            : ""}
                        </p>
                        {config.last_run ? (
                          <p className="mt-1 text-xs text-muted-foreground">
                            Last run: {config.last_run.status}
                            {config.last_run.status === "completed"
                              ? ` — ${config.last_run.new_leads_count} new, ${config.last_run.duplicate_count} duplicate`
                              : ""}
                          </p>
                        ) : (
                          <p className="mt-1 text-xs text-muted-foreground">
                            Not run yet
                          </p>
                        )}
                      </div>
                      <div className="flex flex-wrap items-center gap-2">
                        <Button
                          size="sm"
                          variant="outline"
                          disabled={runningConfigId === config.id}
                          onClick={() => handleRunConfig(config)}
                          className="gap-2"
                        >
                          {runningConfigId === config.id ? (
                            <Spinner className="size-4" />
                          ) : (
                            <Play className="size-4" />
                          )}
                          Run
                        </Button>
                        {config.is_enabled ? (
                          <Button
                            size="sm"
                            variant="outline"
                            disabled={automationBusyId === config.id}
                            onClick={() => handleDisableAutomation(config)}
                            className="gap-2"
                          >
                            {automationBusyId === config.id ? (
                              <Spinner className="size-4" />
                            ) : (
                              <ZapOff className="size-4" />
                            )}
                            Disable Automation
                          </Button>
                        ) : (
                          <>
                            <Select
                              value={scheduleChoice[config.id] ?? "hourly"}
                              onValueChange={(value) =>
                                value &&
                                setScheduleChoice((s) => ({
                                  ...s,
                                  [config.id]: value,
                                }))
                              }
                            >
                              <SelectTrigger size="sm" className="w-[140px]">
                                <SelectValue>
                                  {(value: string) =>
                                    SCHEDULE_LABELS[value] ?? value
                                  }
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
                              variant="outline"
                              disabled={automationBusyId === config.id}
                              onClick={() => handleEnableAutomation(config)}
                              className="gap-2"
                            >
                              {automationBusyId === config.id ? (
                                <Spinner className="size-4" />
                              ) : (
                                <Zap className="size-4" />
                              )}
                              Enable Automation
                            </Button>
                          </>
                        )}
                      </div>
                    </div>
                    {automationError && automationError.id === config.id ? (
                      <Alert variant="destructive" className="mt-3">
                        <AlertCircle className="size-4" />
                        <AlertDescription>
                          {automationError.message}
                        </AlertDescription>
                      </Alert>
                    ) : null}
                    {configRunResult && configRunResult.id === config.id ? (
                      <div className="mt-3">
                        <RunSummary run={configRunResult.run} />
                      </div>
                    ) : null}
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0">
            <div>
              <CardTitle className="text-sm font-medium">
                Leads {total > 0 ? `(${total})` : ""}
              </CardTitle>
              <p className="text-sm text-muted-foreground">
                Everything discovered so far, most recent first.
              </p>
            </div>
          </CardHeader>
          <CardContent>
            {loadingLeads ? (
              <div className="flex items-center justify-center py-10 text-muted-foreground">
                <Spinner className="size-5" />
              </div>
            ) : listError ? (
              <Alert variant="destructive">
                <AlertCircle className="size-4" />
                <AlertTitle>Could not load leads</AlertTitle>
                <AlertDescription>{listError}</AlertDescription>
              </Alert>
            ) : leads.length === 0 ? (
              <p className="py-10 text-center text-sm text-muted-foreground">
                No leads yet. Run a search above to get started.
              </p>
            ) : (
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Business</TableHead>
                      <TableHead>Category</TableHead>
                      <TableHead>Location</TableHead>
                      <TableHead>Phone</TableHead>
                      <TableHead>Website</TableHead>
                      <TableHead>Source</TableHead>
                      <TableHead>Status</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {leads.map((lead) => {
                      return (
                        <TableRow key={lead.id}>
                          <TableCell className="font-medium">
                            {lead.business_name}
                          </TableCell>
                          <TableCell className="text-muted-foreground">
                            {lead.category ?? "—"}
                          </TableCell>
                          <TableCell className="text-muted-foreground">
                            {[lead.city, lead.country].filter(Boolean).join(", ") ||
                              "—"}
                          </TableCell>
                          <TableCell className="text-muted-foreground">
                            {lead.phone ?? "—"}
                          </TableCell>
                          <TableCell>
                            {lead.website ? (
                              <a
                                href={lead.website}
                                target="_blank"
                                rel="noreferrer"
                                className="inline-flex items-center gap-1 text-primary hover:underline"
                              >
                                Visit <ExternalLink className="size-3" />
                              </a>
                            ) : (
                              <span className="text-muted-foreground">—</span>
                            )}
                          </TableCell>
                          <TableCell className="text-muted-foreground">
                            {lead.source}
                          </TableCell>
                          <TableCell>
                            <LeadStatusBadge status={lead.status} />
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

      <Dialog open={saveOpen} onOpenChange={setSaveOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Save this search</DialogTitle>
          </DialogHeader>
          <div className="space-y-1.5">
            <Label htmlFor="save-name">Name</Label>
            <Input
              id="save-name"
              placeholder="e.g. Hotels in Lahore"
              value={saveName}
              onChange={(e) => setSaveName(e.target.value)}
              autoFocus
            />
          </div>
          {saveError ? (
            <Alert variant="destructive">
              <AlertCircle className="size-4" />
              <AlertDescription>{saveError}</AlertDescription>
            </Alert>
          ) : null}
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setSaveOpen(false)}
              disabled={saving}
            >
              Cancel
            </Button>
            <Button
              onClick={handleSaveSearch}
              disabled={saving || !saveName.trim()}
              className="gap-2"
            >
              {saving ? <Spinner className="size-4" /> : null}
              Save
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}

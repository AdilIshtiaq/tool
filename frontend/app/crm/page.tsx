"use client";

import { useCallback, useEffect, useState } from "react";
import { AppHeader } from "@/components/layout/app-header";
import { PageContainer } from "@/components/layout/page-container";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Spinner } from "@/components/ui/spinner";
import { SectionIcon } from "@/components/ui/section-icon";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  getLeadTimeline,
  getLeads,
  type Lead,
  type TimelineEvent,
} from "@/lib/api";
import { History } from "lucide-react";
import { LeadStatusBadge } from "@/components/lead-status-badge";
import { LEAD_STATUS_META, getLeadStatusMeta } from "@/lib/lead-status";

const STAGE_ORDER = Object.keys(LEAD_STATUS_META);

const EVENT_ICON: Record<string, string> = {
  lead_discovered: "🔍",
  qualification: "✅",
  ai_analysis: "🧠",
  recommendation: "💡",
  email: "✉️",
  reply: "↩️",
  call: "📞",
  task: "📋",
  stage_change: "🔀",
};

export default function CRMPage() {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [loading, setLoading] = useState(true);

  const [selectedLead, setSelectedLead] = useState<Lead | null>(null);
  const [timeline, setTimeline] = useState<TimelineEvent[]>([]);
  const [loadingTimeline, setLoadingTimeline] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const res = await getLeads({ page: 1, page_size: 200 });
      setLeads(res.items);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  async function openLead(lead: Lead) {
    setSelectedLead(lead);
    setLoadingTimeline(true);
    try {
      setTimeline(await getLeadTimeline(lead.id));
    } finally {
      setLoadingTimeline(false);
    }
  }

  const stagesPresent = STAGE_ORDER.filter((stage) =>
    leads.some((l) => l.status === stage)
  );
  const otherStages = Array.from(
    new Set(leads.map((l) => l.status).filter((s) => !STAGE_ORDER.includes(s)))
  );
  const allStages = [...stagesPresent, ...otherStages];

  return (
    <>
      <AppHeader title="CRM" description="Pipeline, timeline, and tasks" />
      <PageContainer>
        {loading ? (
          <div className="flex justify-center py-10">
            <Spinner className="size-5" />
          </div>
        ) : leads.length === 0 ? (
          <p className="py-10 text-center text-sm text-muted-foreground">
            No leads yet. Find some in Lead Discovery first.
          </p>
        ) : (
          <div className="flex gap-4 overflow-x-auto pb-4">
            {allStages.map((stage) => {
              const stageLeads = leads.filter((l) => l.status === stage);
              return (
                <div key={stage} className="w-72 shrink-0">
                  <div className="mb-2 flex items-center justify-between px-1">
                    <h3 className="text-sm font-semibold">
                      {getLeadStatusMeta(stage).label}
                    </h3>
                    <Badge variant="secondary">{stageLeads.length}</Badge>
                  </div>
                  <div className="space-y-2">
                    {stageLeads.map((lead) => (
                      <Card
                        key={lead.id}
                        className="cursor-pointer transition-colors hover:bg-muted/50"
                        onClick={() => openLead(lead)}
                      >
                        <CardContent className="p-3">
                          <p className="text-sm font-medium">
                            {lead.business_name}
                          </p>
                          <p className="text-xs text-muted-foreground">
                            {lead.category ?? "—"}
                          </p>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </PageContainer>

      <Dialog
        open={selectedLead !== null}
        onOpenChange={(open) => !open && setSelectedLead(null)}
      >
        <DialogContent className="max-h-[80vh] overflow-y-auto sm:max-w-2xl">
          <DialogHeader>
            <DialogTitle>{selectedLead?.business_name}</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            {selectedLead ? (
              <div className="grid grid-cols-2 gap-2 text-sm">
                <p>
                  <span className="text-muted-foreground">Category: </span>
                  {selectedLead.category ?? "—"}
                </p>
                <p>
                  <span className="text-muted-foreground">Stage: </span>
                  <LeadStatusBadge status={selectedLead.status} />
                </p>
                <p>
                  <span className="text-muted-foreground">Phone: </span>
                  {selectedLead.phone ?? "—"}
                </p>
                <p>
                  <span className="text-muted-foreground">Email: </span>
                  {selectedLead.email ?? "—"}
                </p>
              </div>
            ) : null}

            <Card>
              <CardHeader className="flex-row items-center gap-3 space-y-0">
                <SectionIcon icon={History} color="slate" />
                <CardTitle className="text-base font-semibold">Timeline</CardTitle>
              </CardHeader>
              <CardContent>
                {loadingTimeline ? (
                  <div className="flex justify-center py-6">
                    <Spinner className="size-5" />
                  </div>
                ) : timeline.length === 0 ? (
                  <p className="text-sm text-muted-foreground">No activity yet.</p>
                ) : (
                  <div className="space-y-3">
                    {timeline.map((event, i) => (
                      <div key={i} className="flex gap-3 text-sm">
                        <span>{EVENT_ICON[event.type] ?? "•"}</span>
                        <div>
                          <p>{event.summary}</p>
                          <p className="text-xs text-muted-foreground">
                            {new Date(event.timestamp).toLocaleString()}
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
}

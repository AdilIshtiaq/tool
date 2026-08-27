import { AppHeader } from "@/components/layout/app-header";
import { PageContainer } from "@/components/layout/page-container";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  getApiHealth,
  getDashboardStats,
  getDbHealth,
  getRecentActivity,
  type DashboardStats,
  type HealthStatus,
  type RecentActivityItem,
} from "@/lib/api";
import { LeadStatusBadge } from "@/components/lead-status-badge";
import { getLeadStatusMeta } from "@/lib/lead-status";
import {
  CheckCircle2,
  ClipboardList,
  HelpCircle,
  Mail,
  PhoneCall,
  Radio,
  ShieldCheck,
  ThumbsDown,
  ThumbsUp,
  Trophy,
  Users,
  XCircle,
} from "lucide-react";

async function safeCheck(check: () => Promise<HealthStatus>): Promise<HealthStatus> {
  try {
    return await check();
  } catch (error) {
    return { status: "error", detail: (error as Error).message };
  }
}

function StatCard({
  title,
  value,
  icon: Icon,
  tone = "default",
}: {
  title: string;
  value: number;
  icon: typeof Users;
  tone?: "default" | "positive" | "negative";
}) {
  const iconClasses =
    tone === "positive"
      ? "bg-primary/10 text-primary"
      : tone === "negative"
        ? "bg-destructive/10 text-destructive"
        : "bg-muted text-muted-foreground";
  return (
    <Card>
      <CardContent className="flex items-center justify-between p-4">
        <div>
          <p className="text-xs text-muted-foreground">{title}</p>
          <p className="mt-1 text-2xl font-semibold tabular-nums">{value}</p>
        </div>
        <div className={`flex h-9 w-9 items-center justify-center rounded-lg ${iconClasses}`}>
          <Icon className="size-4.5" />
        </div>
      </CardContent>
    </Card>
  );
}

function StatusRow({ title, result }: { title: string; result: HealthStatus }) {
  const ok = result.status === "ok";
  return (
    <div className="flex items-center justify-between rounded-md border px-3 py-2 text-sm">
      <span>{title}</span>
      <div className="flex items-center gap-2">
        {ok ? (
          <CheckCircle2 className="size-4 text-emerald-500" />
        ) : (
          <XCircle className="size-4 text-destructive" />
        )}
        <Badge variant={ok ? "default" : "destructive"}>{ok ? "Online" : "Offline"}</Badge>
      </div>
    </div>
  );
}

type FunnelStage = { label: string; value: number };

function PipelineFunnel({ stats }: { stats: DashboardStats }) {
  const stages: FunnelStage[] = [
    { label: "New", value: stats.total_leads },
    { label: "Qualified", value: stats.qualified },
    { label: "Contacted", value: stats.contacted },
    { label: "Meetings", value: stats.meetings },
    { label: "Won", value: stats.won },
  ];
  const baseline = stages[0].value || 1;
  const maxBarHeight = 140;

  return (
    <div className="grid grid-cols-5 items-end gap-3 pt-4" style={{ height: maxBarHeight + 70 }}>
      {stages.map((stage, i) => {
        const pct = Math.round((stage.value / baseline) * 100);
        const barHeight = Math.max((stage.value / baseline) * maxBarHeight, stage.value > 0 ? 6 : 2);
        const opacity = 1 - i * 0.15;
        return (
          <div key={stage.label} className="flex h-full flex-col justify-end">
            <div className="mb-2">
              <p className="text-[11px] text-muted-foreground">{stage.label}</p>
              <p className="text-sm font-semibold tabular-nums">{pct}%</p>
              <p className="text-[11px] text-muted-foreground tabular-nums">{stage.value}</p>
            </div>
            <div
              className="w-full rounded-md bg-primary"
              style={{ height: barHeight, opacity }}
            />
          </div>
        );
      })}
    </div>
  );
}

function ActivityRow({ item }: { item: RecentActivityItem }) {
  return (
    <div className="flex items-center justify-between gap-3 py-2 text-sm">
      <div className="min-w-0">
        <p className="truncate font-medium">{item.business_name}</p>
        <div className="mt-0.5 flex items-center gap-1.5 text-xs text-muted-foreground">
          {item.old_stage ? (
            <>
              <span>{getLeadStatusMeta(item.old_stage).label}</span>
              <span>&rarr;</span>
            </>
          ) : null}
          <LeadStatusBadge status={item.new_stage} />
        </div>
      </div>
      <span className="shrink-0 text-xs text-muted-foreground">
        {new Date(item.changed_at).toLocaleString(undefined, {
          month: "short",
          day: "numeric",
          hour: "numeric",
          minute: "2-digit",
        })}
      </span>
    </div>
  );
}

export default async function DashboardPage() {
  const [apiHealth, dbHealth, statsResult, activity] = await Promise.all([
    safeCheck(getApiHealth),
    safeCheck(getDbHealth),
    getDashboardStats().catch(() => null as DashboardStats | null),
    getRecentActivity().catch(() => [] as RecentActivityItem[]),
  ]);

  const stats = statsResult;

  const pipelineCards = stats
    ? [
        { title: "Total Leads", value: stats.total_leads, icon: Users, tone: "default" as const },
        { title: "New Leads", value: stats.new_leads, icon: Radio, tone: "default" as const },
        { title: "Qualified", value: stats.qualified, icon: ShieldCheck, tone: "positive" as const },
        { title: "Needs Review", value: stats.needs_review, icon: HelpCircle, tone: "default" as const },
        { title: "Contacted", value: stats.contacted, icon: Mail, tone: "default" as const },
      ]
    : [];

  const outcomeCards = stats
    ? [
        { title: "Replies", value: stats.replies, icon: Mail, tone: "default" as const },
        { title: "Meetings", value: stats.meetings, icon: PhoneCall, tone: "positive" as const },
        { title: "Won", value: stats.won, icon: Trophy, tone: "positive" as const },
        { title: "Lost", value: stats.lost, icon: ThumbsDown, tone: "negative" as const },
      ]
    : [];

  const opsCards = stats
    ? [
        { title: "Due Tasks", value: stats.due_tasks, icon: ClipboardList, tone: "default" as const },
        {
          title: "Active Automations",
          value: stats.active_automation_runs,
          icon: ThumbsUp,
          tone: "default" as const,
        },
      ]
    : [];

  return (
    <>
      <AppHeader
        title="Dashboard"
        description="Real-time overview of the sales pipeline"
      />
      <PageContainer>
        {stats ? (
          <>
            <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-5">
              {pipelineCards.map((card) => (
                <StatCard key={card.title} {...card} />
              ))}
            </div>

            <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
              <Card className="lg:col-span-2">
                <CardHeader>
                  <CardTitle className="text-sm font-medium">Pipeline Funnel</CardTitle>
                  <p className="text-sm text-muted-foreground">
                    Share of all leads reaching each stage.
                  </p>
                </CardHeader>
                <CardContent>
                  <PipelineFunnel stats={stats} />
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="text-sm font-medium">Recent Activity</CardTitle>
                  <p className="text-sm text-muted-foreground">
                    Latest pipeline stage changes.
                  </p>
                </CardHeader>
                <CardContent className="divide-y">
                  {activity.length === 0 ? (
                    <p className="py-6 text-center text-sm text-muted-foreground">
                      No activity yet.
                    </p>
                  ) : (
                    activity.map((item, i) => (
                      <ActivityRow key={`${item.lead_id}-${item.changed_at}-${i}`} item={item} />
                    ))
                  )}
                </CardContent>
              </Card>
            </div>

            <div className="grid grid-cols-2 gap-4 sm:grid-cols-4 lg:grid-cols-6">
              {outcomeCards.map((card) => (
                <StatCard key={card.title} {...card} />
              ))}
              {opsCards.map((card) => (
                <StatCard key={card.title} {...card} />
              ))}
            </div>
          </>
        ) : (
          <p className="text-sm text-muted-foreground">
            Could not load dashboard stats from the backend.
          </p>
        )}

        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium">System Status</CardTitle>
          </CardHeader>
          <CardContent className="grid grid-cols-1 gap-2 sm:grid-cols-3">
            <StatusRow title="FastAPI Backend" result={apiHealth} />
            <StatusRow title="PostgreSQL Database" result={dbHealth} />
            <StatusRow title="Next.js Frontend" result={{ status: "ok" }} />
          </CardContent>
        </Card>
      </PageContainer>
    </>
  );
}

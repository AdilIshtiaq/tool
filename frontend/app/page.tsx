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
import { SectionIcon } from "@/components/ui/section-icon";
import { getLeadStatusMeta } from "@/lib/lead-status";
import {
  Activity,
  CalendarDays,
  CheckCircle2,
  ClipboardList,
  HelpCircle,
  Mail,
  PhoneCall,
  Radio,
  Server,
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

const statColorClasses = {
  blue: "bg-blue-100 text-blue-600 dark:bg-blue-500/15 dark:text-blue-400",
  indigo: "bg-indigo-100 text-indigo-600 dark:bg-indigo-500/15 dark:text-indigo-400",
  violet: "bg-violet-100 text-violet-600 dark:bg-violet-500/15 dark:text-violet-400",
  emerald: "bg-emerald-100 text-emerald-600 dark:bg-emerald-500/15 dark:text-emerald-400",
  amber: "bg-amber-100 text-amber-600 dark:bg-amber-500/15 dark:text-amber-400",
  rose: "bg-rose-100 text-rose-600 dark:bg-rose-500/15 dark:text-rose-400",
  slate: "bg-slate-100 text-slate-600 dark:bg-slate-500/15 dark:text-slate-400",
} as const;

type StatColor = keyof typeof statColorClasses;

function StatCard({
  title,
  value,
  icon: Icon,
  color = "slate",
}: {
  title: string;
  value: number;
  icon: typeof Users;
  color?: StatColor;
}) {
  return (
    <Card>
      <CardContent className="flex items-start justify-between gap-3 p-4">
        <div className="min-w-0">
          <p className="truncate text-sm font-medium text-muted-foreground">{title}</p>
          <p className="mt-1.5 text-3xl font-bold tabular-nums">{value.toLocaleString()}</p>
        </div>
        <div className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-lg ${statColorClasses[color]}`}>
          <Icon className="size-5" />
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

type FunnelStage = { label: string; value: number; barClass: string };

const FUNNEL_BAR_CLASSES = [
  "bg-blue-500",
  "bg-indigo-500",
  "bg-violet-500",
  "bg-amber-500",
  "bg-emerald-500",
];

function PipelineFunnel({ stats }: { stats: DashboardStats }) {
  const stages: FunnelStage[] = [
    { label: "New", value: stats.total_leads, barClass: FUNNEL_BAR_CLASSES[0] },
    { label: "Qualified", value: stats.qualified, barClass: FUNNEL_BAR_CLASSES[1] },
    { label: "Contacted", value: stats.contacted, barClass: FUNNEL_BAR_CLASSES[2] },
    { label: "Meetings", value: stats.meetings, barClass: FUNNEL_BAR_CLASSES[3] },
    { label: "Won", value: stats.won, barClass: FUNNEL_BAR_CLASSES[4] },
  ];
  const baseline = stages[0].value || 1;
  const maxBarHeight = 140;

  return (
    <div className="overflow-x-auto">
      <div
        className="grid grid-cols-5 items-end gap-3 pt-4"
        style={{ height: maxBarHeight + 70, minWidth: 380 }}
      >
        {stages.map((stage) => {
          const pct = Math.round((stage.value / baseline) * 100);
          const barHeight = Math.max((stage.value / baseline) * maxBarHeight, stage.value > 0 ? 6 : 2);
          return (
            <div key={stage.label} className="flex h-full flex-col justify-end">
              <div className="mb-2">
                <p className="whitespace-nowrap text-[11px] text-muted-foreground">{stage.label}</p>
                <p className="text-sm font-semibold tabular-nums">{pct}%</p>
                <p className="text-[11px] text-muted-foreground tabular-nums">{stage.value}</p>
              </div>
              <div
                className={`w-full rounded-md ${stage.barClass}`}
                style={{ height: barHeight }}
              />
            </div>
          );
        })}
      </div>
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
        { title: "Total Leads", value: stats.total_leads, icon: Users, color: "blue" as const },
        { title: "New Leads", value: stats.new_leads, icon: Radio, color: "indigo" as const },
        { title: "Qualified", value: stats.qualified, icon: ShieldCheck, color: "emerald" as const },
        { title: "Needs Review", value: stats.needs_review, icon: HelpCircle, color: "amber" as const },
        { title: "Contacted", value: stats.contacted, icon: Mail, color: "violet" as const },
      ]
    : [];

  const outcomeCards = stats
    ? [
        { title: "Replies", value: stats.replies, icon: Mail, color: "blue" as const },
        { title: "Meetings", value: stats.meetings, icon: PhoneCall, color: "violet" as const },
        { title: "Won", value: stats.won, icon: Trophy, color: "emerald" as const },
        { title: "Lost", value: stats.lost, icon: ThumbsDown, color: "rose" as const },
      ]
    : [];

  const opsCards = stats
    ? [
        { title: "Due Tasks", value: stats.due_tasks, icon: ClipboardList, color: "slate" as const },
        {
          title: "Active Automations",
          value: stats.active_automation_runs,
          icon: ThumbsUp,
          color: "amber" as const,
        },
      ]
    : [];

  const today = new Date().toLocaleDateString(undefined, {
    weekday: "long",
    year: "numeric",
    month: "long",
    day: "numeric",
  });

  return (
    <>
      <AppHeader
        title="Dashboard"
        description="Real-time overview of the sales pipeline"
        actions={
          <div className="hidden items-center gap-2 rounded-lg border bg-card px-3 py-2 shadow-sm sm:inline-flex">
            <CalendarDays className="size-4 text-muted-foreground" />
            <span className="text-sm font-medium">{today}</span>
          </div>
        }
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
                <CardHeader className="flex-row items-center gap-3 space-y-0">
                  <SectionIcon icon={Activity} color="blue" />
                  <div>
                    <CardTitle className="text-base font-semibold">Pipeline Funnel</CardTitle>
                    <p className="text-sm text-muted-foreground">
                      Share of all leads reaching each stage.
                    </p>
                  </div>
                </CardHeader>
                <CardContent>
                  <PipelineFunnel stats={stats} />
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex-row items-center gap-3 space-y-0">
                  <SectionIcon icon={Radio} color="violet" />
                  <div>
                    <CardTitle className="text-base font-semibold">Recent Activity</CardTitle>
                    <p className="text-sm text-muted-foreground">
                      Latest pipeline stage changes.
                    </p>
                  </div>
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
          <CardHeader className="flex-row items-center gap-3 space-y-0">
            <SectionIcon icon={Server} color="slate" />
            <CardTitle className="text-base font-semibold">System Status</CardTitle>
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

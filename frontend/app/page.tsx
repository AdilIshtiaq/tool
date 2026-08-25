import { AppHeader } from "@/components/layout/app-header";
import { PageContainer } from "@/components/layout/page-container";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  getApiHealth,
  getDashboardStats,
  getDbHealth,
  type DashboardStats,
  type HealthStatus,
} from "@/lib/api";
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
}: {
  title: string;
  value: number;
  icon: typeof Users;
}) {
  return (
    <Card>
      <CardContent className="flex items-center justify-between p-4">
        <div>
          <p className="text-xs text-muted-foreground">{title}</p>
          <p className="mt-1 text-2xl font-semibold tabular-nums">{value}</p>
        </div>
        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-muted">
          <Icon className="size-4.5 text-muted-foreground" />
        </div>
      </CardContent>
    </Card>
  );
}

function StatusRow({
  title,
  result,
}: {
  title: string;
  result: HealthStatus;
}) {
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
        <Badge variant={ok ? "default" : "destructive"}>
          {ok ? "Online" : "Offline"}
        </Badge>
      </div>
    </div>
  );
}

export default async function DashboardPage() {
  const [apiHealth, dbHealth, statsResult] = await Promise.all([
    safeCheck(getApiHealth),
    safeCheck(getDbHealth),
    getDashboardStats().catch(() => null as DashboardStats | null),
  ]);

  const stats = statsResult;

  const cards = stats
    ? [
        { title: "Total Leads", value: stats.total_leads, icon: Users },
        { title: "New Leads", value: stats.new_leads, icon: Radio },
        { title: "Qualified", value: stats.qualified, icon: ShieldCheck },
        { title: "Needs Review", value: stats.needs_review, icon: HelpCircle },
        { title: "Contacted", value: stats.contacted, icon: Mail },
        { title: "Replies", value: stats.replies, icon: Mail },
        { title: "Meetings", value: stats.meetings, icon: PhoneCall },
        { title: "Won", value: stats.won, icon: Trophy },
        { title: "Lost", value: stats.lost, icon: ThumbsDown },
        { title: "Due Tasks", value: stats.due_tasks, icon: ClipboardList },
        {
          title: "Active Automations",
          value: stats.active_automation_runs,
          icon: ThumbsUp,
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
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5">
            {cards.map((card) => (
              <StatCard key={card.title} {...card} />
            ))}
          </div>
        ) : (
          <p className="text-sm text-muted-foreground">
            Could not load dashboard stats from the backend.
          </p>
        )}

        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium">
              System Status
            </CardTitle>
          </CardHeader>
          <CardContent className="grid grid-cols-1 gap-2 sm:grid-cols-3">
            <StatusRow title="FastAPI Backend" result={apiHealth} />
            <StatusRow title="PostgreSQL Database" result={dbHealth} />
            <StatusRow
              title="Next.js Frontend"
              result={{ status: "ok" }}
            />
          </CardContent>
        </Card>
      </PageContainer>
    </>
  );
}

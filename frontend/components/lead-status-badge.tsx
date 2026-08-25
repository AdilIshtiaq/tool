import { Badge } from "@/components/ui/badge";
import { getLeadStatusMeta } from "@/lib/lead-status";

export function LeadStatusBadge({ status }: { status: string }) {
  const meta = getLeadStatusMeta(status);
  return <Badge variant={meta.variant}>{meta.label}</Badge>;
}

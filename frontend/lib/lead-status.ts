export type BadgeVariant = "default" | "destructive" | "secondary" | "outline";

export const LEAD_STATUS_META: Record<string, { label: string; variant: BadgeVariant }> = {
  new: { label: "New", variant: "outline" },
  qualified: { label: "Qualified", variant: "default" },
  not_qualified: { label: "Not Qualified", variant: "destructive" },
  needs_review: { label: "Needs Review", variant: "secondary" },
  analyzed: { label: "Analyzed", variant: "secondary" },
  contacted: { label: "Contacted", variant: "secondary" },
  interested: { label: "Interested", variant: "default" },
  follow_up: { label: "Follow-up", variant: "secondary" },
  meeting: { label: "Meeting", variant: "default" },
  proposal: { label: "Proposal", variant: "default" },
  won: { label: "Won", variant: "default" },
  lost: { label: "Lost", variant: "destructive" },
};

/** Falls back gracefully for any status value not in the map above, so a
 * newly-introduced backend status never renders as blank or crashes the page. */
export function getLeadStatusMeta(status: string) {
  return (
    LEAD_STATUS_META[status] ?? {
      label: status
        .split("_")
        .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
        .join(" "),
      variant: "outline" as BadgeVariant,
    }
  );
}

/** Turns any snake_case or lowercase system value (message status, call
 * outcome, etc.) into readable Title Case for display — e.g.
 * "accepted_by_provider" -> "Accepted By Provider". */
export function humanize(value: string): string {
  return value
    .split(/[_\s]+/)
    .map((w) => (w ? w.charAt(0).toUpperCase() + w.slice(1) : w))
    .join(" ");
}

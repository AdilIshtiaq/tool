import type { LucideIcon } from "lucide-react";

const sectionColorClasses = {
  blue: "bg-blue-100 text-blue-600 dark:bg-blue-500/15 dark:text-blue-400",
  indigo: "bg-indigo-100 text-indigo-600 dark:bg-indigo-500/15 dark:text-indigo-400",
  violet: "bg-violet-100 text-violet-600 dark:bg-violet-500/15 dark:text-violet-400",
  emerald: "bg-emerald-100 text-emerald-600 dark:bg-emerald-500/15 dark:text-emerald-400",
  amber: "bg-amber-100 text-amber-600 dark:bg-amber-500/15 dark:text-amber-400",
  rose: "bg-rose-100 text-rose-600 dark:bg-rose-500/15 dark:text-rose-400",
  slate: "bg-slate-100 text-slate-600 dark:bg-slate-500/15 dark:text-slate-400",
} as const;

export type SectionIconColor = keyof typeof sectionColorClasses;

export function SectionIcon({
  icon: Icon,
  color = "violet",
}: {
  icon: LucideIcon;
  color?: SectionIconColor;
}) {
  return (
    <div
      className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-lg ${sectionColorClasses[color]}`}
    >
      <Icon className="size-4.5" />
    </div>
  );
}

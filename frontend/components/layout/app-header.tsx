import { SidebarTrigger } from "@/components/ui/sidebar";
import { Separator } from "@/components/ui/separator";

export function AppHeader({
  title,
  description,
  actions,
}: {
  title: string;
  description?: string;
  actions?: React.ReactNode;
}) {
  return (
    <header className="sticky top-0 z-10 flex h-[72px] shrink-0 items-center gap-3 border-b bg-card/95 px-6 backdrop-blur supports-backdrop-filter:bg-card/80 md:px-8">
      <SidebarTrigger className="-ml-1" />
      <Separator orientation="vertical" className="h-6" />
      <div className="flex min-w-0 flex-1 flex-col justify-center">
        <h1 className="truncate text-lg font-semibold leading-tight tracking-tight">
          {title}
        </h1>
        {description ? (
          <p className="mt-0.5 truncate text-sm text-muted-foreground">
            {description}
          </p>
        ) : null}
      </div>
      {actions ? (
        <div className="flex shrink-0 items-center gap-2">{actions}</div>
      ) : null}
    </header>
  );
}

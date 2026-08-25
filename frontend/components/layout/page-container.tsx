import { cn } from "@/lib/utils";

export function PageContainer({
  className,
  children,
}: {
  className?: string;
  children: React.ReactNode;
}) {
  return (
    <div
      className={cn(
        "mx-auto flex w-full max-w-[1400px] flex-1 flex-col gap-6 px-6 py-6 md:px-8 md:py-8",
        className
      )}
    >
      {children}
    </div>
  );
}

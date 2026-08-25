import { AppHeader } from "@/components/layout/app-header";
import { PageContainer } from "@/components/layout/page-container";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Construction } from "lucide-react";

export function PhasePlaceholder({
  title,
  description,
  phase,
}: {
  title: string;
  description: string;
  phase: string;
}) {
  return (
    <>
      <AppHeader title={title} description={description} />
      <PageContainer>
        <Card>
          <CardHeader className="flex flex-row items-center gap-3 space-y-0">
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-muted">
              <Construction className="h-4.5 w-4.5 text-muted-foreground" />
            </div>
            <CardTitle className="text-sm font-medium">
              Not yet implemented
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              This module is part of {phase} of the implementation plan and
              has not been built yet. No backend functionality exists behind
              this page.
            </p>
          </CardContent>
        </Card>
      </PageContainer>
    </>
  );
}

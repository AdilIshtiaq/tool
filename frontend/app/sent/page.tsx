"use client";

import { useCallback, useEffect, useState } from "react";
import { AppHeader } from "@/components/layout/app-header";
import { PageContainer } from "@/components/layout/page-container";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Spinner } from "@/components/ui/spinner";
import {
  getCampaigns,
  getLeads,
  getMessages,
  type Campaign,
  type InboundMessage,
  type Lead,
} from "@/lib/api";
import { humanize } from "@/lib/lead-status";
import { Mail, Megaphone, TestTube } from "lucide-react";

export default function SentMailPage() {
  const [messages, setMessages] = useState<InboundMessage[]>([]);
  const [leads, setLeads] = useState<Lead[]>([]);
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [msgs, leadRes, campaignRes] = await Promise.all([
        getMessages({ direction: "outbound", limit: 200 }),
        getLeads({ page: 1, page_size: 200 }),
        getCampaigns(),
      ]);
      setMessages(msgs);
      setLeads(leadRes.items);
      setCampaigns(campaignRes);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  function leadName(leadId: string) {
    return leads.find((l) => l.id === leadId)?.business_name ?? leadId;
  }

  function campaignName(campaignId: string | null) {
    if (!campaignId) return null;
    return campaigns.find((c) => c.id === campaignId)?.name ?? null;
  }

  const sentCount = messages.filter((m) => m.status === "accepted_by_provider").length;

  return (
    <>
      <AppHeader
        title="Sent Mail"
        description="Every outreach email actually sent, one-off or via a campaign"
      />
      <PageContainer>
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium">
              Sent Mail {messages.length > 0 ? `(${messages.length})` : ""}
            </CardTitle>
            <p className="text-sm text-muted-foreground">
              {sentCount} accepted for delivery
              {messages.length !== sentCount ? `, ${messages.length - sentCount} other` : ""}.
            </p>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="flex justify-center py-10">
                <Spinner className="size-5" />
              </div>
            ) : messages.length === 0 ? (
              <p className="py-10 text-center text-sm text-muted-foreground">
                No outreach emails sent yet.
              </p>
            ) : (
              <div className="space-y-3">
                {messages.map((message) => (
                  <div key={message.id} className="rounded-lg border p-4">
                    <div className="flex flex-wrap items-center justify-between gap-3">
                      <div>
                        <p className="font-medium">
                          {leadName(message.lead_id)} — {message.subject}
                        </p>
                        <p className="text-sm text-muted-foreground">
                          To: {message.to_email ?? "—"}
                          {message.sent_at
                            ? ` · ${new Date(message.sent_at).toLocaleString()}`
                            : ""}
                        </p>
                      </div>
                      <div className="flex items-center gap-2">
                        {message.is_test ? (
                          <Badge variant="secondary" className="gap-1">
                            <TestTube className="size-3" />
                            Test
                          </Badge>
                        ) : null}
                        {campaignName(message.campaign_id) ? (
                          <Badge variant="outline" className="gap-1">
                            <Megaphone className="size-3" />
                            {campaignName(message.campaign_id)}
                          </Badge>
                        ) : (
                          <Badge variant="outline" className="gap-1">
                            <Mail className="size-3" />
                            Manual
                          </Badge>
                        )}
                        <Badge
                          variant={
                            message.status === "accepted_by_provider"
                              ? "default"
                              : "destructive"
                          }
                        >
                          {humanize(message.status)}
                        </Badge>
                      </div>
                    </div>
                    <p className="mt-2 whitespace-pre-wrap text-sm text-muted-foreground">
                      {message.body}
                    </p>
                    {message.provider_response ? (
                      <p className="mt-1 text-xs text-muted-foreground">
                        {message.provider_response}
                      </p>
                    ) : null}
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </PageContainer>
    </>
  );
}

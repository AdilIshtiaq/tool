"use client";

import { useCallback, useEffect, useState } from "react";
import { AppHeader } from "@/components/layout/app-header";
import { PageContainer } from "@/components/layout/page-container";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Spinner } from "@/components/ui/spinner";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  classifyReplyMessage,
  fetchInboundReplies,
  getLeads,
  getMessages,
  recordReply,
  type InboundMessage,
  type Lead,
} from "@/lib/api";
import { AlertCircle, Mail, RefreshCw, Sparkles } from "lucide-react";

const CATEGORY_VARIANT: Record<string, "default" | "destructive" | "secondary"> = {
  Positive: "default",
  Interested: "default",
  Question: "secondary",
  "Follow-up": "secondary",
  Neutral: "secondary",
  Negative: "destructive",
  Unsubscribe: "destructive",
  "Out of office": "secondary",
  Invalid: "destructive",
};

export default function RepliesPage() {
  const [messages, setMessages] = useState<InboundMessage[]>([]);
  const [leads, setLeads] = useState<Lead[]>([]);
  const [loading, setLoading] = useState(true);
  const [classifyingId, setClassifyingId] = useState<string | null>(null);
  const [classifyErrors, setClassifyErrors] = useState<Record<string, string>>({});

  const [fetching, setFetching] = useState(false);
  const [fetchResult, setFetchResult] = useState<Awaited<
    ReturnType<typeof fetchInboundReplies>
  > | null>(null);
  const [fetchError, setFetchError] = useState<string | null>(null);

  const [recordOpen, setRecordOpen] = useState(false);
  const [recordLeadId, setRecordLeadId] = useState("");
  const [recordFrom, setRecordFrom] = useState("");
  const [recordSubject, setRecordSubject] = useState("");
  const [recordBody, setRecordBody] = useState("");
  const [recording, setRecording] = useState(false);
  const [recordError, setRecordError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [msgs, leadRes] = await Promise.all([
        getMessages({ direction: "inbound", limit: 100 }),
        getLeads({ page: 1, page_size: 100 }),
      ]);
      setMessages(msgs);
      setLeads(leadRes.items);
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

  async function handleClassify(message: InboundMessage) {
    setClassifyingId(message.id);
    setClassifyErrors((e) => ({ ...e, [message.id]: "" }));
    try {
      const updated = await classifyReplyMessage(message.id);
      setMessages((ms) => ms.map((m) => (m.id === updated.id ? updated : m)));
    } catch (error) {
      setClassifyErrors((e) => ({ ...e, [message.id]: (error as Error).message }));
    } finally {
      setClassifyingId(null);
    }
  }

  async function handleFetchInbound() {
    setFetching(true);
    setFetchError(null);
    setFetchResult(null);
    try {
      const result = await fetchInboundReplies();
      setFetchResult(result);
      await load();
    } catch (error) {
      setFetchError((error as Error).message);
    } finally {
      setFetching(false);
    }
  }

  async function handleRecordReply() {
    if (!recordLeadId || !recordFrom.trim() || !recordSubject.trim() || !recordBody.trim())
      return;
    setRecording(true);
    setRecordError(null);
    try {
      await recordReply(recordLeadId, {
        from_email: recordFrom.trim(),
        subject: recordSubject.trim(),
        body: recordBody.trim(),
      });
      setRecordOpen(false);
      setRecordFrom("");
      setRecordSubject("");
      setRecordBody("");
      await load();
    } catch (error) {
      setRecordError((error as Error).message);
    } finally {
      setRecording(false);
    }
  }

  return (
    <>
      <AppHeader
        title="Replies"
        description="Reply tracking and follow-up"
      />
      <PageContainer>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0">
            <CardTitle className="text-sm font-medium">
              Inbox Polling
            </CardTitle>
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setRecordOpen(true)}
                className="gap-2"
              >
                <Mail className="size-4" />
                Record a Reply
              </Button>
              <Button
                size="sm"
                disabled={fetching}
                onClick={handleFetchInbound}
                className="gap-2"
              >
                {fetching ? (
                  <Spinner className="size-4" />
                ) : (
                  <RefreshCw className="size-4" />
                )}
                Check Inbox Now
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              Automatically polls the connected mailbox for new replies every
              10 minutes via n8n. Use "Check Inbox Now" to poll immediately, or
              "Record a Reply" to manually log one for testing.
            </p>
            {fetchError ? (
              <Alert variant="destructive" className="mt-3">
                <AlertCircle className="size-4" />
                <AlertTitle>Inbox check failed</AlertTitle>
                <AlertDescription>{fetchError}</AlertDescription>
              </Alert>
            ) : null}
            {fetchResult ? (
              <Alert className="mt-3">
                <RefreshCw className="size-4" />
                <AlertTitle>Inbox checked</AlertTitle>
                <AlertDescription>
                  {fetchResult.fetched} email(s) found — {fetchResult.matched}{" "}
                  matched to leads, {fetchResult.unmatched} unmatched,{" "}
                  {fetchResult.classified} classified
                  {fetchResult.classification_errors > 0
                    ? `, ${fetchResult.classification_errors} classification error(s)`
                    : ""}
                  .
                </AlertDescription>
              </Alert>
            ) : null}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium">
              Replies {messages.length > 0 ? `(${messages.length})` : ""}
            </CardTitle>
            <p className="text-sm text-muted-foreground">
              Classify each reply to see the sender's intent and a suggested
              next step.
            </p>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="flex justify-center py-10">
                <Spinner className="size-5" />
              </div>
            ) : messages.length === 0 ? (
              <p className="py-10 text-center text-sm text-muted-foreground">
                No replies yet.
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
                          From: {message.from_email}
                        </p>
                      </div>
                      {message.category ? (
                        <div className="flex items-center gap-2">
                          <Badge variant={CATEGORY_VARIANT[message.category] ?? "secondary"}>
                            {message.category}
                          </Badge>
                          {message.review_required ? (
                            <Badge variant="outline">Needs Review</Badge>
                          ) : null}
                        </div>
                      ) : (
                        <Button
                          size="sm"
                          variant="outline"
                          disabled={classifyingId === message.id}
                          onClick={() => handleClassify(message)}
                          className="gap-2"
                        >
                          {classifyingId === message.id ? (
                            <Spinner className="size-4" />
                          ) : (
                            <Sparkles className="size-4" />
                          )}
                          Classify
                        </Button>
                      )}
                    </div>
                    <p className="mt-2 whitespace-pre-wrap text-sm text-muted-foreground">
                      {message.body}
                    </p>
                    {classifyErrors[message.id] ? (
                      <Alert variant="destructive" className="mt-2">
                        <AlertCircle className="size-4" />
                        <AlertDescription>
                          {classifyErrors[message.id]}
                        </AlertDescription>
                      </Alert>
                    ) : null}
                    {message.classification_summary ? (
                      <div className="mt-2 rounded-md bg-muted/40 p-2 text-sm">
                        <p>{message.classification_summary}</p>
                        {message.suggested_action ? (
                          <p className="mt-1">
                            <span className="font-medium">Suggested action: </span>
                            {message.suggested_action}
                          </p>
                        ) : null}
                        {message.classification_confidence !== null ? (
                          <p className="mt-1 text-xs text-muted-foreground">
                            Confidence: {Math.round(message.classification_confidence * 100)}%
                          </p>
                        ) : null}
                      </div>
                    ) : null}
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </PageContainer>

      <Dialog open={recordOpen} onOpenChange={setRecordOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Record a Reply</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-1.5">
              <Label>Lead</Label>
              <Select value={recordLeadId} onValueChange={setRecordLeadId}>
                <SelectTrigger className="w-full">
                  <SelectValue placeholder="Choose a lead">
                    {(value: string) => leadName(value)}
                  </SelectValue>
                </SelectTrigger>
                <SelectContent>
                  {leads.map((lead) => (
                    <SelectItem key={lead.id} value={lead.id}>
                      {lead.business_name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="record-from">From email</Label>
              <Input
                id="record-from"
                type="email"
                value={recordFrom}
                onChange={(e) => setRecordFrom(e.target.value)}
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="record-subject">Subject</Label>
              <Input
                id="record-subject"
                value={recordSubject}
                onChange={(e) => setRecordSubject(e.target.value)}
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="record-body">Body</Label>
              <Textarea
                id="record-body"
                rows={5}
                value={recordBody}
                onChange={(e) => setRecordBody(e.target.value)}
              />
            </div>
            {recordError ? (
              <Alert variant="destructive">
                <AlertCircle className="size-4" />
                <AlertDescription>{recordError}</AlertDescription>
              </Alert>
            ) : null}
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setRecordOpen(false)}
              disabled={recording}
            >
              Cancel
            </Button>
            <Button
              onClick={handleRecordReply}
              disabled={
                recording ||
                !recordLeadId ||
                !recordFrom.trim() ||
                !recordSubject.trim() ||
                !recordBody.trim()
              }
              className="gap-2"
            >
              {recording ? <Spinner className="size-4" /> : null}
              Save
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}

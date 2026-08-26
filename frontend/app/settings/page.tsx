"use client";

import { useCallback, useEffect, useState } from "react";
import { AppHeader } from "@/components/layout/app-header";
import { PageContainer } from "@/components/layout/page-container";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Spinner } from "@/components/ui/spinner";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import {
  getSettings,
  updateSettings,
  type Settings,
  type SettingsUpdate,
} from "@/lib/api";
import { AlertCircle, CheckCircle2, KeyRound, Mail } from "lucide-react";

type KeyField =
  | "google_places_api_key"
  | "openai_api_key"
  | "anthropic_api_key"
  | "gemini_api_key";

const KEY_FIELDS: { field: KeyField; label: string; hint: string }[] = [
  {
    field: "google_places_api_key",
    label: "Google Places API Key",
    hint: "Powers Lead Discovery search.",
  },
  {
    field: "openai_api_key",
    label: "OpenAI API Key",
    hint: "First provider tried for analysis, email drafts, call scripts, and reply classification.",
  },
  {
    field: "anthropic_api_key",
    label: "Anthropic API Key",
    hint: "Used automatically if OpenAI fails or is out of credits.",
  },
  {
    field: "gemini_api_key",
    label: "Gemini API Key",
    hint: "Used automatically if OpenAI and Anthropic both fail.",
  },
];

const EMPTY_KEY_INPUTS: Record<KeyField, string> = {
  google_places_api_key: "",
  openai_api_key: "",
  anthropic_api_key: "",
  gemini_api_key: "",
};

type FormMessage = { type: "success" | "error"; text: string };

export default function SettingsPage() {
  const [settings, setSettings] = useState<Settings | null>(null);
  const [loading, setLoading] = useState(true);

  const [keyInputs, setKeyInputs] = useState<Record<KeyField, string>>(EMPTY_KEY_INPUTS);
  const [savingKeys, setSavingKeys] = useState(false);
  const [keysMessage, setKeysMessage] = useState<FormMessage | null>(null);

  const [emailForm, setEmailForm] = useState({
    smtp_host: "",
    smtp_port: "",
    smtp_user: "",
    smtp_password: "",
    smtp_from_name: "",
    imap_host: "",
    imap_port: "",
  });
  const [savingEmail, setSavingEmail] = useState(false);
  const [emailMessage, setEmailMessage] = useState<FormMessage | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const data = await getSettings();
      setSettings(data);
      setEmailForm({
        smtp_host: data.smtp_host,
        smtp_port: String(data.smtp_port),
        smtp_user: data.smtp_user,
        smtp_password: "",
        smtp_from_name: data.smtp_from_name,
        imap_host: data.imap_host,
        imap_port: String(data.imap_port),
      });
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  async function handleSaveKeys() {
    const payload: SettingsUpdate = {};
    (Object.keys(keyInputs) as KeyField[]).forEach((field) => {
      const value = keyInputs[field].trim();
      if (value) payload[field] = value;
    });
    if (Object.keys(payload).length === 0) {
      setKeysMessage({ type: "error", text: "Enter at least one key before saving." });
      return;
    }
    setSavingKeys(true);
    setKeysMessage(null);
    try {
      const updated = await updateSettings(payload);
      setSettings(updated);
      setKeyInputs(EMPTY_KEY_INPUTS);
      setKeysMessage({
        type: "success",
        text: "API keys updated — takes effect immediately, no restart needed.",
      });
    } catch (error) {
      setKeysMessage({ type: "error", text: (error as Error).message });
    } finally {
      setSavingKeys(false);
    }
  }

  async function handleSaveEmail() {
    setSavingEmail(true);
    setEmailMessage(null);
    try {
      const payload: SettingsUpdate = {
        smtp_host: emailForm.smtp_host,
        smtp_port: Number(emailForm.smtp_port),
        smtp_user: emailForm.smtp_user,
        smtp_from_name: emailForm.smtp_from_name,
        imap_host: emailForm.imap_host,
        imap_port: Number(emailForm.imap_port),
      };
      if (emailForm.smtp_password.trim()) {
        payload.smtp_password = emailForm.smtp_password.trim();
      }
      const updated = await updateSettings(payload);
      setSettings(updated);
      setEmailForm((f) => ({ ...f, smtp_password: "" }));
      setEmailMessage({ type: "success", text: "Email configuration updated." });
    } catch (error) {
      setEmailMessage({ type: "error", text: (error as Error).message });
    } finally {
      setSavingEmail(false);
    }
  }

  return (
    <>
      <AppHeader
        title="Settings"
        description="AI provider keys and email configuration"
      />
      <PageContainer>
        {loading || !settings ? (
          <div className="flex justify-center py-10">
            <Spinner className="size-5" />
          </div>
        ) : (
          <>
            <Card>
              <CardHeader className="flex flex-row items-center gap-2 space-y-0">
                <KeyRound className="size-4 text-muted-foreground" />
                <div>
                  <CardTitle className="text-sm font-medium">AI Provider Keys</CardTitle>
                  <p className="text-sm text-muted-foreground">
                    Tried in order — OpenAI, then Anthropic, then Gemini — so a key
                    running out of credit fails over to the next automatically.
                  </p>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                {KEY_FIELDS.map(({ field, label, hint }) => (
                  <div key={field} className="space-y-1.5">
                    <div className="flex items-center gap-2">
                      <Label htmlFor={field}>{label}</Label>
                      {settings[`${field}_set` as keyof Settings] ? (
                        <Badge variant="secondary" className="gap-1">
                          <CheckCircle2 className="size-3" />
                          Configured
                        </Badge>
                      ) : (
                        <Badge variant="outline">Not set</Badge>
                      )}
                    </div>
                    <Input
                      id={field}
                      type="password"
                      autoComplete="off"
                      placeholder={
                        settings[`${field}_set` as keyof Settings]
                          ? "Enter a new value to replace the existing key"
                          : "Not set"
                      }
                      value={keyInputs[field]}
                      onChange={(e) =>
                        setKeyInputs((k) => ({ ...k, [field]: e.target.value }))
                      }
                    />
                    <p className="text-sm text-muted-foreground">{hint}</p>
                  </div>
                ))}
                {keysMessage ? (
                  <Alert variant={keysMessage.type === "error" ? "destructive" : "default"}>
                    {keysMessage.type === "error" ? (
                      <AlertCircle className="size-4" />
                    ) : (
                      <CheckCircle2 className="size-4" />
                    )}
                    <AlertTitle>
                      {keysMessage.type === "error" ? "Couldn't save" : "Saved"}
                    </AlertTitle>
                    <AlertDescription>{keysMessage.text}</AlertDescription>
                  </Alert>
                ) : null}
                <Button onClick={handleSaveKeys} disabled={savingKeys} className="gap-2">
                  {savingKeys ? <Spinner className="size-4" /> : null}
                  Save API Keys
                </Button>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center gap-2 space-y-0">
                <Mail className="size-4 text-muted-foreground" />
                <div>
                  <CardTitle className="text-sm font-medium">Email (SMTP / IMAP)</CardTitle>
                  <p className="text-sm text-muted-foreground">
                    SMTP sends outreach emails; IMAP polls for replies.
                  </p>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                  <div className="space-y-1.5">
                    <Label htmlFor="smtp-host">SMTP host</Label>
                    <Input
                      id="smtp-host"
                      value={emailForm.smtp_host}
                      onChange={(e) =>
                        setEmailForm((f) => ({ ...f, smtp_host: e.target.value }))
                      }
                    />
                  </div>
                  <div className="space-y-1.5">
                    <Label htmlFor="smtp-port">SMTP port</Label>
                    <Input
                      id="smtp-port"
                      type="number"
                      value={emailForm.smtp_port}
                      onChange={(e) =>
                        setEmailForm((f) => ({ ...f, smtp_port: e.target.value }))
                      }
                    />
                  </div>
                  <div className="space-y-1.5">
                    <Label htmlFor="smtp-user">SMTP username</Label>
                    <Input
                      id="smtp-user"
                      value={emailForm.smtp_user}
                      onChange={(e) =>
                        setEmailForm((f) => ({ ...f, smtp_user: e.target.value }))
                      }
                    />
                  </div>
                  <div className="space-y-1.5">
                    <div className="flex items-center gap-2">
                      <Label htmlFor="smtp-password">SMTP password</Label>
                      {settings.smtp_password_set ? (
                        <Badge variant="secondary" className="gap-1">
                          <CheckCircle2 className="size-3" />
                          Configured
                        </Badge>
                      ) : (
                        <Badge variant="outline">Not set</Badge>
                      )}
                    </div>
                    <Input
                      id="smtp-password"
                      type="password"
                      autoComplete="off"
                      placeholder={
                        settings.smtp_password_set
                          ? "Enter a new value to replace it"
                          : "Not set"
                      }
                      value={emailForm.smtp_password}
                      onChange={(e) =>
                        setEmailForm((f) => ({ ...f, smtp_password: e.target.value }))
                      }
                    />
                  </div>
                  <div className="space-y-1.5">
                    <Label htmlFor="smtp-from-name">From name</Label>
                    <Input
                      id="smtp-from-name"
                      value={emailForm.smtp_from_name}
                      onChange={(e) =>
                        setEmailForm((f) => ({ ...f, smtp_from_name: e.target.value }))
                      }
                    />
                  </div>
                  <div />
                  <div className="space-y-1.5">
                    <Label htmlFor="imap-host">IMAP host</Label>
                    <Input
                      id="imap-host"
                      value={emailForm.imap_host}
                      onChange={(e) =>
                        setEmailForm((f) => ({ ...f, imap_host: e.target.value }))
                      }
                    />
                  </div>
                  <div className="space-y-1.5">
                    <Label htmlFor="imap-port">IMAP port</Label>
                    <Input
                      id="imap-port"
                      type="number"
                      value={emailForm.imap_port}
                      onChange={(e) =>
                        setEmailForm((f) => ({ ...f, imap_port: e.target.value }))
                      }
                    />
                  </div>
                </div>
                {emailMessage ? (
                  <Alert variant={emailMessage.type === "error" ? "destructive" : "default"}>
                    {emailMessage.type === "error" ? (
                      <AlertCircle className="size-4" />
                    ) : (
                      <CheckCircle2 className="size-4" />
                    )}
                    <AlertTitle>
                      {emailMessage.type === "error" ? "Couldn't save" : "Saved"}
                    </AlertTitle>
                    <AlertDescription>{emailMessage.text}</AlertDescription>
                  </Alert>
                ) : null}
                <Button onClick={handleSaveEmail} disabled={savingEmail} className="gap-2">
                  {savingEmail ? <Spinner className="size-4" /> : null}
                  Save Email Configuration
                </Button>
              </CardContent>
            </Card>
          </>
        )}
      </PageContainer>
    </>
  );
}

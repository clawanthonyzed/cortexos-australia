"use client";

import { useState } from "react";
import { AppShell } from "@/components/layout/app-shell";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import {
  Settings,
  Key,
  Cpu,
  Plug,
  Users,
  Bell,
  Shield,
  CheckCircle2,
  XCircle,
  Eye,
  EyeOff,
} from "lucide-react";

interface APIKeyField {
  id: string;
  label: string;
  placeholder: string;
  envVar: string;
  connected: boolean;
}

const LLM_PROVIDERS: APIKeyField[] = [
  {
    id: "anthropic",
    label: "Anthropic (Claude)",
    placeholder: "sk-ant-...",
    envVar: "ANTHROPIC_API_KEY",
    connected: true,
  },
  {
    id: "openai",
    label: "OpenAI",
    placeholder: "sk-...",
    envVar: "OPENAI_API_KEY",
    connected: false,
  },
  {
    id: "google",
    label: "Google (Gemini)",
    placeholder: "AIza...",
    envVar: "GOOGLE_API_KEY",
    connected: false,
  },
  {
    id: "openrouter",
    label: "OpenRouter",
    placeholder: "sk-or-...",
    envVar: "OPENROUTER_API_KEY",
    connected: false,
  },
];

const INTEGRATIONS: APIKeyField[] = [
  {
    id: "etsy",
    label: "Etsy",
    placeholder: "Etsy API Key",
    envVar: "ETSY_API_KEY",
    connected: false,
  },
  {
    id: "gumroad",
    label: "Gumroad",
    placeholder: "Access Token",
    envVar: "GUMROAD_ACCESS_TOKEN",
    connected: false,
  },
  {
    id: "lemonsqueezy",
    label: "Lemon Squeezy",
    placeholder: "API Key",
    envVar: "LEMONSQUEEZY_API_KEY",
    connected: false,
  },
  {
    id: "github",
    label: "GitHub",
    placeholder: "ghp_...",
    envVar: "GITHUB_TOKEN",
    connected: true,
  },
];

function APIKeyRow({ field }: { field: APIKeyField }) {
  const [visible, setVisible] = useState(false);
  const [value, setValue] = useState("");

  return (
    <div className="flex items-center gap-4 py-3">
      <div className="w-48 shrink-0">
        <div className="flex items-center gap-2">
          {field.connected ? (
            <CheckCircle2 className="h-4 w-4 text-green-500" />
          ) : (
            <XCircle className="h-4 w-4 text-cortex-muted" />
          )}
          <span className="text-sm font-medium text-cortex-text">{field.label}</span>
        </div>
        <p className="text-xs text-cortex-muted mt-0.5">{field.envVar}</p>
      </div>
      <div className="flex-1 relative">
        <Input
          type={visible ? "text" : "password"}
          placeholder={field.connected ? "••••••••••••••••" : field.placeholder}
          value={value}
          onChange={(e) => setValue(e.target.value)}
          className="pr-10 bg-cortex-surface border-cortex-border"
        />
        <button
          type="button"
          onClick={() => setVisible(!visible)}
          className="absolute right-3 top-1/2 -translate-y-1/2 text-cortex-muted hover:text-cortex-text"
        >
          {visible ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
        </button>
      </div>
      <Button
        variant="outline"
        size="sm"
        className="shrink-0 border-cortex-border"
      >
        {field.connected ? "Update" : "Connect"}
      </Button>
      {field.connected && (
        <Badge variant="outline" className="border-green-500/30 text-green-500 shrink-0">
          Connected
        </Badge>
      )}
    </div>
  );
}

export default function SettingsPage() {
  const [langfuseEnabled, setLangfuseEnabled] = useState(true);
  const [debugMode, setDebugMode] = useState(false);
  const [autoRetry, setAutoRetry] = useState(true);
  const [maxRetries, setMaxRetries] = useState("3");
  const [taskTimeout, setTaskTimeout] = useState("3600");

  return (
    <AppShell>
      <div className="p-6 max-w-4xl">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-2xl font-semibold text-cortex-text flex items-center gap-2">
            <Settings className="h-6 w-6 text-cortex-accent" />
            Settings
          </h1>
          <p className="text-sm text-cortex-muted mt-1">
            Configure CortexOS — API keys, models, integrations, and system preferences.
          </p>
        </div>

        <Tabs defaultValue="models">
          <TabsList className="bg-cortex-surface border border-cortex-border mb-6">
            <TabsTrigger value="models" className="gap-1.5">
              <Cpu className="h-3.5 w-3.5" />
              Models
            </TabsTrigger>
            <TabsTrigger value="integrations" className="gap-1.5">
              <Plug className="h-3.5 w-3.5" />
              Integrations
            </TabsTrigger>
            <TabsTrigger value="system" className="gap-1.5">
              <Settings className="h-3.5 w-3.5" />
              System
            </TabsTrigger>
            <TabsTrigger value="security" className="gap-1.5">
              <Shield className="h-3.5 w-3.5" />
              Security
            </TabsTrigger>
            <TabsTrigger value="notifications" className="gap-1.5">
              <Bell className="h-3.5 w-3.5" />
              Notifications
            </TabsTrigger>
          </TabsList>

          {/* Models Tab */}
          <TabsContent value="models">
            <Card className="bg-cortex-surface border-cortex-border">
              <CardHeader>
                <CardTitle className="text-cortex-text flex items-center gap-2">
                  <Key className="h-4 w-4 text-cortex-accent" />
                  LLM Provider API Keys
                </CardTitle>
                <CardDescription className="text-cortex-muted">
                  Connect LLM providers. Keys stored encrypted in environment — never logged.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="divide-y divide-cortex-border">
                  {LLM_PROVIDERS.map((field) => (
                    <APIKeyRow key={field.id} field={field} />
                  ))}
                </div>
              </CardContent>
            </Card>

            <Card className="bg-cortex-surface border-cortex-border mt-4">
              <CardHeader>
                <CardTitle className="text-cortex-text text-base">Default Model</CardTitle>
                <CardDescription className="text-cortex-muted">
                  Used when agents don&apos;t specify a model.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-1.5">
                    <Label className="text-cortex-text text-sm">Provider</Label>
                    <Input
                      defaultValue="claude"
                      className="bg-cortex-bg border-cortex-border"
                    />
                  </div>
                  <div className="space-y-1.5">
                    <Label className="text-cortex-text text-sm">Model</Label>
                    <Input
                      defaultValue="claude-sonnet-4-6"
                      className="bg-cortex-bg border-cortex-border"
                    />
                  </div>
                </div>
                <Button size="sm">Save Defaults</Button>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Integrations Tab */}
          <TabsContent value="integrations">
            <Card className="bg-cortex-surface border-cortex-border">
              <CardHeader>
                <CardTitle className="text-cortex-text flex items-center gap-2">
                  <Plug className="h-4 w-4 text-cortex-accent" />
                  Commerce Integrations
                </CardTitle>
                <CardDescription className="text-cortex-muted">
                  Connect Etsy, Gumroad, Lemon Squeezy, and GitHub for product publishing and analytics.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="divide-y divide-cortex-border">
                  {INTEGRATIONS.map((field) => (
                    <APIKeyRow key={field.id} field={field} />
                  ))}
                </div>
              </CardContent>
            </Card>

            <Card className="bg-cortex-surface border-cortex-border mt-4">
              <CardHeader>
                <CardTitle className="text-cortex-text text-base">Observability</CardTitle>
                <CardDescription className="text-cortex-muted">
                  Langfuse LLM tracing and cost analytics.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-cortex-text">Enable Langfuse</p>
                    <p className="text-xs text-cortex-muted">Trace all LLM calls for cost and latency analysis</p>
                  </div>
                  <Switch
                    checked={langfuseEnabled}
                    onCheckedChange={setLangfuseEnabled}
                  />
                </div>
                <Separator className="bg-cortex-border" />
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-1.5">
                    <Label className="text-cortex-text text-sm">Secret Key</Label>
                    <Input
                      type="password"
                      placeholder="sk-lf-..."
                      className="bg-cortex-bg border-cortex-border"
                    />
                  </div>
                  <div className="space-y-1.5">
                    <Label className="text-cortex-text text-sm">Public Key</Label>
                    <Input
                      type="password"
                      placeholder="pk-lf-..."
                      className="bg-cortex-bg border-cortex-border"
                    />
                  </div>
                </div>
                <div className="space-y-1.5">
                  <Label className="text-cortex-text text-sm">Langfuse Host</Label>
                  <Input
                    defaultValue="http://langfuse:3000"
                    className="bg-cortex-bg border-cortex-border"
                  />
                </div>
                <Button size="sm">Save Langfuse Config</Button>
              </CardContent>
            </Card>
          </TabsContent>

          {/* System Tab */}
          <TabsContent value="system">
            <Card className="bg-cortex-surface border-cortex-border">
              <CardHeader>
                <CardTitle className="text-cortex-text">System Configuration</CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-cortex-text">Debug Mode</p>
                      <p className="text-xs text-cortex-muted">Enable verbose logging. Not for production.</p>
                    </div>
                    <Switch checked={debugMode} onCheckedChange={setDebugMode} />
                  </div>
                  <Separator className="bg-cortex-border" />
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-cortex-text">Auto-retry Failed Tasks</p>
                      <p className="text-xs text-cortex-muted">Automatically retry tasks on transient errors.</p>
                    </div>
                    <Switch checked={autoRetry} onCheckedChange={setAutoRetry} />
                  </div>
                </div>
                <Separator className="bg-cortex-border" />
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-1.5">
                    <Label className="text-cortex-text text-sm">Max Retries</Label>
                    <Input
                      type="number"
                      value={maxRetries}
                      onChange={(e) => setMaxRetries(e.target.value)}
                      className="bg-cortex-bg border-cortex-border"
                      min={0}
                      max={10}
                    />
                  </div>
                  <div className="space-y-1.5">
                    <Label className="text-cortex-text text-sm">Task Timeout (seconds)</Label>
                    <Input
                      type="number"
                      value={taskTimeout}
                      onChange={(e) => setTaskTimeout(e.target.value)}
                      className="bg-cortex-bg border-cortex-border"
                    />
                  </div>
                </div>
                <Button size="sm">Save System Config</Button>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Security Tab */}
          <TabsContent value="security">
            <Card className="bg-cortex-surface border-cortex-border">
              <CardHeader>
                <CardTitle className="text-cortex-text flex items-center gap-2">
                  <Shield className="h-4 w-4 text-cortex-accent" />
                  Security
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="space-y-1.5">
                  <Label className="text-cortex-text text-sm">Change Password</Label>
                  <div className="space-y-2 max-w-sm">
                    <Input
                      type="password"
                      placeholder="Current password"
                      className="bg-cortex-bg border-cortex-border"
                    />
                    <Input
                      type="password"
                      placeholder="New password"
                      className="bg-cortex-bg border-cortex-border"
                    />
                    <Input
                      type="password"
                      placeholder="Confirm new password"
                      className="bg-cortex-bg border-cortex-border"
                    />
                    <Button size="sm">Update Password</Button>
                  </div>
                </div>
                <Separator className="bg-cortex-border" />
                <div>
                  <p className="text-sm font-medium text-cortex-text mb-1">Session Tokens</p>
                  <p className="text-xs text-cortex-muted mb-3">
                    Access tokens expire in 30 minutes. Refresh tokens valid for 7 days.
                  </p>
                  <Button variant="destructive" size="sm">
                    Revoke All Sessions
                  </Button>
                </div>
                <Separator className="bg-cortex-border" />
                <div>
                  <p className="text-sm font-medium text-cortex-text mb-1">Audit Log</p>
                  <p className="text-xs text-cortex-muted mb-3">
                    All admin actions are logged. View in{" "}
                    <a href="/logs" className="text-cortex-accent hover:underline">Logs</a>.
                  </p>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Notifications Tab */}
          <TabsContent value="notifications">
            <Card className="bg-cortex-surface border-cortex-border">
              <CardHeader>
                <CardTitle className="text-cortex-text flex items-center gap-2">
                  <Bell className="h-4 w-4 text-cortex-accent" />
                  Notifications
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {[
                  { id: "agent_error", label: "Agent Errors", desc: "Notify when an agent enters error state" },
                  { id: "task_complete", label: "Task Completion", desc: "Notify when long-running tasks finish" },
                  { id: "approval_needed", label: "Approval Gates", desc: "Notify when a workflow needs human approval" },
                  { id: "cost_alert", label: "Cost Alerts", desc: "Notify when daily spend exceeds threshold" },
                ].map((item) => (
                  <div key={item.id} className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-cortex-text">{item.label}</p>
                      <p className="text-xs text-cortex-muted">{item.desc}</p>
                    </div>
                    <Switch defaultChecked={item.id !== "task_complete"} />
                  </div>
                ))}
                <Separator className="bg-cortex-border" />
                <div className="space-y-1.5">
                  <Label className="text-cortex-text text-sm">Daily Cost Alert Threshold (USD)</Label>
                  <Input
                    type="number"
                    defaultValue="10"
                    className="bg-cortex-bg border-cortex-border max-w-xs"
                    min={0}
                  />
                </div>
                <Button size="sm">Save Notification Settings</Button>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </AppShell>
  );
}

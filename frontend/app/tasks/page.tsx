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
  createTask,
  deleteTask,
  getLeads,
  getTasks,
  updateTask,
  type Lead,
  type Task,
} from "@/lib/api";
import { humanize } from "@/lib/lead-status";
import { SectionIcon } from "@/components/ui/section-icon";
import { AlertCircle, CheckSquare, Plus, Trash2 } from "lucide-react";

const PRIORITY_VARIANT: Record<string, "default" | "destructive" | "secondary"> = {
  low: "secondary",
  medium: "default",
  high: "destructive",
};

const STATUS_OPTIONS = [
  { value: "pending", label: "Pending" },
  { value: "in_progress", label: "In Progress" },
  { value: "done", label: "Done" },
];

export default function TasksPage() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [leads, setLeads] = useState<Lead[]>([]);
  const [loading, setLoading] = useState(true);

  const [dialogOpen, setDialogOpen] = useState(false);
  const [leadId, setLeadId] = useState("");
  const [title, setTitle] = useState("");
  const [owner, setOwner] = useState("");
  const [dueDate, setDueDate] = useState("");
  const [priority, setPriority] = useState<"low" | "medium" | "high">("medium");
  const [notes, setNotes] = useState("");
  const [saving, setSaving] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [taskRes, leadRes] = await Promise.all([
        getTasks(),
        getLeads({ page: 1, page_size: 200 }),
      ]);
      setTasks(taskRes);
      setLeads(leadRes.items);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  function leadName(id: string) {
    return leads.find((l) => l.id === id)?.business_name ?? id;
  }

  async function handleCreate() {
    if (!leadId || !title.trim()) return;
    setSaving(true);
    try {
      await createTask({
        lead_id: leadId,
        title: title.trim(),
        owner: owner.trim() || undefined,
        due_date: dueDate ? new Date(dueDate).toISOString() : undefined,
        priority,
        notes: notes.trim() || undefined,
      });
      setDialogOpen(false);
      setLeadId("");
      setTitle("");
      setOwner("");
      setDueDate("");
      setPriority("medium");
      setNotes("");
      await load();
    } finally {
      setSaving(false);
    }
  }

  async function handleStatusChange(task: Task, status: string) {
    await updateTask(task.id, { status: status as Task["status"] });
    await load();
  }

  async function handleDelete(task: Task) {
    await deleteTask(task.id);
    await load();
  }

  return (
    <>
      <AppHeader title="Tasks" description="Follow-up and sales tasks" />
      <PageContainer>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0">
            <div className="flex items-center gap-3">
              <SectionIcon icon={CheckSquare} color="emerald" />
              <div>
                <CardTitle className="text-base font-semibold">
                  Tasks {tasks.length > 0 ? `(${tasks.length})` : ""}
                </CardTitle>
                <p className="text-sm text-muted-foreground">
                  Follow-ups and to-dos tied to a specific lead.
                </p>
              </div>
            </div>
            <Button size="sm" onClick={() => setDialogOpen(true)} className="gap-2">
              <Plus className="size-4" />
              Add Task
            </Button>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="flex justify-center py-10">
                <Spinner className="size-5" />
              </div>
            ) : tasks.length === 0 ? (
              <p className="py-10 text-center text-sm text-muted-foreground">
                No tasks yet. Add one from here or from a lead's call workspace.
              </p>
            ) : (
              <div className="space-y-2">
                {tasks.map((task) => {
                  const isOverdue =
                    task.status !== "done" &&
                    task.due_date !== null &&
                    new Date(task.due_date) < new Date();
                  return (
                  <div
                    key={task.id}
                    className="flex flex-wrap items-center justify-between gap-3 rounded-lg border p-3"
                  >
                    <div>
                      <div className="flex items-center gap-2">
                        <p className="font-medium">{task.title}</p>
                        <Badge variant={PRIORITY_VARIANT[task.priority]}>
                          {humanize(task.priority)}
                        </Badge>
                        {isOverdue ? (
                          <Badge variant="destructive" className="gap-1">
                            <AlertCircle className="size-3" />
                            Overdue
                          </Badge>
                        ) : null}
                      </div>
                      <p className="text-sm text-muted-foreground">
                        {leadName(task.lead_id)}
                        {task.owner ? ` · ${task.owner}` : ""}
                        {task.due_date
                          ? ` · due ${new Date(task.due_date).toLocaleDateString()}`
                          : ""}
                      </p>
                      {task.notes ? (
                        <p className="mt-1 text-sm text-muted-foreground">
                          {task.notes}
                        </p>
                      ) : null}
                    </div>
                    <div className="flex items-center gap-2">
                      <Select
                        value={task.status}
                        onValueChange={(v) => v && handleStatusChange(task, v)}
                      >
                        <SelectTrigger size="sm" className="w-[130px]">
                          <SelectValue>
                            {(value: string) =>
                              STATUS_OPTIONS.find((o) => o.value === value)
                                ?.label ?? value
                            }
                          </SelectValue>
                        </SelectTrigger>
                        <SelectContent>
                          {STATUS_OPTIONS.map((o) => (
                            <SelectItem key={o.value} value={o.value}>
                              {o.label}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                      <Button
                        size="icon-sm"
                        variant="outline"
                        onClick={() => handleDelete(task)}
                      >
                        <Trash2 className="size-4" />
                      </Button>
                    </div>
                  </div>
                  );
                })}
              </div>
            )}
          </CardContent>
        </Card>
      </PageContainer>

      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Add Task</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-1.5">
              <Label>Lead</Label>
              <Select value={leadId} onValueChange={(v) => setLeadId(v ?? "")}>
                <SelectTrigger className="w-full">
                  <SelectValue placeholder="Choose a lead">
                    {(value: string) => leadName(value)}
                  </SelectValue>
                </SelectTrigger>
                <SelectContent>
                  {leads.map((l) => (
                    <SelectItem key={l.id} value={l.id}>
                      {l.business_name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="task-title">Title</Label>
              <Input
                id="task-title"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1.5">
                <Label htmlFor="task-owner">Owner</Label>
                <Input
                  id="task-owner"
                  value={owner}
                  onChange={(e) => setOwner(e.target.value)}
                />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="task-due">Due date</Label>
                <Input
                  id="task-due"
                  type="date"
                  value={dueDate}
                  onChange={(e) => setDueDate(e.target.value)}
                />
              </div>
            </div>
            <div className="space-y-1.5">
              <Label>Priority</Label>
              <Select
                value={priority}
                onValueChange={(v) => setPriority(v as "low" | "medium" | "high")}
              >
                <SelectTrigger className="w-full">
                  <SelectValue>
                    {(value: string) => value.charAt(0).toUpperCase() + value.slice(1)}
                  </SelectValue>
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="low">Low</SelectItem>
                  <SelectItem value="medium">Medium</SelectItem>
                  <SelectItem value="high">High</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="task-notes">Notes</Label>
              <Textarea
                id="task-notes"
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
              />
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setDialogOpen(false)}
              disabled={saving}
            >
              Cancel
            </Button>
            <Button
              onClick={handleCreate}
              disabled={saving || !leadId || !title.trim()}
              className="gap-2"
            >
              {saving ? <Spinner className="size-4" /> : null}
              Save
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}

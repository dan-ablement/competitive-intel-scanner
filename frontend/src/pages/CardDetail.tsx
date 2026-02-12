import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useCard, useUpdateCard, useChangeCardStatus } from "@/hooks/use-cards";
import type { AnalysisCard, CardStatus, Priority, EventType } from "@/types";
import { cn } from "@/lib/utils";
import {
  ArrowLeft,
  Save,
  Loader2,
  CheckCircle2,
  ExternalLink,
  ChevronDown,
} from "lucide-react";
import { CommentsPanel, EditHistory, ApprovalWorkflow } from "@/components/cards";

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const EVENT_TYPE_OPTIONS: { value: EventType; label: string }[] = [
  { value: "new_feature", label: "New Feature" },
  { value: "product_announcement", label: "Product Announcement" },
  { value: "partnership", label: "Partnership" },
  { value: "acquisition", label: "Acquisition" },
  { value: "acquired", label: "Acquired" },
  { value: "funding", label: "Funding" },
  { value: "pricing_change", label: "Pricing Change" },
  { value: "leadership_change", label: "Leadership Change" },
  { value: "expansion", label: "Expansion" },
  { value: "other", label: "Other" },
];

const PRIORITY_CONFIG: { value: Priority; label: string; letter: string; bg: string; ring: string; dot: string }[] = [
  { value: "red", label: "Red — Urgent", letter: "R", bg: "bg-red-100 text-red-800 border-red-300", ring: "ring-red-400", dot: "bg-red-500" },
  { value: "yellow", label: "Yellow — Warning", letter: "Y", bg: "bg-amber-100 text-amber-800 border-amber-300", ring: "ring-amber-400", dot: "bg-amber-400" },
  { value: "green", label: "Green — Info", letter: "G", bg: "bg-green-100 text-green-800 border-green-300", ring: "ring-green-400", dot: "bg-green-500" },
];

// ---------------------------------------------------------------------------
// Form type
// ---------------------------------------------------------------------------

interface CardForm {
  title: string;
  summary: string;
  impact_assessment: string;
  suggested_counter_moves: string;
  event_type: EventType;
  priority: Priority;
}

// ---------------------------------------------------------------------------
// Main Component
// ---------------------------------------------------------------------------

export default function CardDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { data: card, isLoading, error } = useCard(id!);
  const updateMutation = useUpdateCard();
  const statusMutation = useChangeCardStatus();

  const [saved, setSaved] = useState(false);
  const [historyOpen, setHistoryOpen] = useState(false);
  const [form, setForm] = useState<CardForm>({
    title: "",
    summary: "",
    impact_assessment: "",
    suggested_counter_moves: "",
    event_type: "other",
    priority: "green",
  });

  useEffect(() => {
    if (card) {
      setForm({
        title: card.title ?? "",
        summary: card.summary ?? "",
        impact_assessment: card.impact_assessment ?? "",
        suggested_counter_moves: card.suggested_counter_moves ?? "",
        event_type: card.event_type,
        priority: card.priority,
      });
    }
  }, [card]);

  const handleSave = async () => {
    if (!id) return;
    setSaved(false);
    await updateMutation.mutateAsync({ id, card: form });
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  };

  const handleStatusChange = async (status: CardStatus) => {
    if (!id) return;
    await statusMutation.mutateAsync({ id, status });
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (error || !card) {
    return (
      <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-4 text-destructive">
        Analysis card not found.
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-5xl">
      {/* Header */}
      <div className="mb-6 flex items-center gap-3">
        <button
          onClick={() => navigate("/cards")}
          className="rounded-md p-1.5 hover:bg-muted"
        >
          <ArrowLeft className="h-5 w-5" />
        </button>
        <div className="flex-1">
          <input
            value={form.title}
            onChange={(e) => setForm((prev) => ({ ...prev, title: e.target.value }))}
            className="w-full border-none bg-transparent text-2xl font-bold focus:outline-none"
            placeholder="Card title..."
          />
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-[1fr_280px]">
        {/* Main content */}
        <div className="space-y-6">
          {/* Summary */}
          <div className="space-y-2">
            <label className="text-sm font-medium">Summary</label>
            <textarea
              value={form.summary}
              onChange={(e) => setForm((prev) => ({ ...prev, summary: e.target.value }))}
              placeholder="Brief summary of the competitive development..."
              rows={4}
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
            />
          </div>

          {/* Impact Assessment */}
          <div className="space-y-2">
            <label className="text-sm font-medium">Impact Assessment</label>
            <textarea
              value={form.impact_assessment}
              onChange={(e) => setForm((prev) => ({ ...prev, impact_assessment: e.target.value }))}
              placeholder="How does this impact Augment Code..."
              rows={6}
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
            />
          </div>

          {/* Suggested Counter-moves */}
          <div className="space-y-2">
            <label className="text-sm font-medium">Suggested Counter-moves</label>
            <textarea
              value={form.suggested_counter_moves}
              onChange={(e) => setForm((prev) => ({ ...prev, suggested_counter_moves: e.target.value }))}
              placeholder="Recommended actions and responses..."
              rows={6}
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
            />
          </div>

          {/* Save button (bottom) */}
          <div className="flex items-center justify-between border-t border-border pt-4">
            <p className="text-xs text-muted-foreground">
              Last updated: {new Date(card.updated_at).toLocaleString()}
            </p>
            <button
              onClick={handleSave}
              disabled={updateMutation.isPending}
              className="inline-flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
            >
              {updateMutation.isPending ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : saved ? (
                <CheckCircle2 className="h-4 w-4" />
              ) : (
                <Save className="h-4 w-4" />
              )}
              {updateMutation.isPending ? "Saving..." : saved ? "Saved" : "Save Changes"}
            </button>
          </div>

          {updateMutation.isError && (
            <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-3 text-sm text-destructive">
              Failed to save changes. Please try again.
            </div>
          )}

          {/* Edit History (collapsible) */}
          <div className="rounded-lg border border-border">
            <button
              onClick={() => setHistoryOpen((prev) => !prev)}
              className="flex w-full items-center justify-between px-4 py-3 text-sm font-medium hover:bg-muted/50"
            >
              Edit History
              <ChevronDown
                className={cn(
                  "h-4 w-4 text-muted-foreground transition-transform",
                  historyOpen && "rotate-180"
                )}
              />
            </button>
            {historyOpen && <EditHistory cardId={id!} />}
          </div>
        </div>

        {/* Sidebar */}
        <div className="space-y-5">
          {/* Priority selector */}
          <div className="rounded-lg border border-border bg-card p-4">
            <label className="mb-2 block text-sm font-medium">Priority</label>
            <div className="flex gap-2">
              {PRIORITY_CONFIG.map((p) => (
                <button
                  key={p.value}
                  onClick={() => setForm((prev) => ({ ...prev, priority: p.value }))}
                  className={cn(
                    "flex h-10 w-10 items-center justify-center rounded-lg border text-sm font-bold transition-all",
                    form.priority === p.value
                      ? cn(p.bg, "ring-2", p.ring)
                      : "border-input bg-background text-muted-foreground hover:bg-muted"
                  )}
                  title={p.label}
                >
                  {p.letter}
                </button>
              ))}
            </div>
            <p className="mt-2 text-xs text-muted-foreground">
              {PRIORITY_CONFIG.find((p) => p.value === form.priority)?.label}
            </p>
          </div>

          {/* Approval Workflow */}
          <div className="rounded-lg border border-border bg-card p-4">
            <label className="mb-3 block text-sm font-medium">Status</label>
            <ApprovalWorkflow
              card={card as AnalysisCard}
              onStatusChange={handleStatusChange}
              isUpdating={statusMutation.isPending}
            />
          </div>

          {/* Event Type */}
          <div className="rounded-lg border border-border bg-card p-4">
            <label className="mb-2 block text-sm font-medium">Event Type</label>
            <select
              value={form.event_type}
              onChange={(e) => setForm((prev) => ({ ...prev, event_type: e.target.value as EventType }))}
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
            >
              {EVENT_TYPE_OPTIONS.map((et) => (
                <option key={et.value} value={et.value}>{et.label}</option>
              ))}
            </select>
          </div>

          {/* Competitors */}
          {card.competitors.length > 0 && (
            <div className="rounded-lg border border-border bg-card p-4">
              <label className="mb-2 block text-sm font-medium">Competitors</label>
              <div className="flex flex-wrap gap-1.5">
                {card.competitors.map((c) => (
                  <span
                    key={c.id}
                    className="rounded-full bg-violet-100 px-2.5 py-1 text-xs font-medium text-violet-700"
                  >
                    {c.name}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Source */}
          {card.feed_item_id && (
            <div className="rounded-lg border border-border bg-card p-4">
              <label className="mb-2 block text-sm font-medium">Source</label>
              <p className="flex items-center gap-1 text-xs text-muted-foreground">
                <ExternalLink className="h-3 w-3" />
                Feed item: {card.feed_item_id.slice(0, 8)}…
              </p>
            </div>
          )}

          {/* Metadata */}
          <div className="rounded-lg border border-border bg-card p-4">
            <label className="mb-2 block text-sm font-medium">Details</label>
            <dl className="space-y-1.5 text-xs">
              <div className="flex justify-between">
                <dt className="text-muted-foreground">Created</dt>
                <dd>{new Date(card.created_at).toLocaleDateString()}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-muted-foreground">Updated</dt>
                <dd>{new Date(card.updated_at).toLocaleDateString()}</dd>
              </div>
              {card.approved_at && (
                <div className="flex justify-between">
                  <dt className="text-muted-foreground">Approved</dt>
                  <dd>{new Date(card.approved_at).toLocaleDateString()}</dd>
                </div>
              )}
            </dl>
          </div>

          {/* Comments Panel */}
          <div className="rounded-lg border border-border bg-card">
            <CommentsPanel cardId={id!} />
          </div>
        </div>
      </div>
    </div>
  );
}


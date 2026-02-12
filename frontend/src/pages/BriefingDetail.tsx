import { useState, useEffect } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { useBriefing, useUpdateBriefing, useChangeBriefingStatus } from "@/hooks/use-briefings";
import { useAuth } from "@/contexts/AuthContext";
import type { BriefingStatus, BriefingCard } from "@/types";
import { cn } from "@/lib/utils";
import {
  ArrowLeft,
  Save,
  Loader2,
  CheckCircle2,
  Send,
  Shield,
  Archive,
  CreditCard,
} from "lucide-react";

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const STATUS_CONFIG: Record<BriefingStatus, { label: string; color: string; bgColor: string }> = {
  draft: { label: "Draft", color: "text-gray-700", bgColor: "bg-gray-100" },
  in_review: { label: "In Review", color: "text-blue-700", bgColor: "bg-blue-100" },
  approved: { label: "Approved", color: "text-green-700", bgColor: "bg-green-100" },
  archived: { label: "Archived", color: "text-amber-700", bgColor: "bg-amber-100" },
};

const STATUS_ORDER: BriefingStatus[] = ["draft", "in_review", "approved", "archived"];

const PRIORITY_BADGE: Record<string, { bg: string; dot: string; label: string }> = {
  red: { bg: "bg-red-100 text-red-800 border-red-200", dot: "bg-red-500", label: "R" },
  yellow: { bg: "bg-amber-100 text-amber-800 border-amber-200", dot: "bg-amber-400", label: "Y" },
  green: { bg: "bg-green-100 text-green-800 border-green-200", dot: "bg-green-500", label: "G" },
};

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function formatBriefingDate(iso: string): string {
  const d = new Date(iso + "T00:00:00");
  return d.toLocaleDateString(undefined, { weekday: "long", month: "long", day: "numeric", year: "numeric" });
}

function PriorityBadge({ priority }: { priority: string }) {
  const config = PRIORITY_BADGE[priority] ?? PRIORITY_BADGE.green;
  return (
    <span className={cn("inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-xs font-semibold", config.bg)}>
      <span className={cn("h-2 w-2 rounded-full", config.dot)} />
      {config.label}
    </span>
  );
}

// ---------------------------------------------------------------------------
// Approval Workflow (mirrors cards pattern)
// ---------------------------------------------------------------------------

function BriefingApprovalWorkflow({
  status,
  approvedAt,
  onStatusChange,
  isUpdating,
}: {
  status: BriefingStatus;
  approvedAt: string | null;
  onStatusChange: (status: BriefingStatus) => void;
  isUpdating?: boolean;
}) {
  const { user } = useAuth();
  const isAdmin = user?.role === "admin";
  const config = STATUS_CONFIG[status];

  return (
    <div className="space-y-4">
      {/* Current status badge */}
      <div className="flex items-center gap-3">
        <span className="text-sm font-medium text-muted-foreground">Status:</span>
        <span className={cn("inline-flex items-center rounded-full px-3 py-1 text-xs font-semibold", config.bgColor, config.color)}>
          {config.label}
        </span>
      </div>

      {/* Status progress bar */}
      <div className="flex items-center gap-1">
        {STATUS_ORDER.map((s, index) => {
          const currentIndex = STATUS_ORDER.indexOf(status);
          const isCompleted = index <= currentIndex;
          const isCurrent = s === status;

          return (
            <div key={s} className="flex flex-1 items-center">
              <div
                className={cn(
                  "flex h-8 w-8 items-center justify-center rounded-full border-2 text-xs font-medium transition-colors",
                  isCurrent
                    ? "border-primary bg-primary text-primary-foreground"
                    : isCompleted
                      ? "border-primary/50 bg-primary/10 text-primary"
                      : "border-muted bg-muted text-muted-foreground"
                )}
              >
                {index + 1}
              </div>
              {index < STATUS_ORDER.length - 1 && (
                <div className={cn("mx-1 h-0.5 flex-1", isCompleted && index < currentIndex ? "bg-primary/50" : "bg-muted")} />
              )}
            </div>
          );
        })}
      </div>
      <div className="flex justify-between text-xs text-muted-foreground">
        {STATUS_ORDER.map((s) => (
          <span key={s} className="w-8 text-center">{STATUS_CONFIG[s].label}</span>
        ))}
      </div>

      {/* Approval info */}
      {status === "approved" && approvedAt && (
        <div className="rounded-md border border-green-200 bg-green-50 p-3">
          <div className="flex items-center gap-2 text-sm text-green-800">
            <CheckCircle2 className="h-4 w-4" />
            <span>Approved on {new Date(approvedAt).toLocaleDateString()}</span>
          </div>
        </div>
      )}

      {/* Action buttons */}
      <div className="flex flex-wrap gap-2">
        {status === "draft" && (
          <button
            onClick={() => onStatusChange("in_review")}
            disabled={isUpdating}
            className="inline-flex items-center gap-2 rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-blue-700 disabled:opacity-50"
          >
            <Send className="h-4 w-4" />
            Submit for Review
          </button>
        )}

        {status === "in_review" && isAdmin && (
          <button
            onClick={() => onStatusChange("approved")}
            disabled={isUpdating}
            className="inline-flex items-center gap-2 rounded-md bg-green-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-green-700 disabled:opacity-50"
          >
            <Shield className="h-4 w-4" />
            Approve
          </button>
        )}

        {status === "in_review" && !isAdmin && (
          <p className="text-xs text-muted-foreground italic">Only admins can approve briefings.</p>
        )}

        {status !== "archived" && (
          <button
            onClick={() => onStatusChange("archived")}
            disabled={isUpdating}
            className="inline-flex items-center gap-2 rounded-md border border-input bg-background px-4 py-2 text-sm font-medium text-muted-foreground transition-colors hover:bg-muted disabled:opacity-50"
          >
            <Archive className="h-4 w-4" />
            Archive
          </button>
        )}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Linked Cards List
// ---------------------------------------------------------------------------

function LinkedCards({ cards }: { cards: BriefingCard[] }) {
  if (cards.length === 0) {
    return (
      <div className="flex flex-col items-center gap-1 py-6 text-center text-muted-foreground">
        <CreditCard className="h-6 w-6" />
        <p className="text-sm">No linked cards</p>
      </div>
    );
  }

  return (
    <div className="divide-y divide-border">
      {cards.map((card) => (
        <Link
          key={card.id}
          to={`/cards/${card.id}`}
          className="flex items-center gap-3 px-4 py-2.5 transition-colors hover:bg-muted/50"
        >
          <PriorityBadge priority={card.priority} />
          <span className="min-w-0 flex-1 truncate text-sm">{card.title}</span>
        </Link>
      ))}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main Component
// ---------------------------------------------------------------------------

export default function BriefingDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { data: briefing, isLoading, error } = useBriefing(id!);
  const updateMutation = useUpdateBriefing();
  const statusMutation = useChangeBriefingStatus();

  const [content, setContent] = useState("");
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    if (briefing) {
      setContent(briefing.content ?? "");
    }
  }, [briefing]);

  const handleSave = async () => {
    if (!id) return;
    setSaved(false);
    await updateMutation.mutateAsync({ id, briefing: { content } });
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  };

  const handleStatusChange = async (status: BriefingStatus) => {
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

  if (error || !briefing) {
    return (
      <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-4 text-destructive">
        Briefing not found.
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-5xl">
      {/* Header */}
      <div className="mb-6 flex items-center gap-3">
        <button
          onClick={() => navigate("/briefings")}
          className="rounded-md p-1.5 hover:bg-muted"
        >
          <ArrowLeft className="h-5 w-5" />
        </button>
        <div className="flex-1">
          <h1 className="text-2xl font-bold">
            Briefing — {formatBriefingDate(briefing.date)}
          </h1>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-[1fr_280px]">
        {/* Main content */}
        <div className="space-y-6">
          {/* Content editor */}
          <div className="space-y-2">
            <label className="text-sm font-medium">Briefing Content</label>
            <textarea
              value={content}
              onChange={(e) => setContent(e.target.value)}
              placeholder="Briefing content (supports markdown)..."
              rows={20}
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm font-mono placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
            />
          </div>

          {/* Save button */}
          <div className="flex items-center justify-between border-t border-border pt-4">
            <p className="text-xs text-muted-foreground">
              Last updated: {new Date(briefing.updated_at).toLocaleString()}
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
        </div>

        {/* Sidebar */}
        <div className="space-y-5">
          {/* Approval Workflow */}
          <div className="rounded-lg border border-border bg-card p-4">
            <label className="mb-3 block text-sm font-medium">Status</label>
            <BriefingApprovalWorkflow
              status={briefing.status}
              approvedAt={briefing.approved_at}
              onStatusChange={handleStatusChange}
              isUpdating={statusMutation.isPending}
            />
          </div>

          {/* Linked Cards */}
          <div className="rounded-lg border border-border bg-card">
            <div className="border-b border-border px-4 py-3">
              <label className="text-sm font-medium">
                Linked Cards ({briefing.cards?.length ?? 0})
              </label>
            </div>
            <LinkedCards cards={briefing.cards ?? []} />
          </div>

          {/* Metadata */}
          <div className="rounded-lg border border-border bg-card p-4">
            <label className="mb-2 block text-sm font-medium">Details</label>
            <dl className="space-y-1.5 text-xs">
              <div className="flex justify-between">
                <dt className="text-muted-foreground">Date</dt>
                <dd>{briefing.date}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-muted-foreground">Created</dt>
                <dd>{new Date(briefing.created_at).toLocaleDateString()}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-muted-foreground">Updated</dt>
                <dd>{new Date(briefing.updated_at).toLocaleDateString()}</dd>
              </div>
              {briefing.approved_at && (
                <div className="flex justify-between">
                  <dt className="text-muted-foreground">Approved</dt>
                  <dd>{new Date(briefing.approved_at).toLocaleDateString()}</dd>
                </div>
              )}
            </dl>
          </div>
        </div>
      </div>
    </div>
  );
}


import { Link } from "react-router-dom";
import { useBriefings } from "@/hooks/use-briefings";
import type { Briefing, BriefingStatus } from "@/types";
import { cn } from "@/lib/utils";
import { Loader2, FileText } from "lucide-react";

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const STATUS_CONFIG: Record<BriefingStatus, { label: string; className: string }> = {
  draft: { label: "Draft", className: "bg-gray-100 text-gray-700 border-gray-200" },
  in_review: { label: "In Review", className: "bg-blue-100 text-blue-700 border-blue-200" },
  approved: { label: "Approved", className: "bg-green-100 text-green-700 border-green-200" },
  archived: { label: "Archived", className: "bg-muted text-muted-foreground border-border" },
};

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function StatusBadge({ status }: { status: BriefingStatus }) {
  const config = STATUS_CONFIG[status];
  return (
    <span className={cn("inline-flex rounded-full border px-2 py-0.5 text-xs font-medium", config.className)}>
      {config.label}
    </span>
  );
}

function formatDate(iso: string): string {
  const d = new Date(iso + "T00:00:00");
  return d.toLocaleDateString(undefined, { weekday: "short", month: "short", day: "numeric", year: "numeric" });
}

// ---------------------------------------------------------------------------
// Briefing Row
// ---------------------------------------------------------------------------

function BriefingRow({ briefing }: { briefing: Briefing }) {
  const cardCount = briefing.cards?.length ?? 0;

  return (
    <Link
      to={`/briefings/${briefing.id}`}
      className="flex items-center gap-4 border-b border-border px-4 py-3 transition-colors hover:bg-muted/50 last:border-b-0"
    >
      {/* Date */}
      <div className="min-w-0 flex-1">
        <div className="font-medium">{formatDate(briefing.date)}</div>
        <div className="mt-0.5 flex items-center gap-2 text-xs text-muted-foreground">
          <span>{cardCount} {cardCount === 1 ? "card" : "cards"}</span>
          {briefing.approved_at && (
            <span>· Approved {new Date(briefing.approved_at).toLocaleDateString()}</span>
          )}
        </div>
      </div>

      {/* Status */}
      <StatusBadge status={briefing.status} />

      {/* Created */}
      <span className="hidden shrink-0 text-xs text-muted-foreground sm:block">
        {new Date(briefing.created_at).toLocaleDateString()}
      </span>
    </Link>
  );
}

// ---------------------------------------------------------------------------
// Main Page
// ---------------------------------------------------------------------------

export default function Briefings() {
  const { data: briefings, isLoading, error } = useBriefings();

  // Sort by date descending (most recent first)
  const sorted = [...(briefings ?? [])].sort(
    (a, b) => new Date(b.date).getTime() - new Date(a.date).getTime()
  );

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-4 text-destructive">
        Failed to load briefings.
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold">Briefings</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Daily intelligence briefings for the leadership team.
        </p>
      </div>

      {/* Briefing list */}
      {sorted.length === 0 ? (
        <div className="flex flex-col items-center gap-2 py-12 text-center text-muted-foreground">
          <FileText className="h-10 w-10" />
          <p className="text-lg font-medium">No briefings yet</p>
          <p className="text-sm">
            Briefings will appear here once they are generated from analysis cards.
          </p>
        </div>
      ) : (
        <div className="overflow-hidden rounded-lg border border-border">
          {sorted.map((briefing) => (
            <BriefingRow key={briefing.id} briefing={briefing} />
          ))}
        </div>
      )}
    </div>
  );
}


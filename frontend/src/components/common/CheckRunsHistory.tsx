import { useState } from "react";
import { useCheckRuns, useTriggerFeedCheck } from "@/hooks/use-system";
import type { CheckRun, CheckRunStatus } from "@/types";
import { cn } from "@/lib/utils";
import {
  Loader2,
  CheckCircle2,
  XCircle,
  Play,
  Clock,
  ChevronDown,
  ChevronRight,
  AlertTriangle,
} from "lucide-react";

// ---------------------------------------------------------------------------
// Status Badge
// ---------------------------------------------------------------------------

const statusConfig: Record<CheckRunStatus, { label: string; className: string; icon: typeof CheckCircle2 }> = {
  running: {
    label: "Running",
    className: "bg-blue-100 text-blue-700",
    icon: Loader2,
  },
  completed: {
    label: "Completed",
    className: "bg-green-100 text-green-700",
    icon: CheckCircle2,
  },
  failed: {
    label: "Failed",
    className: "bg-red-100 text-red-700",
    icon: XCircle,
  },
};

function RunStatusBadge({ status }: { status: CheckRunStatus }) {
  const config = statusConfig[status] ?? statusConfig.completed;
  const Icon = config.icon;
  return (
    <span className={cn("inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium", config.className)}>
      <Icon className={cn("h-3 w-3", status === "running" && "animate-spin")} />
      {config.label}
    </span>
  );
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function formatDate(iso: string | null): string {
  if (!iso) return "—";
  const d = new Date(iso);
  return (
    d.toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" }) +
    " " +
    d.toLocaleTimeString(undefined, { hour: "2-digit", minute: "2-digit" })
  );
}

// ---------------------------------------------------------------------------
// Check Run Row
// ---------------------------------------------------------------------------

function CheckRunRow({ run }: { run: CheckRun }) {
  const [expanded, setExpanded] = useState(false);
  const hasError = !!run.error_log;

  return (
    <>
      <tr className="border-b border-border hover:bg-muted/50">
        <td className="px-4 py-3 text-sm text-muted-foreground">
          {formatDate(run.started_at)}
        </td>
        <td className="px-4 py-3 text-sm text-muted-foreground">
          {formatDate(run.completed_at)}
        </td>
        <td className="px-4 py-3">
          <RunStatusBadge status={run.status} />
        </td>
        <td className="px-4 py-3 text-center text-sm">{run.feeds_checked}</td>
        <td className="px-4 py-3 text-center text-sm">{run.new_items_found}</td>
        <td className="px-4 py-3 text-center text-sm">{run.cards_generated}</td>
        <td className="px-4 py-3 text-center">
          {hasError ? (
            <button
              onClick={() => setExpanded(!expanded)}
              className="inline-flex items-center gap-1 text-xs font-medium text-red-600 hover:text-red-800"
            >
              {expanded ? <ChevronDown className="h-3.5 w-3.5" /> : <ChevronRight className="h-3.5 w-3.5" />}
              View
            </button>
          ) : (
            <span className="text-xs text-muted-foreground">—</span>
          )}
        </td>
      </tr>
      {expanded && hasError && (
        <tr>
          <td colSpan={7} className="px-4 pb-3">
            <div className="rounded-md bg-red-50 px-3 py-2 text-xs font-mono text-red-800 whitespace-pre-wrap">
              {run.error_log}
            </div>
          </td>
        </tr>
      )}
    </>
  );
}

// ---------------------------------------------------------------------------
// Main Component
// ---------------------------------------------------------------------------

export function CheckRunsHistory() {
  const { data: runs, isLoading, error } = useCheckRuns();
  const triggerCheck = useTriggerFeedCheck();

  return (
    <div className="mt-10">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold">Check Run History</h2>
          <p className="mt-0.5 text-sm text-muted-foreground">
            Recent feed check runs and their results.
          </p>
        </div>
        <button
          onClick={() => triggerCheck.mutate()}
          disabled={triggerCheck.isPending}
          className="inline-flex items-center gap-1.5 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
        >
          {triggerCheck.isPending ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Play className="h-4 w-4" />
          )}
          Run Feed Check Now
        </button>
      </div>

      {/* Trigger error */}
      {triggerCheck.isError && (
        <div className="mt-3 flex items-start gap-2 rounded-md bg-red-50 px-4 py-3 text-sm text-red-700">
          <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
          Feed check failed. Please try again.
        </div>
      )}

      {/* Trigger success */}
      {triggerCheck.isSuccess && (
        <div className="mt-3 flex items-start gap-2 rounded-md bg-green-50 px-4 py-3 text-sm text-green-700">
          <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0" />
          Feed check completed — {triggerCheck.data.feeds_checked} feeds checked, {triggerCheck.data.new_items_found} new items found.
        </div>
      )}

      {/* Loading */}
      {isLoading && (
        <div className="mt-8 flex justify-center">
          <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="mt-4 rounded-md bg-red-50 px-4 py-3 text-sm text-red-700">
          Failed to load check run history.
        </div>
      )}

      {/* Empty state */}
      {runs && runs.length === 0 && (
        <div className="mt-8 flex flex-col items-center gap-2 text-center text-muted-foreground">
          <Clock className="h-8 w-8" />
          <p className="text-sm">No check runs yet. Click "Run Feed Check Now" to start.</p>
        </div>
      )}

      {/* Table */}
      {runs && runs.length > 0 && (
        <div className="mt-4 overflow-hidden rounded-lg border border-border">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-border bg-muted/50">
              <tr>
                <th className="px-4 py-3 font-medium">Started</th>
                <th className="px-4 py-3 font-medium">Completed</th>
                <th className="px-4 py-3 font-medium">Status</th>
                <th className="px-4 py-3 text-center font-medium">Feeds</th>
                <th className="px-4 py-3 text-center font-medium">New Items</th>
                <th className="px-4 py-3 text-center font-medium">Cards</th>
                <th className="px-4 py-3 text-center font-medium">Errors</th>
              </tr>
            </thead>
            <tbody>
              {runs.map((run) => (
                <CheckRunRow key={run.id} run={run} />
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

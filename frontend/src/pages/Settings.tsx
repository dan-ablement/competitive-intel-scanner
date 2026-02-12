import { useState } from "react";
import { useSettings } from "@/hooks/use-system";
import { useSuggestions, useApproveSuggestion, useRejectSuggestion } from "@/hooks/use-suggestions";
import { useTriggerProfileReview } from "@/hooks/use-system";
import type { ProfileUpdateSuggestion } from "@/types";
import { cn } from "@/lib/utils";
import {
  Clock,
  Calendar,
  Shield,
  Loader2,
  CheckCircle2,
  XCircle,
  RefreshCw,
  Lightbulb,
  Building2,
  Users,
  Tag,
} from "lucide-react";

// ---------------------------------------------------------------------------
// Schedule Section
// ---------------------------------------------------------------------------

interface ScheduleCheck {
  time: string;
  cron: string;
  purpose: string;
}

function ScheduleSection({ settings }: { settings: Record<string, unknown> }) {
  const feedChecks = (settings.feed_checks ?? []) as ScheduleCheck[];
  const maintenance = (settings.maintenance ?? {}) as Record<string, ScheduleCheck>;
  const profileReview = maintenance.profile_review;

  return (
    <section className="rounded-lg border border-border p-6">
      <div className="flex items-center gap-2 mb-4">
        <Clock className="h-5 w-5 text-muted-foreground" />
        <h2 className="text-lg font-semibold">Feed Check Schedule</h2>
      </div>
      <p className="text-sm text-muted-foreground mb-4">
        Automated feed checks run at these times (Eastern Time). Managed via Cloud Scheduler.
      </p>
      <div className="overflow-hidden rounded-md border border-border">
        <table className="w-full text-sm">
          <thead className="border-b border-border bg-muted/50">
            <tr>
              <th className="px-4 py-2 text-left font-medium">Time (ET)</th>
              <th className="px-4 py-2 text-left font-medium">Cron</th>
              <th className="px-4 py-2 text-left font-medium">Purpose</th>
            </tr>
          </thead>
          <tbody>
            {feedChecks.map((check, i) => (
              <tr key={i} className="border-b border-border last:border-0">
                <td className="px-4 py-2 font-mono text-xs">{check.time}</td>
                <td className="px-4 py-2 font-mono text-xs text-muted-foreground">{check.cron}</td>
                <td className="px-4 py-2">{check.purpose}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {profileReview && (
        <div className="mt-4">
          <div className="flex items-center gap-2 mb-2">
            <Calendar className="h-4 w-4 text-muted-foreground" />
            <h3 className="text-sm font-semibold">Weekly Maintenance</h3>
          </div>
          <div className="rounded-md border border-border px-4 py-3 bg-muted/30 text-sm">
            <span className="font-medium">Profile Review:</span>{" "}
            <span className="font-mono text-xs">{profileReview.time}</span>
            <span className="text-muted-foreground ml-2">— {profileReview.purpose}</span>
          </div>
        </div>
      )}
    </section>
  );
}

// ---------------------------------------------------------------------------
// Content Types Section
// ---------------------------------------------------------------------------

function ContentTypesSection({ contentTypes }: { contentTypes: string[] }) {
  return (
    <section className="rounded-lg border border-border p-6">
      <div className="flex items-center gap-2 mb-4">
        <Tag className="h-5 w-5 text-muted-foreground" />
        <h2 className="text-lg font-semibold">Content Types</h2>
      </div>
      <p className="text-sm text-muted-foreground mb-4">
        Event types used for analysis card classification.
      </p>
      <div className="flex flex-wrap gap-2">
        {contentTypes.map((ct) => (
          <span
            key={ct}
            className="inline-flex items-center rounded-full bg-secondary px-3 py-1 text-xs font-medium"
          >
            {ct.replace(/_/g, " ")}
          </span>
        ))}
      </div>
    </section>
  );
}

// ---------------------------------------------------------------------------
// Admins Section
// ---------------------------------------------------------------------------

function AdminsSection({ admins }: { admins: string[] }) {
  return (
    <section className="rounded-lg border border-border p-6">
      <div className="flex items-center gap-2 mb-4">
        <Shield className="h-5 w-5 text-muted-foreground" />
        <h2 className="text-lg font-semibold">Administrators</h2>
      </div>
      <p className="text-sm text-muted-foreground mb-4">
        Users with admin privileges for approving cards and managing the system.
      </p>
      <ul className="space-y-1">
        {admins.map((email) => (
          <li key={email} className="flex items-center gap-2 text-sm">
            <Users className="h-3.5 w-3.5 text-muted-foreground" />
            {email}
          </li>
        ))}
      </ul>
    </section>
  );
}

// ---------------------------------------------------------------------------
// Suggestion Card
// ---------------------------------------------------------------------------

function SuggestionCard({ suggestion }: { suggestion: ProfileUpdateSuggestion }) {
  const approve = useApproveSuggestion();
  const reject = useRejectSuggestion();
  const isActing = approve.isPending || reject.isPending;

  const targetLabel =
    suggestion.target_type === "augment"
      ? "Augment Code"
      : suggestion.competitor_name ?? "Unknown Competitor";

  return (
    <div className="rounded-lg border border-border p-4">
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            {suggestion.target_type === "augment" ? (
              <Building2 className="h-4 w-4 text-blue-500 shrink-0" />
            ) : (
              <Users className="h-4 w-4 text-orange-500 shrink-0" />
            )}
            <span className="text-sm font-semibold">{targetLabel}</span>
            <span className="rounded-full bg-muted px-2 py-0.5 text-xs font-medium text-muted-foreground">
              {suggestion.field.replace(/_/g, " ")}
            </span>
          </div>
          <p className="text-sm text-muted-foreground mt-1">{suggestion.reason}</p>
        </div>
      </div>

      <div className="mt-3 grid grid-cols-1 md:grid-cols-2 gap-3">
        <div className="rounded-md border border-border bg-red-50/50 p-3">
          <div className="text-xs font-medium text-red-700 mb-1">Current Value</div>
          <div className="text-sm whitespace-pre-wrap break-words">
            {suggestion.current_value || <span className="text-muted-foreground italic">Empty</span>}
          </div>
        </div>
        <div className="rounded-md border border-border bg-green-50/50 p-3">
          <div className="text-xs font-medium text-green-700 mb-1">Suggested Value</div>
          <div className="text-sm whitespace-pre-wrap break-words">{suggestion.suggested_value}</div>
        </div>
      </div>

      <div className="mt-3 flex items-center justify-end gap-2">
        <button
          onClick={() => reject.mutate(suggestion.id)}
          disabled={isActing}
          className="inline-flex items-center gap-1.5 rounded-md border border-input px-3 py-1.5 text-sm font-medium hover:bg-accent disabled:opacity-50"
        >
          {reject.isPending ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <XCircle className="h-3.5 w-3.5" />}
          Reject
        </button>
        <button
          onClick={() => approve.mutate(suggestion.id)}
          disabled={isActing}
          className="inline-flex items-center gap-1.5 rounded-md bg-primary px-3 py-1.5 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
        >
          {approve.isPending ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <CheckCircle2 className="h-3.5 w-3.5" />}
          Approve
        </button>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Suggestions Section
// ---------------------------------------------------------------------------

function SuggestionsSection() {
  const { data: suggestions, isLoading, error } = useSuggestions();
  const triggerReview = useTriggerProfileReview();
  const [filter, setFilter] = useState<"all" | "competitor" | "augment">("all");

  const filtered = suggestions?.filter((s) => {
    if (filter === "all") return true;
    return s.target_type === filter;
  });

  return (
    <section className="rounded-lg border border-border p-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Lightbulb className="h-5 w-5 text-muted-foreground" />
          <h2 className="text-lg font-semibold">Profile Update Suggestions</h2>
        </div>
        <button
          onClick={() => triggerReview.mutate()}
          disabled={triggerReview.isPending}
          className="inline-flex items-center gap-1.5 rounded-md border border-input px-3 py-1.5 text-sm font-medium hover:bg-accent disabled:opacity-50"
        >
          {triggerReview.isPending ? (
            <Loader2 className="h-3.5 w-3.5 animate-spin" />
          ) : (
            <RefreshCw className="h-3.5 w-3.5" />
          )}
          Run Review
        </button>
      </div>

      {/* Filter tabs */}
      <div className="flex gap-1 mb-4">
        {(["all", "competitor", "augment"] as const).map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={cn(
              "rounded-md px-3 py-1 text-sm font-medium transition-colors",
              filter === f
                ? "bg-primary text-primary-foreground"
                : "text-muted-foreground hover:bg-accent",
            )}
          >
            {f === "all" ? "All" : f === "competitor" ? "Competitors" : "Augment"}
          </button>
        ))}
      </div>

      {isLoading && (
        <div className="flex justify-center py-8">
          <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
        </div>
      )}

      {error && (
        <div className="rounded-md bg-red-50 px-4 py-3 text-sm text-red-700">
          Failed to load suggestions.
        </div>
      )}

      {filtered && filtered.length === 0 && (
        <div className="flex flex-col items-center gap-2 py-8 text-center text-muted-foreground">
          <Lightbulb className="h-8 w-8" />
          <p className="text-sm">No pending suggestions.</p>
          <p className="text-xs">Run a profile review to generate suggestions from recent analysis cards.</p>
        </div>
      )}

      {filtered && filtered.length > 0 && (
        <div className="space-y-3">
          {filtered.map((s) => (
            <SuggestionCard key={s.id} suggestion={s} />
          ))}
        </div>
      )}

      {triggerReview.isSuccess && (
        <div className="mt-3 rounded-md bg-green-50 px-4 py-2 text-sm text-green-700">
          Profile review completed successfully.
        </div>
      )}
      {triggerReview.isError && (
        <div className="mt-3 rounded-md bg-red-50 px-4 py-2 text-sm text-red-700">
          Profile review failed. Check server logs.
        </div>
      )}
    </section>
  );
}

// ---------------------------------------------------------------------------
// Main Page
// ---------------------------------------------------------------------------

export default function Settings() {
  const { data: settings, isLoading } = useSettings();

  return (
    <div>
      <h1 className="text-2xl font-bold">Settings</h1>
      <p className="mt-1 text-sm text-muted-foreground">
        System configuration, schedule, and profile update suggestions.
      </p>

      {isLoading && (
        <div className="mt-12 flex justify-center">
          <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
        </div>
      )}

      {settings && (
        <div className="mt-6 space-y-6">
          <SuggestionsSection />
          <ScheduleSection settings={settings as Record<string, unknown>} />
          <ContentTypesSection contentTypes={(settings as Record<string, unknown>).content_types as string[] ?? []} />
          <AdminsSection admins={(settings as Record<string, unknown>).admins as string[] ?? []} />
        </div>
      )}
    </div>
  );
}

import { Link } from "react-router-dom";
import { useBriefings } from "@/hooks/use-briefings";
import { useCards } from "@/hooks/use-cards";
import { useCheckRuns } from "@/hooks/use-system";
import { useSuggestions } from "@/hooks/use-suggestions";
import { useCompetitors } from "@/hooks/use-competitors";
import type { AnalysisCard, Priority, CheckRun, Briefing } from "@/types";
import { cn } from "@/lib/utils";
import {
  Loader2,
  FileText,
  CreditCard,
  AlertCircle,
  CheckCircle2,
  XCircle,
  Clock,
  ArrowRight,
  Users,
  Lightbulb,
  Eye,
} from "lucide-react";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function formatDateTime(iso: string | null): string {
  if (!iso) return "—";
  const d = new Date(iso);
  return (
    d.toLocaleDateString(undefined, { month: "short", day: "numeric" }) +
    " " +
    d.toLocaleTimeString(undefined, { hour: "2-digit", minute: "2-digit" })
  );
}

function formatRelativeTime(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

function todayDateString(): string {
  const d = new Date();
  return d.toISOString().split("T")[0];
}

// ---------------------------------------------------------------------------
// Priority Count Card
// ---------------------------------------------------------------------------

function PriorityCountCard({
  priority,
  count,
  label,
}: {
  priority: Priority;
  count: number;
  label: string;
}) {
  const config = {
    red: {
      bg: "bg-red-50 border-red-200",
      dot: "bg-red-500",
      text: "text-red-700",
      count: "text-red-900",
    },
    yellow: {
      bg: "bg-amber-50 border-amber-200",
      dot: "bg-amber-400",
      text: "text-amber-700",
      count: "text-amber-900",
    },
    green: {
      bg: "bg-green-50 border-green-200",
      dot: "bg-green-500",
      text: "text-green-700",
      count: "text-green-900",
    },
  }[priority];

  return (
    <Link
      to={`/cards?priority=${priority}`}
      className={cn(
        "flex items-center gap-4 rounded-lg border p-4 transition-colors hover:shadow-sm",
        config.bg
      )}
    >
      <span className={cn("h-3 w-3 rounded-full", config.dot)} />
      <div>
        <div className={cn("text-2xl font-bold", config.count)}>{count}</div>
        <div className={cn("text-sm font-medium", config.text)}>{label}</div>
      </div>
    </Link>
  );
}

// ---------------------------------------------------------------------------
// Briefing Section
// ---------------------------------------------------------------------------

function BriefingSection({ briefings }: { briefings: Briefing[] }) {
  const today = todayDateString();
  const todayBriefing = briefings.find((b) => b.date === today);

  if (!todayBriefing) {
    return (
      <div className="rounded-lg border border-border bg-card p-6">
        <div className="flex items-center gap-2">
          <FileText className="h-5 w-5 text-muted-foreground" />
          <h2 className="text-lg font-semibold">Today's Briefing</h2>
        </div>
        <p className="mt-3 text-sm text-muted-foreground">
          No briefing yet today. Briefings are generated after the morning feed check.
        </p>
        <Link
          to="/briefings"
          className="mt-3 inline-flex items-center gap-1 text-sm font-medium text-primary hover:underline"
        >
          View all briefings <ArrowRight className="h-3.5 w-3.5" />
        </Link>
      </div>
    );
  }

  const statusConfig = {
    draft: { label: "Draft", className: "bg-gray-100 text-gray-700 border-gray-200" },
    in_review: { label: "In Review", className: "bg-blue-100 text-blue-700 border-blue-200" },
    approved: { label: "Approved", className: "bg-green-100 text-green-700 border-green-200" },
    archived: { label: "Archived", className: "bg-muted text-muted-foreground border-border" },
  };
  const sc = statusConfig[todayBriefing.status];
  const cardCount = todayBriefing.cards?.length ?? 0;

  return (
    <Link
      to={`/briefings/${todayBriefing.id}`}
      className="block rounded-lg border border-border bg-card p-6 transition-colors hover:bg-muted/30"
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <FileText className="h-5 w-5 text-primary" />
          <h2 className="text-lg font-semibold">Today's Briefing</h2>
        </div>
        <span
          className={cn(
            "inline-flex rounded-full border px-2 py-0.5 text-xs font-medium",
            sc.className
          )}
        >
          {sc.label}
        </span>
      </div>
      <p className="mt-2 text-sm text-muted-foreground">
        {cardCount} analysis {cardCount === 1 ? "card" : "cards"} included
      </p>
      <span className="mt-3 inline-flex items-center gap-1 text-sm font-medium text-primary">
        View briefing <ArrowRight className="h-3.5 w-3.5" />
      </span>
    </Link>
  );
}


// ---------------------------------------------------------------------------
// Check Run Section
// ---------------------------------------------------------------------------

function CheckRunSection({ runs }: { runs: CheckRun[] }) {
  const latest = runs[0];

  if (!latest) {
    return (
      <div className="rounded-lg border border-border bg-card p-6">
        <div className="flex items-center gap-2">
          <Clock className="h-5 w-5 text-muted-foreground" />
          <h2 className="text-lg font-semibold">Latest Check Run</h2>
        </div>
        <p className="mt-3 text-sm text-muted-foreground">
          No check runs yet. Feed checks run automatically on schedule.
        </p>
      </div>
    );
  }

  const statusIcon = {
    running: <Loader2 className="h-4 w-4 animate-spin text-blue-600" />,
    completed: <CheckCircle2 className="h-4 w-4 text-green-600" />,
    failed: <XCircle className="h-4 w-4 text-red-600" />,
  }[latest.status];

  const statusLabel = {
    running: "Running",
    completed: "Completed",
    failed: "Failed",
  }[latest.status];

  return (
    <div className="rounded-lg border border-border bg-card p-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Clock className="h-5 w-5 text-muted-foreground" />
          <h2 className="text-lg font-semibold">Latest Check Run</h2>
        </div>
        <div className="flex items-center gap-1.5 text-sm">
          {statusIcon}
          <span className="font-medium">{statusLabel}</span>
        </div>
      </div>
      <div className="mt-3 grid grid-cols-3 gap-4 text-center">
        <div>
          <div className="text-xl font-bold">{latest.feeds_checked}</div>
          <div className="text-xs text-muted-foreground">Feeds checked</div>
        </div>
        <div>
          <div className="text-xl font-bold">{latest.new_items_found}</div>
          <div className="text-xs text-muted-foreground">Items found</div>
        </div>
        <div>
          <div className="text-xl font-bold">{latest.cards_generated}</div>
          <div className="text-xs text-muted-foreground">Cards generated</div>
        </div>
      </div>
      <div className="mt-3 text-xs text-muted-foreground">
        {formatDateTime(latest.started_at)}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Pending Items Section
// ---------------------------------------------------------------------------

function PendingItemRow({
  icon: Icon,
  label,
  count,
  to,
}: {
  icon: typeof AlertCircle;
  label: string;
  count: number;
  to: string;
}) {
  if (count === 0) return null;
  return (
    <Link
      to={to}
      className="flex items-center justify-between rounded-md px-3 py-2.5 transition-colors hover:bg-muted/50"
    >
      <div className="flex items-center gap-3">
        <Icon className="h-4 w-4 text-muted-foreground" />
        <span className="text-sm">{label}</span>
      </div>
      <span className="rounded-full bg-primary/10 px-2 py-0.5 text-xs font-semibold text-primary">
        {count}
      </span>
    </Link>
  );
}

function PendingItemsSection({
  draftCards,
  inReviewCards,
  pendingSuggestions,
  suggestedCompetitors,
}: {
  draftCards: number;
  inReviewCards: number;
  pendingSuggestions: number;
  suggestedCompetitors: number;
}) {
  const total = draftCards + inReviewCards + pendingSuggestions + suggestedCompetitors;

  return (
    <div className="rounded-lg border border-border bg-card p-6">
      <div className="flex items-center gap-2">
        <AlertCircle className="h-5 w-5 text-muted-foreground" />
        <h2 className="text-lg font-semibold">Pending Items</h2>
        {total > 0 && (
          <span className="rounded-full bg-amber-100 px-2 py-0.5 text-xs font-semibold text-amber-800">
            {total}
          </span>
        )}
      </div>
      {total === 0 ? (
        <p className="mt-3 text-sm text-muted-foreground">
          All caught up! No items need attention.
        </p>
      ) : (
        <div className="mt-3 divide-y divide-border">
          <PendingItemRow
            icon={CreditCard}
            label="Draft cards needing review"
            count={draftCards}
            to="/cards"
          />
          <PendingItemRow
            icon={Eye}
            label="Cards in review needing approval"
            count={inReviewCards}
            to="/cards"
          />
          <PendingItemRow
            icon={Lightbulb}
            label="Profile update suggestions"
            count={pendingSuggestions}
            to="/settings"
          />
          <PendingItemRow
            icon={Users}
            label="Suggested competitors pending approval"
            count={suggestedCompetitors}
            to="/competitors"
          />
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Recent Cards Section
// ---------------------------------------------------------------------------

function PriorityBadge({ priority }: { priority: Priority }) {
  const config = {
    red: { bg: "bg-red-100 text-red-800 border-red-200", dot: "bg-red-500", label: "R" },
    yellow: { bg: "bg-amber-100 text-amber-800 border-amber-200", dot: "bg-amber-400", label: "Y" },
    green: { bg: "bg-green-100 text-green-800 border-green-200", dot: "bg-green-500", label: "G" },
  }[priority];

  return (
    <span className={cn("inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-xs font-semibold", config.bg)}>
      <span className={cn("h-2 w-2 rounded-full", config.dot)} />
      {config.label}
    </span>
  );
}

function RecentCardsSection({ cards }: { cards: AnalysisCard[] }) {
  const recent = [...cards]
    .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
    .slice(0, 5);

  return (
    <div className="rounded-lg border border-border bg-card p-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <CreditCard className="h-5 w-5 text-muted-foreground" />
          <h2 className="text-lg font-semibold">Recent Analysis Cards</h2>
        </div>
        <Link
          to="/cards"
          className="inline-flex items-center gap-1 text-sm font-medium text-primary hover:underline"
        >
          View all <ArrowRight className="h-3.5 w-3.5" />
        </Link>
      </div>
      {recent.length === 0 ? (
        <p className="mt-3 text-sm text-muted-foreground">
          No analysis cards yet. Cards will appear once feeds are processed.
        </p>
      ) : (
        <div className="mt-3 divide-y divide-border">
          {recent.map((card) => (
            <Link
              key={card.id}
              to={`/cards/${card.id}`}
              className="flex items-center gap-3 py-2.5 transition-colors hover:bg-muted/30 rounded-md px-2"
            >
              <PriorityBadge priority={card.priority} />
              <span className="min-w-0 flex-1 truncate text-sm font-medium">
                {card.title}
              </span>
              <span className="shrink-0 text-xs text-muted-foreground">
                {formatRelativeTime(card.created_at)}
              </span>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main Dashboard
// ---------------------------------------------------------------------------

export default function Dashboard() {
  const { data: cards, isLoading: cardsLoading } = useCards();
  const { data: briefings, isLoading: briefingsLoading } = useBriefings();
  const { data: checkRuns, isLoading: checkRunsLoading } = useCheckRuns();
  const { data: suggestions, isLoading: suggestionsLoading } = useSuggestions();
  const { data: suggestedCompetitors, isLoading: competitorsLoading } = useCompetitors({ is_suggested: true });

  const isLoading = cardsLoading || briefingsLoading || checkRunsLoading || suggestionsLoading || competitorsLoading;

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  // Compute priority counts from cards created in the last 24 hours
  const now = Date.now();
  const oneDayAgo = now - 24 * 60 * 60 * 1000;
  const recentCards = (cards ?? []).filter(
    (c) => new Date(c.created_at).getTime() >= oneDayAgo
  );
  const redCount = recentCards.filter((c) => c.priority === "red").length;
  const yellowCount = recentCards.filter((c) => c.priority === "yellow").length;
  const greenCount = recentCards.filter((c) => c.priority === "green").length;

  // Pending counts
  const draftCards = (cards ?? []).filter((c) => c.status === "draft").length;
  const inReviewCards = (cards ?? []).filter((c) => c.status === "in_review").length;
  const pendingSuggestions = (suggestions ?? []).filter((s) => s.status === "pending").length;
  const suggestedCount = (suggestedCompetitors ?? []).length;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold">Dashboard</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Competitive intelligence overview and recent activity.
        </p>
      </div>

      {/* Priority counts — prominent cards at top */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <PriorityCountCard priority="red" count={redCount} label="Red — last 24h" />
        <PriorityCountCard priority="yellow" count={yellowCount} label="Yellow — last 24h" />
        <PriorityCountCard priority="green" count={greenCount} label="Green — last 24h" />
      </div>

      {/* Briefing + Check Run row */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <BriefingSection briefings={briefings ?? []} />
        <CheckRunSection runs={checkRuns ?? []} />
      </div>

      {/* Pending items + Recent cards row */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <PendingItemsSection
          draftCards={draftCards}
          inReviewCards={inReviewCards}
          pendingSuggestions={pendingSuggestions}
          suggestedCompetitors={suggestedCount}
        />
        <RecentCardsSection cards={cards ?? []} />
      </div>
    </div>
  );
}
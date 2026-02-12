import { useState } from "react";
import { Link } from "react-router-dom";
import { useCards } from "@/hooks/use-cards";
import { useCompetitors } from "@/hooks/use-competitors";
import type { CardFilters } from "@/api/cards";
import type { AnalysisCard, CardStatus, Priority, EventType } from "@/types";
import { cn } from "@/lib/utils";
import { Loader2, Search, CreditCard, Filter, X } from "lucide-react";

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const STATUS_OPTIONS: { value: CardStatus; label: string }[] = [
  { value: "draft", label: "Draft" },
  { value: "in_review", label: "In Review" },
  { value: "approved", label: "Approved" },
  { value: "archived", label: "Archived" },
];

const PRIORITY_OPTIONS: { value: Priority; label: string }[] = [
  { value: "red", label: "Red" },
  { value: "yellow", label: "Yellow" },
  { value: "green", label: "Green" },
];

const EVENT_TYPE_LABELS: Record<EventType, string> = {
  new_feature: "New Feature",
  product_announcement: "Product Announcement",
  partnership: "Partnership",
  acquisition: "Acquisition",
  acquired: "Acquired",
  funding: "Funding",
  pricing_change: "Pricing Change",
  leadership_change: "Leadership Change",
  expansion: "Expansion",
  other: "Other",
};

// ---------------------------------------------------------------------------
// Helper components
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

function CardStatusBadge({ status }: { status: CardStatus }) {
  const config: Record<CardStatus, string> = {
    draft: "bg-gray-100 text-gray-700 border-gray-200",
    in_review: "bg-blue-100 text-blue-700 border-blue-200",
    approved: "bg-green-100 text-green-700 border-green-200",
    archived: "bg-muted text-muted-foreground border-border",
  };
  const labels: Record<CardStatus, string> = {
    draft: "Draft",
    in_review: "In Review",
    approved: "Approved",
    archived: "Archived",
  };

  return (
    <span className={cn("inline-flex rounded-full border px-2 py-0.5 text-xs font-medium", config[status])}>
      {labels[status]}
    </span>
  );
}

function formatDate(iso: string | null): string {
  if (!iso) return "—";
  const d = new Date(iso);
  return d.toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" });
}

// ---------------------------------------------------------------------------
// Card Row
// ---------------------------------------------------------------------------

function CardRow({ card }: { card: AnalysisCard }) {
  return (
    <Link
      to={`/cards/${card.id}`}
      className="flex items-center gap-4 border-b border-border px-4 py-3 transition-colors hover:bg-muted/50 last:border-b-0"
    >
      {/* Priority */}
      <PriorityBadge priority={card.priority} />

      {/* Title + event type */}
      <div className="min-w-0 flex-1">
        <div className="truncate font-medium">{card.title}</div>
        <div className="mt-0.5 flex flex-wrap items-center gap-2">
          <span className="rounded bg-secondary px-1.5 py-0.5 text-xs text-secondary-foreground">
            {EVENT_TYPE_LABELS[card.event_type] ?? card.event_type}
          </span>
          {card.competitors.map((c) => (
            <span
              key={c.id}
              className="rounded bg-violet-100 px-1.5 py-0.5 text-xs text-violet-700"
            >
              {c.name}
            </span>
          ))}
        </div>
      </div>

      {/* Status */}
      <CardStatusBadge status={card.status} />

      {/* Date */}
      <span className="hidden shrink-0 text-xs text-muted-foreground sm:block">
        {formatDate(card.created_at)}
      </span>
    </Link>
  );
}

// ---------------------------------------------------------------------------
// Main Page
// ---------------------------------------------------------------------------

export default function Cards() {
  const [filters, setFilters] = useState<CardFilters>({});
  const [search, setSearch] = useState("");
  const [showFilters, setShowFilters] = useState(false);

  const { data: cards, isLoading, error } = useCards(filters);
  const { data: competitors } = useCompetitors();

  const hasActiveFilters = !!(filters.status || filters.priority || filters.competitor_id || filters.date_from || filters.date_to);

  const filtered = (cards ?? []).filter((c) =>
    !search || c.title.toLowerCase().includes(search.toLowerCase())
  );

  function clearFilters() {
    setFilters({});
  }

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
        Failed to load analysis cards.
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Analysis Cards</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Browse and manage competitive intelligence analysis cards.
          </p>
        </div>
        <button
          onClick={() => setShowFilters(!showFilters)}
          className={cn(
            "inline-flex items-center gap-2 rounded-md border px-4 py-2 text-sm font-medium transition-colors",
            showFilters || hasActiveFilters
              ? "border-primary bg-primary/10 text-primary"
              : "border-input hover:bg-muted"
          )}
        >
          <Filter className="h-4 w-4" />
          Filters
          {hasActiveFilters && (
            <span className="rounded-full bg-primary px-1.5 py-0.5 text-xs text-primary-foreground">
              !
            </span>
          )}
        </button>
      </div>

      {/* Filter bar */}
      {showFilters && (
        <div className="rounded-lg border border-border bg-card p-4 shadow-sm">
          <div className="mb-3 flex items-center justify-between">
            <h3 className="text-sm font-medium">Filters</h3>
            {hasActiveFilters && (
              <button
                onClick={clearFilters}
                className="inline-flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground"
              >
                <X className="h-3 w-3" />
                Clear all
              </button>
            )}
          </div>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            {/* Status */}
            <div>
              <label className="mb-1 block text-xs font-medium text-muted-foreground">Status</label>
              <select
                value={filters.status ?? ""}
                onChange={(e) => setFilters((f) => ({ ...f, status: (e.target.value || undefined) as CardStatus | undefined }))}
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
              >
                <option value="">All statuses</option>
                {STATUS_OPTIONS.map((s) => (
                  <option key={s.value} value={s.value}>{s.label}</option>
                ))}
              </select>
            </div>

            {/* Priority */}
            <div>
              <label className="mb-1 block text-xs font-medium text-muted-foreground">Priority</label>
              <select
                value={filters.priority ?? ""}
                onChange={(e) => setFilters((f) => ({ ...f, priority: (e.target.value || undefined) as Priority | undefined }))}
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
              >
                <option value="">All priorities</option>
                {PRIORITY_OPTIONS.map((p) => (
                  <option key={p.value} value={p.value}>{p.label}</option>
                ))}
              </select>
            </div>

            {/* Competitor */}
            <div>
              <label className="mb-1 block text-xs font-medium text-muted-foreground">Competitor</label>
              <select
                value={filters.competitor_id ?? ""}
                onChange={(e) => setFilters((f) => ({ ...f, competitor_id: e.target.value || undefined }))}
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
              >
                <option value="">All competitors</option>
                {competitors?.map((c) => (
                  <option key={c.id} value={c.id}>{c.name}</option>
                ))}
              </select>
            </div>

            {/* Date range */}
            <div>
              <label className="mb-1 block text-xs font-medium text-muted-foreground">Date range</label>
              <div className="flex gap-2">
                <input
                  type="date"
                  value={filters.date_from ?? ""}
                  onChange={(e) => setFilters((f) => ({ ...f, date_from: e.target.value || undefined }))}
                  className="w-full rounded-md border border-input bg-background px-2 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                />
                <input
                  type="date"
                  value={filters.date_to ?? ""}
                  onChange={(e) => setFilters((f) => ({ ...f, date_to: e.target.value || undefined }))}
                  className="w-full rounded-md border border-input bg-background px-2 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                />
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search cards by title..."
          className="w-full rounded-md border border-input bg-background py-2 pl-10 pr-3 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
        />
      </div>

      {/* Card list */}
      {filtered.length === 0 ? (
        <div className="flex flex-col items-center gap-2 py-12 text-center text-muted-foreground">
          <CreditCard className="h-10 w-10" />
          <p className="text-lg font-medium">No analysis cards</p>
          <p className="text-sm">
            {search || hasActiveFilters
              ? "No cards match your current filters."
              : "Cards will appear here once feeds are processed."}
          </p>
        </div>
      ) : (
        <div className="overflow-hidden rounded-lg border border-border">
          {filtered.map((card) => (
            <CardRow key={card.id} card={card} />
          ))}
        </div>
      )}
    </div>
  );
}


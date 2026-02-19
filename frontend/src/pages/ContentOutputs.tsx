import { useState } from "react";
import { Link } from "react-router-dom";
import { useContentOutputs, useGenerateDraft } from "@/hooks/use-content-outputs";
import { useContentTemplates } from "@/hooks/use-content-templates";
import { useCompetitors } from "@/hooks/use-competitors";
import type { ContentOutputFilters } from "@/api/content-outputs";
import type { ContentOutput, ContentOutputStatus } from "@/types";
import { cn } from "@/lib/utils";
import {
  Loader2,
  Search,
  FileText,
  Filter,
  X,
  RefreshCw,
  Plus,
  ExternalLink,
} from "lucide-react";

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const STATUS_OPTIONS: { value: ContentOutputStatus; label: string }[] = [
  { value: "draft", label: "Draft" },
  { value: "in_review", label: "In Review" },
  { value: "approved", label: "Approved" },
  { value: "published", label: "Published" },
  { value: "failed", label: "Failed" },
];

const STATUS_BADGE_CONFIG: Record<ContentOutputStatus, string> = {
  draft: "bg-gray-100 text-gray-700 border-gray-200",
  in_review: "bg-blue-100 text-blue-700 border-blue-200",
  approved: "bg-green-100 text-green-700 border-green-200",
  published: "bg-purple-100 text-purple-700 border-purple-200",
  failed: "bg-red-100 text-red-700 border-red-200",
};

const STATUS_LABELS: Record<ContentOutputStatus, string> = {
  draft: "Draft",
  in_review: "In Review",
  approved: "Approved",
  published: "Published",
  failed: "Failed",
};

// ---------------------------------------------------------------------------
// Helper components
// ---------------------------------------------------------------------------

export function ContentStatusBadge({ status }: { status: ContentOutputStatus }) {
  return (
    <span
      className={cn(
        "inline-flex rounded-full border px-2 py-0.5 text-xs font-medium",
        STATUS_BADGE_CONFIG[status]
      )}
    >
      {STATUS_LABELS[status]}
    </span>
  );
}

function formatDate(iso: string | null): string {
  if (!iso) return "—";
  const d = new Date(iso);
  return d.toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" });
}

// ---------------------------------------------------------------------------
// Content Output Row
// ---------------------------------------------------------------------------

function ContentOutputRow({ output }: { output: ContentOutput }) {
  return (
    <Link
      to={`/content/${output.id}`}
      className="flex items-center gap-4 border-b border-border px-4 py-3 transition-colors hover:bg-muted/50 last:border-b-0"
    >
      {/* Title + type + competitor */}
      <div className="min-w-0 flex-1">
        <div className="truncate font-medium">{output.title}</div>
        <div className="mt-0.5 flex flex-wrap items-center gap-2">
          <span className="rounded bg-secondary px-1.5 py-0.5 text-xs text-secondary-foreground">
            {output.content_type}
          </span>
          {output.competitor_name && (
            <span className="rounded bg-violet-100 px-1.5 py-0.5 text-xs text-violet-700">
              {output.competitor_name}
            </span>
          )}
        </div>
      </div>

      {/* Status */}
      <ContentStatusBadge status={output.status} />

      {/* Google Doc link */}
      {output.google_doc_url && (
        <a
          href={output.google_doc_url}
          target="_blank"
          rel="noopener noreferrer"
          onClick={(e) => e.stopPropagation()}
          className="hidden shrink-0 items-center gap-1 text-xs text-blue-600 hover:underline sm:inline-flex"
        >
          <ExternalLink className="h-3 w-3" />
          Doc
        </a>
      )}

      {/* Date */}
      <span className="hidden shrink-0 text-xs text-muted-foreground sm:block">
        {formatDate(output.updated_at)}
      </span>
    </Link>
  );
}

// ---------------------------------------------------------------------------
// Generate Modal
// ---------------------------------------------------------------------------

function GenerateModal({
  onClose,
  onGenerate,
  isGenerating,
}: {
  onClose: () => void;
  onGenerate: (competitorId: string, templateId: string) => void;
  isGenerating: boolean;
}) {
  const { data: competitors } = useCompetitors();
  const { data: templates } = useContentTemplates();
  const [competitorId, setCompetitorId] = useState("");
  const [templateId, setTemplateId] = useState("");

  const activeTemplates = (templates ?? []).filter((t) => t.is_active);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="w-full max-w-md rounded-lg border border-border bg-background p-6 shadow-lg">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-lg font-semibold">Generate New Content</h2>
          <button onClick={onClose} className="rounded-md p-1 hover:bg-muted">
            <X className="h-4 w-4" />
          </button>
        </div>

        <div className="space-y-4">
          <div>
            <label className="mb-1 block text-sm font-medium">Competitor</label>
            <select
              value={competitorId}
              onChange={(e) => setCompetitorId(e.target.value)}
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
            >
              <option value="">Select a competitor...</option>
              {competitors?.map((c) => (
                <option key={c.id} value={c.id}>{c.name}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="mb-1 block text-sm font-medium">Template</label>
            <select
              value={templateId}
              onChange={(e) => setTemplateId(e.target.value)}
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
            >
              <option value="">Select a template...</option>
              {activeTemplates.map((t) => (
                <option key={t.id} value={t.id}>{t.name} ({t.content_type})</option>
              ))}
            </select>
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <button
              onClick={onClose}
              className="rounded-md border border-input px-4 py-2 text-sm font-medium hover:bg-muted"
            >
              Cancel
            </button>
            <button
              onClick={() => onGenerate(competitorId, templateId)}
              disabled={!competitorId || !templateId || isGenerating}
              className="inline-flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
            >
              {isGenerating && <Loader2 className="h-4 w-4 animate-spin" />}
              Generate
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main Page
// ---------------------------------------------------------------------------

export default function ContentOutputs() {
  const [filters, setFilters] = useState<ContentOutputFilters>({});
  const [search, setSearch] = useState("");
  const [showFilters, setShowFilters] = useState(false);
  const [showGenerateModal, setShowGenerateModal] = useState(false);

  const { data: outputs, isLoading, error, refetch } = useContentOutputs(filters);
  const { data: competitors } = useCompetitors();
  const generateMutation = useGenerateDraft();

  const hasActiveFilters = !!(filters.status || filters.competitor_id || filters.content_type);

  const filtered = (outputs ?? []).filter(
    (o) => !search || o.title.toLowerCase().includes(search.toLowerCase())
  );

  function clearFilters() {
    setFilters({});
  }

  async function handleGenerate(competitorId: string, templateId: string) {
    await generateMutation.mutateAsync({ competitorId, templateId });
    setShowGenerateModal(false);
  }

  // Get unique content types from the data for the filter dropdown
  const contentTypes = [...new Set((outputs ?? []).map((o) => o.content_type))];

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
        <div className="flex items-center justify-between">
          <span>Failed to load content outputs.</span>
          <button
            onClick={() => refetch()}
            className="inline-flex items-center gap-1.5 rounded-md border border-destructive/30 px-3 py-1.5 text-sm font-medium hover:bg-destructive/10"
          >
            <RefreshCw className="h-3.5 w-3.5" /> Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Content Outputs</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            {filtered.length} content output{filtered.length !== 1 ? "s" : ""}
          </p>
        </div>
        <div className="flex items-center gap-2">
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
              <span className="rounded-full bg-primary px-1.5 py-0.5 text-xs text-primary-foreground">!</span>
            )}
          </button>
          <button
            onClick={() => setShowGenerateModal(true)}
            className="inline-flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
          >
            <Plus className="h-4 w-4" />
            Generate New
          </button>
        </div>
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
          <div className="grid gap-3 sm:grid-cols-3">
            {/* Status */}
            <div>
              <label className="mb-1 block text-xs font-medium text-muted-foreground">Status</label>
              <select
                value={filters.status ?? ""}
                onChange={(e) =>
                  setFilters((f) => ({
                    ...f,
                    status: (e.target.value || undefined) as ContentOutputStatus | undefined,
                  }))
                }
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
              >
                <option value="">All statuses</option>
                {STATUS_OPTIONS.map((s) => (
                  <option key={s.value} value={s.value}>{s.label}</option>
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

            {/* Content Type */}
            <div>
              <label className="mb-1 block text-xs font-medium text-muted-foreground">Content Type</label>
              <select
                value={filters.content_type ?? ""}
                onChange={(e) => setFilters((f) => ({ ...f, content_type: e.target.value || undefined }))}
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
              >
                <option value="">All types</option>
                {contentTypes.map((t) => (
                  <option key={t} value={t}>{t}</option>
                ))}
              </select>
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
          placeholder="Search content by title..."
          className="w-full rounded-md border border-input bg-background py-2 pl-10 pr-3 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
        />
      </div>

      {/* Content list */}
      {filtered.length === 0 ? (
        <div className="flex flex-col items-center gap-2 py-12 text-center text-muted-foreground">
          <FileText className="h-10 w-10" />
          <p className="text-lg font-medium">No content outputs</p>
          <p className="text-sm">
            {search || hasActiveFilters
              ? "No content matches your current filters."
              : "Generate content by clicking the button above."}
          </p>
        </div>
      ) : (
        <div className="overflow-hidden rounded-lg border border-border">
          {filtered.map((output) => (
            <ContentOutputRow key={output.id} output={output} />
          ))}
        </div>
      )}

      {/* Generate Modal */}
      {showGenerateModal && (
        <GenerateModal
          onClose={() => setShowGenerateModal(false)}
          onGenerate={handleGenerate}
          isGenerating={generateMutation.isPending}
        />
      )}

      {/* Generate error */}
      {generateMutation.isError && (
        <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-3 text-sm text-destructive">
          Failed to generate content. Please try again.
        </div>
      )}
    </div>
  );
}

import { useState } from "react";
import {
  useFeeds,
  useCreateFeed,
  useUpdateFeed,
  useDeleteFeed,
  useTestFeed,
  useTestFeedUrl,
} from "@/hooks/use-feeds";
import { useCompetitors } from "@/hooks/use-competitors";
import { CheckRunsHistory } from "@/components/common/CheckRunsHistory";
import type { RssFeed } from "@/types";
import type { TestFeedResult } from "@/api/feeds";
import { cn } from "@/lib/utils";
import {
  Plus,
  FlaskConical,
  Pencil,
  Loader2,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Rss,
  ExternalLink,
  RefreshCw,
} from "lucide-react";

// ---------------------------------------------------------------------------
// Feed Form Dialog
// ---------------------------------------------------------------------------

interface FeedFormProps {
  open: boolean;
  onClose: () => void;
  feed?: RssFeed | null;
}

function FeedFormDialog({ open, onClose, feed }: FeedFormProps) {
  const isEdit = !!feed;
  const [name, setName] = useState(feed?.name ?? "");
  const [url, setUrl] = useState(feed?.url ?? "");
  const [competitorId, setCompetitorId] = useState(feed?.competitor_id ?? "");
  const [testResult, setTestResult] = useState<TestFeedResult | null>(null);

  const { data: competitors } = useCompetitors();
  const createFeed = useCreateFeed();
  const updateFeed = useUpdateFeed();
  const testFeedUrl = useTestFeedUrl();

  const isSaving = createFeed.isPending || updateFeed.isPending;
  const isTesting = testFeedUrl.isPending;

  function handleTest() {
    if (!url) return;
    setTestResult(null);
    testFeedUrl.mutate(url, {
      onSuccess: (result) => setTestResult(result),
      onError: () =>
        setTestResult({ success: false, message: "Network error testing feed.", item_count: 0 }),
    });
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const payload = {
      name,
      url,
      competitor_id: competitorId || null,
    };

    if (isEdit && feed) {
      updateFeed.mutate(
        { id: feed.id, feed: payload },
        { onSuccess: () => { onClose(); } },
      );
    } else {
      createFeed.mutate(payload, {
        onSuccess: () => { onClose(); },
      });
    }
  }

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="w-full max-w-lg rounded-lg border border-border bg-background p-6 shadow-lg">
        <h2 className="text-lg font-semibold">{isEdit ? "Edit Feed" : "Add Feed"}</h2>

        <form onSubmit={handleSubmit} className="mt-4 space-y-4">
          {/* Name */}
          <div>
            <label className="mb-1 block text-sm font-medium">Name</label>
            <input
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. TechCrunch AI"
              required
            />
          </div>

          {/* URL + Test */}
          <div>
            <label className="mb-1 block text-sm font-medium">Feed URL</label>
            <div className="flex gap-2">
              <input
                className="flex-1 rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                value={url}
                onChange={(e) => { setUrl(e.target.value); setTestResult(null); }}
                placeholder="https://example.com/feed.xml"
                required
              />
              <button
                type="button"
                onClick={handleTest}
                disabled={!url || isTesting}
                className="inline-flex items-center gap-1.5 rounded-md border border-input bg-secondary px-3 py-2 text-sm font-medium hover:bg-accent disabled:opacity-50"
              >
                {isTesting ? <Loader2 className="h-4 w-4 animate-spin" /> : <FlaskConical className="h-4 w-4" />}
                Test
              </button>
            </div>
            {testResult && (
              <div
                className={cn(
                  "mt-2 flex items-start gap-2 rounded-md px-3 py-2 text-sm",
                  testResult.success ? "bg-green-50 text-green-800" : "bg-red-50 text-red-800",
                )}
              >
                {testResult.success ? (
                  <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0" />
                ) : (
                  <XCircle className="mt-0.5 h-4 w-4 shrink-0" />
                )}
                <span>{testResult.message}</span>
              </div>
            )}
          </div>

          {/* Competitor */}
          <div>
            <label className="mb-1 block text-sm font-medium">Linked Competitor (optional)</label>
            <select
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
              value={competitorId}
              onChange={(e) => setCompetitorId(e.target.value)}
            >
              <option value="">— None —</option>
              {competitors?.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </select>
          </div>

          {/* Actions */}
          <div className="flex justify-end gap-2 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="rounded-md border border-input px-4 py-2 text-sm font-medium hover:bg-accent"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSaving}
              className="inline-flex items-center gap-1.5 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
            >
              {isSaving && <Loader2 className="h-4 w-4 animate-spin" />}
              {isEdit ? "Save Changes" : "Add Feed"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}


// ---------------------------------------------------------------------------
// Feed Row
// ---------------------------------------------------------------------------

function StatusBadge({ feed }: { feed: RssFeed }) {
  if (!feed.is_active) {
    return (
      <span className="inline-flex items-center gap-1 rounded-full bg-muted px-2 py-0.5 text-xs font-medium text-muted-foreground">
        Inactive
      </span>
    );
  }
  if (feed.error_count > 0) {
    return (
      <span className="inline-flex items-center gap-1 rounded-full bg-red-100 px-2 py-0.5 text-xs font-medium text-red-700">
        <AlertTriangle className="h-3 w-3" />
        Error ({feed.error_count})
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1 rounded-full bg-green-100 px-2 py-0.5 text-xs font-medium text-green-700">
      <CheckCircle2 className="h-3 w-3" />
      Active
    </span>
  );
}

function formatDate(iso: string | null): string {
  if (!iso) return "—";
  const d = new Date(iso);
  return d.toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" }) +
    " " +
    d.toLocaleTimeString(undefined, { hour: "2-digit", minute: "2-digit" });
}

interface FeedRowProps {
  feed: RssFeed;
  onEdit: (feed: RssFeed) => void;
}

function FeedRow({ feed, onEdit }: FeedRowProps) {
  const updateFeed = useUpdateFeed();
  const deleteFeed = useDeleteFeed();
  const testFeed = useTestFeed();
  const [testResult, setTestResult] = useState<TestFeedResult | null>(null);
  const [testLoading, setTestLoading] = useState(false);

  function handleToggleActive() {
    updateFeed.mutate({ id: feed.id, feed: { is_active: !feed.is_active } });
  }

  function handleTest() {
    setTestLoading(true);
    setTestResult(null);
    testFeed.mutate(feed.id, {
      onSuccess: (result) => { setTestResult(result); setTestLoading(false); },
      onError: () => {
        setTestResult({ success: false, message: "Network error.", item_count: 0 });
        setTestLoading(false);
      },
    });
  }

  function handleDeactivate() {
    if (window.confirm("Deactivate this feed? It will no longer be checked.")) {
      deleteFeed.mutate(feed.id);
    }
  }

  return (
    <>
      <tr className="border-b border-border hover:bg-muted/50">
        <td className="px-4 py-3">
          <div className="flex items-center gap-2">
            <Rss className="h-4 w-4 shrink-0 text-muted-foreground" />
            <div>
              <div className="font-medium">{feed.name}</div>
              <a
                href={feed.url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1 text-xs text-muted-foreground hover:underline"
              >
                {feed.url.length > 60 ? feed.url.slice(0, 60) + "…" : feed.url}
                <ExternalLink className="h-3 w-3" />
              </a>
            </div>
          </div>
        </td>
        <td className="px-4 py-3 text-sm">
          {feed.competitor_name ?? <span className="text-muted-foreground">—</span>}
        </td>
        <td className="px-4 py-3">
          <StatusBadge feed={feed} />
        </td>
        <td className="px-4 py-3 text-sm text-muted-foreground">
          {formatDate(feed.last_checked_at)}
        </td>
        <td className="px-4 py-3 text-center text-sm">
          {feed.error_count > 0 ? (
            <span className="font-medium text-red-600" title={feed.last_error ?? undefined}>
              {feed.error_count}
            </span>
          ) : (
            <span className="text-muted-foreground">0</span>
          )}
        </td>
        <td className="px-4 py-3">
          <div className="flex items-center justify-end gap-1">
            {/* Toggle active */}
            <button
              onClick={handleToggleActive}
              className={cn(
                "relative inline-flex h-5 w-9 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors",
                feed.is_active ? "bg-primary" : "bg-muted",
              )}
              title={feed.is_active ? "Deactivate" : "Activate"}
            >
              <span
                className={cn(
                  "pointer-events-none inline-block h-4 w-4 rounded-full bg-background shadow-sm transition-transform",
                  feed.is_active ? "translate-x-4" : "translate-x-0",
                )}
              />
            </button>

            {/* Test */}
            <button
              onClick={handleTest}
              disabled={testLoading}
              className="ml-2 inline-flex items-center gap-1 rounded-md px-2 py-1 text-xs font-medium text-muted-foreground hover:bg-accent hover:text-foreground"
              title="Test feed"
            >
              {testLoading ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <FlaskConical className="h-3.5 w-3.5" />}
            </button>

            {/* Edit */}
            <button
              onClick={() => onEdit(feed)}
              className="inline-flex items-center gap-1 rounded-md px-2 py-1 text-xs font-medium text-muted-foreground hover:bg-accent hover:text-foreground"
              title="Edit feed"
            >
              <Pencil className="h-3.5 w-3.5" />
            </button>

            {/* Deactivate (soft delete) */}
            {feed.is_active && (
              <button
                onClick={handleDeactivate}
                className="inline-flex items-center gap-1 rounded-md px-2 py-1 text-xs font-medium text-destructive hover:bg-red-50"
                title="Deactivate feed"
              >
                <XCircle className="h-3.5 w-3.5" />
              </button>
            )}
          </div>
        </td>
      </tr>
      {/* Test result row */}
      {testResult && (
        <tr>
          <td colSpan={6} className="px-4 pb-3">
            <div
              className={cn(
                "flex items-start gap-2 rounded-md px-3 py-2 text-sm",
                testResult.success ? "bg-green-50 text-green-800" : "bg-red-50 text-red-800",
              )}
            >
              {testResult.success ? (
                <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0" />
              ) : (
                <XCircle className="mt-0.5 h-4 w-4 shrink-0" />
              )}
              <span>{testResult.message}</span>
              <button
                onClick={() => setTestResult(null)}
                className="ml-auto text-xs underline opacity-60 hover:opacity-100"
              >
                dismiss
              </button>
            </div>
          </td>
        </tr>
      )}
    </>
  );
}


// ---------------------------------------------------------------------------
// Main Page
// ---------------------------------------------------------------------------

export default function Feeds() {
  const { data: feeds, isLoading, error, refetch } = useFeeds();
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingFeed, setEditingFeed] = useState<RssFeed | null>(null);

  function openAdd() {
    setEditingFeed(null);
    setDialogOpen(true);
  }

  function openEdit(feed: RssFeed) {
    setEditingFeed(feed);
    setDialogOpen(true);
  }

  function closeDialog() {
    setDialogOpen(false);
    setEditingFeed(null);
  }

  return (
    <div>
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">RSS Feeds</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Manage RSS feed sources for competitive intelligence monitoring.
          </p>
        </div>
        <button
          onClick={openAdd}
          className="inline-flex items-center gap-1.5 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
        >
          <Plus className="h-4 w-4" />
          Add Feed
        </button>
      </div>

      {/* Loading */}
      {isLoading && (
        <div className="mt-12 flex justify-center">
          <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="mt-6 rounded-md bg-red-50 px-4 py-3 text-sm text-red-700">
          <div className="flex items-center justify-between">
            <span>Failed to load feeds.</span>
            <button onClick={() => refetch()} className="inline-flex items-center gap-1.5 rounded-md border border-red-300 px-3 py-1.5 text-sm font-medium hover:bg-red-100">
              <RefreshCw className="h-3.5 w-3.5" /> Retry
            </button>
          </div>
        </div>
      )}

      {/* Empty state */}
      {feeds && feeds.length === 0 && (
        <div className="mt-12 flex flex-col items-center gap-2 text-center text-muted-foreground">
          <Rss className="h-10 w-10" />
          <p className="text-lg font-medium">No feeds yet</p>
          <p className="text-sm">Add an RSS feed to start monitoring competitive intelligence.</p>
        </div>
      )}

      {/* Table */}
      {feeds && feeds.length > 0 && (
        <div className="mt-6 overflow-hidden rounded-lg border border-border">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-border bg-muted/50">
              <tr>
                <th className="px-4 py-3 font-medium">Feed</th>
                <th className="px-4 py-3 font-medium">Competitor</th>
                <th className="px-4 py-3 font-medium">Status</th>
                <th className="px-4 py-3 font-medium">Last Checked</th>
                <th className="px-4 py-3 text-center font-medium">Errors</th>
                <th className="px-4 py-3 text-right font-medium">Actions</th>
              </tr>
            </thead>
            <tbody>
              {feeds.map((feed) => (
                <FeedRow key={feed.id} feed={feed} onEdit={openEdit} />
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Check Run History */}
      <CheckRunsHistory />

      {/* Dialog */}
      <FeedFormDialog
        key={editingFeed?.id ?? "new"}
        open={dialogOpen}
        onClose={closeDialog}
        feed={editingFeed}
      />
    </div>
  );
}

import { useState } from "react";
import { Link } from "react-router-dom";
import {
  useCompetitors,
  useCreateCompetitor,
  useDeleteCompetitor,
  useApproveCompetitor,
  useRejectCompetitor,
} from "@/hooks/use-competitors";
import {
  Loader2,
  Plus,
  Search,
  CheckCircle2,
  XCircle,
  Trash2,
  Sparkles,
  RefreshCw,
} from "lucide-react";

export default function Competitors() {
  const { data: competitors, isLoading, error, refetch } = useCompetitors();
  const createMutation = useCreateCompetitor();
  const deleteMutation = useDeleteCompetitor();
  const approveMutation = useApproveCompetitor();
  const rejectMutation = useRejectCompetitor();

  const [search, setSearch] = useState("");
  const [showCreate, setShowCreate] = useState(false);
  const [newName, setNewName] = useState("");
  const [createError, setCreateError] = useState("");

  const suggested = competitors?.filter((c) => c.is_suggested) ?? [];
  const active = competitors?.filter((c) => !c.is_suggested) ?? [];
  const filtered = active.filter(
    (c) =>
      c.name.toLowerCase().includes(search.toLowerCase()) ||
      c.description.toLowerCase().includes(search.toLowerCase())
  );

  const handleCreate = async () => {
    if (!newName.trim()) return;
    setCreateError("");
    try {
      await createMutation.mutateAsync({ name: newName.trim() });
      setNewName("");
      setShowCreate(false);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to create competitor";
      setCreateError(msg);
    }
  };

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
          <span>Failed to load competitors.</span>
          <button onClick={() => refetch()} className="inline-flex items-center gap-1.5 rounded-md border border-destructive/30 px-3 py-1.5 text-sm font-medium hover:bg-destructive/10">
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
          <h1 className="text-2xl font-bold">Competitors</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Manage tracked competitors and their profiles.
          </p>
        </div>
        <button
          onClick={() => setShowCreate(true)}
          className="inline-flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
        >
          <Plus className="h-4 w-4" />
          Add Competitor
        </button>
      </div>

      {/* Create dialog */}
      {showCreate && (
        <div className="rounded-lg border border-border bg-card p-4 shadow-sm">
          <h3 className="mb-3 text-sm font-medium">New Competitor</h3>
          <div className="flex gap-2">
            <input
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleCreate()}
              placeholder="Competitor name..."
              className="flex-1 rounded-md border border-input bg-background px-3 py-2 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
              autoFocus
            />
            <button
              onClick={handleCreate}
              disabled={createMutation.isPending || !newName.trim()}
              className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
            >
              {createMutation.isPending ? "Creating..." : "Create"}
            </button>
            <button
              onClick={() => { setShowCreate(false); setNewName(""); setCreateError(""); }}
              className="rounded-md border border-input px-4 py-2 text-sm hover:bg-muted"
            >
              Cancel
            </button>
          </div>
          {createError && (
            <p className="mt-2 text-sm text-destructive">{createError}</p>
          )}
        </div>
      )}

      {/* Suggested Competitors */}
      {suggested.length > 0 && (
        <div className="space-y-3">
          <div className="flex items-center gap-2">
            <Sparkles className="h-4 w-4 text-yellow-500" />
            <h2 className="text-lg font-semibold">Suggested Competitors</h2>
            <span className="rounded-full bg-yellow-100 px-2 py-0.5 text-xs font-medium text-yellow-800">
              {suggested.length} pending
            </span>
          </div>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {suggested.map((c) => (
              <div
                key={c.id}
                className="rounded-lg border border-yellow-200 bg-yellow-50/50 p-4"
              >
                <div className="mb-2 flex items-start justify-between">
                  <Link
                    to={`/competitors/${c.id}`}
                    className="font-medium hover:underline"
                  >
                    {c.name}
                  </Link>
                </div>
                {c.suggested_reason && (
                  <p className="mb-3 text-xs text-muted-foreground line-clamp-2">
                    {c.suggested_reason}
                  </p>
                )}
                <div className="flex gap-2">
                  <button
                    onClick={() => approveMutation.mutate(c.id)}
                    disabled={approveMutation.isPending}
                    className="inline-flex items-center gap-1 rounded-md bg-green-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-green-700 disabled:opacity-50"
                  >
                    <CheckCircle2 className="h-3 w-3" />
                    Approve
                  </button>
                  <button
                    onClick={() => rejectMutation.mutate(c.id)}
                    disabled={rejectMutation.isPending}
                    className="inline-flex items-center gap-1 rounded-md border border-input px-3 py-1.5 text-xs font-medium hover:bg-muted disabled:opacity-50"
                  >
                    <XCircle className="h-3 w-3" />
                    Reject
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}


      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search competitors..."
          className="w-full rounded-md border border-input bg-background py-2 pl-10 pr-3 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
        />
      </div>

      {/* Active Competitors Grid */}
      {filtered.length === 0 ? (
        <div className="py-12 text-center text-muted-foreground">
          {search ? "No competitors match your search." : "No competitors yet. Add one to get started."}
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {filtered.map((c) => (
            <Link
              key={c.id}
              to={`/competitors/${c.id}`}
              className="group rounded-lg border border-border bg-card p-4 transition-shadow hover:shadow-md"
            >
              <div className="mb-2 flex items-start justify-between">
                <h3 className="font-medium group-hover:underline">{c.name}</h3>
                <button
                  onClick={(e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    if (confirm(`Delete "${c.name}"?`)) {
                      deleteMutation.mutate(c.id);
                    }
                  }}
                  className="rounded p-1 text-muted-foreground opacity-0 hover:bg-muted hover:text-destructive group-hover:opacity-100"
                >
                  <Trash2 className="h-3.5 w-3.5" />
                </button>
              </div>
              {c.description && (
                <p className="mb-2 text-sm text-muted-foreground line-clamp-2">
                  {c.description}
                </p>
              )}
              {c.content_types && c.content_types.length > 0 && (
                <div className="flex flex-wrap gap-1">
                  {c.content_types.slice(0, 3).map((ct) => (
                    <span
                      key={ct}
                      className="rounded-full bg-secondary px-2 py-0.5 text-xs text-secondary-foreground"
                    >
                      {ct}
                    </span>
                  ))}
                  {c.content_types.length > 3 && (
                    <span className="text-xs text-muted-foreground">
                      +{c.content_types.length - 3} more
                    </span>
                  )}
                </div>
              )}
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
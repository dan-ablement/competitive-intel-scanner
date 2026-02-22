import { useState } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import {
  useContentOutput,
  useUpdateContentOutput,
  useChangeContentOutputStatus,
  useGenerateDraft,
  useDeleteContentOutput,
  usePublishContentOutput,
} from "@/hooks/use-content-outputs";
import { useAuth } from "@/contexts/AuthContext";
import type { ContentOutput, ContentOutputStatus } from "@/types";
import { cn } from "@/lib/utils";
import {
  ArrowLeft,
  Loader2,
  RefreshCw,
  ExternalLink,
  ChevronDown,
  Send,
  Shield,
  BookOpen,
  AlertTriangle,
  Save,
  CheckCircle2,
  CreditCard,
  Trash2,
} from "lucide-react";
import { ContentStatusBadge } from "./ContentOutputs";

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const STATUS_ORDER: ContentOutputStatus[] = ["draft", "in_review", "approved", "published"];

const STATUS_CONFIG: Record<ContentOutputStatus, { label: string; color: string; bgColor: string }> = {
  draft: { label: "Draft", color: "text-gray-700", bgColor: "bg-gray-100" },
  generating: { label: "Generating…", color: "text-yellow-700", bgColor: "bg-yellow-100" },
  in_review: { label: "In Review", color: "text-blue-700", bgColor: "bg-blue-100" },
  approved: { label: "Approved", color: "text-green-700", bgColor: "bg-green-100" },
  published: { label: "Published", color: "text-purple-700", bgColor: "bg-purple-100" },
  failed: { label: "Failed", color: "text-red-700", bgColor: "bg-red-100" },
};

// ---------------------------------------------------------------------------
// Approval Workflow (adapted for content outputs)
// ---------------------------------------------------------------------------

function ContentApprovalWorkflow({
  output,
  onStatusChange,
  isUpdating,
  onPublish,
  isPublishing,
  publishError,
}: {
  output: ContentOutput;
  onStatusChange: (status: ContentOutputStatus) => void;
  isUpdating: boolean;
  onPublish: () => void;
  isPublishing: boolean;
  publishError: string | null;
}) {
  const { user } = useAuth();
  const isAdmin = user?.role === "admin";
  const currentStatus = output.status;
  const config = STATUS_CONFIG[currentStatus];

  return (
    <div className="space-y-4">
      {/* Current status badge */}
      <div className="flex items-center gap-3">
        <span className="text-sm font-medium text-muted-foreground">Status:</span>
        <span
          className={cn(
            "inline-flex items-center rounded-full px-3 py-1 text-xs font-semibold",
            config.bgColor,
            config.color
          )}
        >
          {config.label}
        </span>
      </div>

      {/* Status progress bar */}
      {currentStatus !== "failed" && (
        <>
          <div className="flex items-center gap-1">
            {STATUS_ORDER.map((status, index) => {
              const currentIndex = STATUS_ORDER.indexOf(currentStatus);
              const isCompleted = index <= currentIndex;
              const isCurrent = status === currentStatus;

              return (
                <div key={status} className="flex flex-1 items-center">
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
                    <div
                      className={cn(
                        "mx-1 h-0.5 flex-1",
                        isCompleted && index < currentIndex ? "bg-primary/50" : "bg-muted"
                      )}
                    />
                  )}
                </div>
              );
            })}
          </div>
          <div className="flex justify-between text-xs text-muted-foreground">
            {STATUS_ORDER.map((status) => (
              <span key={status} className="w-8 text-center">
                {STATUS_CONFIG[status].label}
              </span>
            ))}
          </div>
        </>
      )}

      {/* Published info */}
      {currentStatus === "published" && output.published_at && (
        <div className="rounded-md border border-purple-200 bg-purple-50 p-3">
          <div className="flex items-center gap-2 text-sm text-purple-800">
            <BookOpen className="h-4 w-4" />
            <span>Published on {new Date(output.published_at).toLocaleDateString()}</span>
          </div>
        </div>
      )}

      {/* Approved info */}
      {currentStatus === "approved" && output.approved_at && (
        <div className="rounded-md border border-green-200 bg-green-50 p-3">
          <div className="flex items-center gap-2 text-sm text-green-800">
            <CheckCircle2 className="h-4 w-4" />
            <span>
              Approved on {new Date(output.approved_at).toLocaleDateString()}
              {output.approved_by && ` by ${output.approved_by_name || output.approved_by}`}
            </span>
          </div>
        </div>
      )}

      {/* Action buttons */}
      <div className="flex flex-wrap gap-2">
        {currentStatus === "draft" && (
          <button
            onClick={() => onStatusChange("in_review")}
            disabled={isUpdating}
            className="inline-flex items-center gap-2 rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-blue-700 disabled:opacity-50"
          >
            <Send className="h-4 w-4" />
            Submit for Review
          </button>
        )}

        {currentStatus === "in_review" && isAdmin && (
          <button
            onClick={() => onStatusChange("approved")}
            disabled={isUpdating}
            className="inline-flex items-center gap-2 rounded-md bg-green-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-green-700 disabled:opacity-50"
          >
            <Shield className="h-4 w-4" />
            Approve
          </button>
        )}

        {currentStatus === "in_review" && !isAdmin && (
          <p className="text-xs italic text-muted-foreground">Only admins can approve content.</p>
        )}

        {currentStatus === "approved" && isAdmin && (
          <button
            onClick={onPublish}
            disabled={isPublishing}
            className="inline-flex items-center gap-2 rounded-md bg-purple-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-purple-700 disabled:opacity-50"
          >
            {isPublishing ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <BookOpen className="h-4 w-4" />
            )}
            {isPublishing ? "Publishing…" : "Publish to Google Docs"}
          </button>
        )}

        {publishError && (
          <div className="rounded-md border border-red-200 bg-red-50 p-3">
            <div className="flex items-center gap-2 text-sm text-red-800">
              <AlertTriangle className="h-4 w-4" />
              <span>{publishError}</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Collapsible Section
// ---------------------------------------------------------------------------

function CollapsibleSection({
  title,
  content,
  isEditable,
  onContentChange,
}: {
  title: string;
  content: string;
  isEditable: boolean;
  onContentChange?: (content: string) => void;
}) {
  const [isOpen, setIsOpen] = useState(true);

  return (
    <div className="rounded-lg border border-border">
      <button
        onClick={() => setIsOpen((prev) => !prev)}
        className="flex w-full items-center justify-between px-4 py-3 text-sm font-medium hover:bg-muted/50"
      >
        {title}
        <ChevronDown
          className={cn(
            "h-4 w-4 text-muted-foreground transition-transform",
            isOpen && "rotate-180"
          )}
        />
      </button>
      {isOpen && (
        <div className="border-t border-border px-4 py-3">
          {isEditable ? (
            <textarea
              value={content}
              onChange={(e) => onContentChange?.(e.target.value)}
              rows={6}
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
            />
          ) : (
            <div className="prose prose-sm max-w-none whitespace-pre-wrap text-sm">
              {content || <span className="italic text-muted-foreground">No content</span>}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main Component
// ---------------------------------------------------------------------------

export default function ContentOutputDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { data: output, isLoading, error, refetch } = useContentOutput(id!);
  const updateMutation = useUpdateContentOutput();
  const statusMutation = useChangeContentOutputStatus();
  const retryMutation = useGenerateDraft();
  const deleteMutation = useDeleteContentOutput();
  const publishMutation = usePublishContentOutput();

  const [saved, setSaved] = useState(false);
  const [editedContent, setEditedContent] = useState<string | null>(null);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [publishError, setPublishError] = useState<string | null>(null);

  const isEditable = output?.status === "draft" || output?.status === "in_review";
  const currentContent = editedContent ?? output?.content ?? "";

  const handleStatusChange = async (status: ContentOutputStatus) => {
    if (!id) return;
    await statusMutation.mutateAsync({ id, status });
  };

  const handleSave = async () => {
    if (!id || editedContent === null) return;
    setSaved(false);
    await updateMutation.mutateAsync({ id, output: { content: editedContent } });
    setSaved(true);
    setEditedContent(null);
    setTimeout(() => setSaved(false), 3000);
  };

  const handleRetry = async () => {
    if (!output?.competitor_id || !output?.template_id) return;
    await retryMutation.mutateAsync({
      competitorId: output.competitor_id,
      templateId: output.template_id,
    });
    navigate("/content");
  };

  const handleDelete = async () => {
    if (!id) return;
    await deleteMutation.mutateAsync(id);
    navigate("/content");
  };

  const handlePublish = async () => {
    if (!id) return;
    setPublishError(null);
    try {
      await publishMutation.mutateAsync(id);
    } catch (err: unknown) {
      const message =
        err && typeof err === "object" && "response" in err
          ? ((err as { response?: { data?: { detail?: string } } }).response?.data?.detail ?? "Publish failed")
          : "Publish failed";
      setPublishError(message);
    }
  };

  // Parse content into sections (try JSON first, fallback to plain text)
  function parseSections(content: string): { title: string; content: string }[] {
    try {
      const parsed = JSON.parse(content);
      if (Array.isArray(parsed)) {
        return parsed.map((s: { title?: string; heading?: string; content?: string; body?: string }) => ({
          title: s.title || s.heading || "Section",
          content: s.content || s.body || "",
        }));
      }
      if (typeof parsed === "object" && parsed !== null) {
        return Object.entries(parsed).map(([key, value]) => ({
          title: key,
          content: typeof value === "string" ? value : JSON.stringify(value, null, 2),
        }));
      }
    } catch {
      // Not JSON, treat as plain text
    }
    return [{ title: "Content", content }];
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (error || !output) {
    return (
      <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-4 text-destructive">
        <div className="flex items-center justify-between">
          <span>Content output not found.</span>
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

  const sections = parseSections(currentContent);

  return (
    <div className="mx-auto max-w-5xl">
      {/* Header */}
      <div className="mb-6 flex items-center gap-3">
        <button onClick={() => navigate("/content")} className="rounded-md p-1.5 hover:bg-muted">
          <ArrowLeft className="h-5 w-5" />
        </button>
        <div className="flex-1">
          <h1 className="text-2xl font-bold">{output.title}</h1>
          <div className="mt-1 flex items-center gap-2">
            <ContentStatusBadge status={output.status} />
            {output.competitor_name && (
              <span className="rounded bg-violet-100 px-1.5 py-0.5 text-xs text-violet-700">
                {output.competitor_name}
              </span>
            )}
            <span className="rounded bg-secondary px-1.5 py-0.5 text-xs text-secondary-foreground">
              {output.content_type}
            </span>
          </div>
        </div>
        <button
          onClick={() => setShowDeleteConfirm(true)}
          className="inline-flex items-center gap-2 rounded-md border border-red-200 px-3 py-2 text-sm font-medium text-red-600 transition-colors hover:bg-red-50"
        >
          <Trash2 className="h-4 w-4" />
          Delete
        </button>
      </div>

      {/* Delete confirmation dialog */}
      {showDeleteConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="w-full max-w-sm rounded-lg border border-border bg-background p-6 shadow-lg">
            <h2 className="text-lg font-semibold">Delete Content Output</h2>
            <p className="mt-2 text-sm text-muted-foreground">
              Are you sure you want to delete this content output? This action cannot be undone.
            </p>
            <div className="mt-4 flex justify-end gap-2">
              <button
                onClick={() => setShowDeleteConfirm(false)}
                className="rounded-md border border-input px-4 py-2 text-sm font-medium hover:bg-muted"
              >
                Cancel
              </button>
              <button
                onClick={handleDelete}
                disabled={deleteMutation.isPending}
                className="inline-flex items-center gap-2 rounded-md bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700 disabled:opacity-50"
              >
                {deleteMutation.isPending && <Loader2 className="h-4 w-4 animate-spin" />}
                Delete
              </button>
            </div>
          </div>
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-[1fr_280px]">
        {/* Main content */}
        <div className="space-y-4">
          {/* Error display */}
          {output.status === "failed" && (
            <div className="rounded-lg border border-red-200 bg-red-50 p-4">
              <div className="flex items-start gap-3">
                <AlertTriangle className="mt-0.5 h-5 w-5 text-red-600" />
                <div className="flex-1">
                  <h3 className="font-medium text-red-800">Generation Failed</h3>
                  <p className="mt-1 text-sm text-red-700">
                    {output.error_message || "An unknown error occurred during content generation."}
                  </p>
                  {output.competitor_id && output.template_id && (
                    <button
                      onClick={handleRetry}
                      disabled={retryMutation.isPending}
                      className="mt-3 inline-flex items-center gap-2 rounded-md bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700 disabled:opacity-50"
                    >
                      {retryMutation.isPending ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : (
                        <RefreshCw className="h-4 w-4" />
                      )}
                      Retry Generation
                    </button>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Google Doc link (prominent when published) */}
          {output.google_doc_url && (
            <a
              href={output.google_doc_url}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-3 rounded-lg border border-blue-200 bg-blue-50 p-4 text-blue-700 transition-colors hover:bg-blue-100"
            >
              <ExternalLink className="h-5 w-5" />
              <div>
                <div className="font-medium">View in Google Docs</div>
                <div className="text-xs text-blue-600">Opens in a new tab</div>
              </div>
            </a>
          )}

          {/* Content sections */}
          {sections.map((section, index) => (
            <CollapsibleSection
              key={index}
              title={section.title}
              content={section.content}
              isEditable={!!isEditable}
              onContentChange={
                isEditable
                  ? (newContent) => {
                      // For single-section plain text, update directly
                      if (sections.length === 1) {
                        setEditedContent(newContent);
                      } else {
                        // For multi-section, reconstruct
                        const updated = [...sections];
                        updated[index] = { ...updated[index], content: newContent };
                        try {
                          JSON.parse(currentContent);
                          setEditedContent(JSON.stringify(updated));
                        } catch {
                          setEditedContent(newContent);
                        }
                      }
                    }
                  : undefined
              }
            />
          ))}

          {/* Save button */}
          {isEditable && editedContent !== null && (
            <div className="flex items-center justify-end border-t border-border pt-4">
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
          )}

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
            <label className="mb-3 block text-sm font-medium">Workflow</label>
            <ContentApprovalWorkflow
              output={output}
              onStatusChange={handleStatusChange}
              isUpdating={statusMutation.isPending}
              onPublish={handlePublish}
              isPublishing={publishMutation.isPending}
              publishError={publishError}
            />
          </div>

          {/* Source Cards */}
          {output.source_card_ids.length > 0 && (
            <div className="rounded-lg border border-border bg-card p-4">
              <label className="mb-2 block text-sm font-medium">Source Cards</label>
              <div className="space-y-1.5">
                {output.source_card_ids.map((cardId) => (
                  <Link
                    key={cardId}
                    to={`/cards/${cardId}`}
                    className="flex items-center gap-2 rounded-md px-2 py-1.5 text-xs text-blue-600 hover:bg-muted"
                  >
                    <CreditCard className="h-3 w-3" />
                    Card {cardId.slice(0, 8)}…
                  </Link>
                ))}
              </div>
            </div>
          )}

          {/* Metadata */}
          <div className="rounded-lg border border-border bg-card p-4">
            <label className="mb-2 block text-sm font-medium">Details</label>
            <dl className="space-y-1.5 text-xs">
              <div className="flex justify-between">
                <dt className="text-muted-foreground">Version</dt>
                <dd>{output.version}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-muted-foreground">Created</dt>
                <dd>{new Date(output.created_at).toLocaleDateString()}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-muted-foreground">Updated</dt>
                <dd>{new Date(output.updated_at).toLocaleDateString()}</dd>
              </div>
              {output.approved_at && (
                <div className="flex justify-between">
                  <dt className="text-muted-foreground">Approved</dt>
                  <dd>{new Date(output.approved_at).toLocaleDateString()}</dd>
                </div>
              )}
              {output.approved_by && (
                <div className="flex justify-between">
                  <dt className="text-muted-foreground">Approved by</dt>
                  <dd>{output.approved_by_name || output.approved_by}</dd>
                </div>
              )}
              {output.published_at && (
                <div className="flex justify-between">
                  <dt className="text-muted-foreground">Published</dt>
                  <dd>{new Date(output.published_at).toLocaleDateString()}</dd>
                </div>
              )}
            </dl>
          </div>
        </div>
      </div>
    </div>
  );
}

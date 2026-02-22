import { useState, useEffect } from "react";
import { useSettings, useKVSetting, useSetKVSetting } from "@/hooks/use-system";
import { useSuggestions, useApproveSuggestion, useRejectSuggestion } from "@/hooks/use-suggestions";
import { useTriggerProfileReview } from "@/hooks/use-system";
import {
  useContentTemplates,
  useCreateContentTemplate,
  useUpdateContentTemplate,
  useDeleteContentTemplate,
} from "@/hooks/use-content-templates";
import type { ProfileUpdateSuggestion, ContentTemplate, ContentTemplateSection } from "@/types";
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
  FileText,
  Plus,
  Trash2,
  ChevronDown,
  ChevronRight,
  Save,
  FolderOpen,
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
  const { data: suggestions, isLoading, error, refetch } = useSuggestions();
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
          <div className="flex items-center justify-between">
            <span>Failed to load suggestions.</span>
            <button onClick={() => refetch()} className="inline-flex items-center gap-1.5 rounded-md border border-red-300 px-3 py-1.5 text-sm font-medium hover:bg-red-100">
              <RefreshCw className="h-3.5 w-3.5" /> Retry
            </button>
          </div>
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
// Google Drive Folder ID Section
// ---------------------------------------------------------------------------

function GoogleDriveFolderSection() {
  const { data: kvSetting, isLoading } = useKVSetting("GOOGLE_DRIVE_FOLDER_ID");
  const setKV = useSetKVSetting();
  const [folderId, setFolderId] = useState("");
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    if (kvSetting?.value) {
      setFolderId(kvSetting.value);
    }
  }, [kvSetting]);

  const handleSave = () => {
    setKV.mutate(
      { key: "GOOGLE_DRIVE_FOLDER_ID", value: folderId || null },
      {
        onSuccess: () => {
          setSaved(true);
          setTimeout(() => setSaved(false), 2000);
        },
      }
    );
  };

  return (
    <section className="rounded-lg border border-border p-6">
      <div className="flex items-center gap-2 mb-4">
        <FolderOpen className="h-5 w-5 text-muted-foreground" />
        <h2 className="text-lg font-semibold">Google Drive</h2>
      </div>
      <p className="text-sm text-muted-foreground mb-4">
        Folder ID for storing generated content documents in Google Drive.
      </p>
      <div className="flex items-center gap-3">
        <input
          type="text"
          value={folderId}
          onChange={(e) => setFolderId(e.target.value)}
          placeholder={isLoading ? "Loading..." : "Enter Google Drive folder ID"}
          disabled={isLoading}
          className="flex-1 rounded-md border border-input bg-background px-3 py-2 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring disabled:opacity-50"
        />
        <button
          onClick={handleSave}
          disabled={setKV.isPending || isLoading}
          className="inline-flex items-center gap-1.5 rounded-md bg-primary px-3 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
        >
          {setKV.isPending ? (
            <Loader2 className="h-3.5 w-3.5 animate-spin" />
          ) : saved ? (
            <CheckCircle2 className="h-3.5 w-3.5" />
          ) : (
            <Save className="h-3.5 w-3.5" />
          )}
          {saved ? "Saved" : "Save"}
        </button>
      </div>
    </section>
  );
}

// ---------------------------------------------------------------------------
// Content Templates Section
// ---------------------------------------------------------------------------

function TemplateEditor({
  template,
  onSave,
  onCancel,
  isSaving,
}: {
  template: Omit<ContentTemplate, "id" | "created_at" | "updated_at"> & { id?: string };
  onSave: (t: Omit<ContentTemplate, "id" | "created_at" | "updated_at">) => void;
  onCancel: () => void;
  isSaving: boolean;
}) {
  const [name, setName] = useState(template.name);
  const [contentType, setContentType] = useState(template.content_type);
  const [description, setDescription] = useState(template.description);
  const [docNamePattern, setDocNamePattern] = useState(template.doc_name_pattern);
  const [sections, setSections] = useState<ContentTemplateSection[]>(
    template.sections ?? []
  );
  const isActive = template.is_active;

  const addSection = () => {
    setSections([...sections, { title: "", description: "", prompt_hint: "" }]);
  };

  const removeSection = (index: number) => {
    setSections(sections.filter((_, i) => i !== index));
  };

  const updateSection = (
    index: number,
    field: keyof ContentTemplateSection,
    value: string
  ) => {
    setSections(
      sections.map((s, i) => (i === index ? { ...s, [field]: value } : s))
    );
  };

  const handleSave = () => {
    onSave({
      name,
      content_type: contentType,
      description,
      doc_name_pattern: docNamePattern,
      sections,
      is_active: isActive,
    });
  };

  return (
    <div className="mt-3 space-y-4 rounded-md border border-border bg-muted/30 p-4">
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <div>
          <label className="text-xs font-medium text-muted-foreground">
            Template Name
          </label>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="mt-1 w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
          />
        </div>
        <div>
          <label className="text-xs font-medium text-muted-foreground">
            Content Type
          </label>
          <input
            type="text"
            value={contentType}
            onChange={(e) => setContentType(e.target.value)}
            className="mt-1 w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
          />
        </div>
      </div>

      <div>
        <label className="text-xs font-medium text-muted-foreground">
          Description
        </label>
        <textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          rows={2}
          className="mt-1 w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
        />
      </div>

      <div>
        <label className="text-xs font-medium text-muted-foreground">
          Doc Name Pattern
        </label>
        <input
          type="text"
          value={docNamePattern}
          onChange={(e) => setDocNamePattern(e.target.value)}
          placeholder="{competitor} - Battle Card"
          className="mt-1 w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
        />
        <p className="mt-1 text-xs text-muted-foreground">
          Use <code className="rounded bg-muted px-1">{"{competitor}"}</code> as
          a placeholder for the competitor name.
        </p>
      </div>

      {/* Sections */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <label className="text-xs font-medium text-muted-foreground">
            Sections ({sections.length})
          </label>
          <button
            onClick={addSection}
            className="inline-flex items-center gap-1 rounded-md border border-input px-2 py-1 text-xs font-medium hover:bg-accent"
          >
            <Plus className="h-3 w-3" /> Add Section
          </button>
        </div>
        <div className="space-y-3">
          {sections.map((section, i) => (
            <div
              key={i}
              className="rounded-md border border-border bg-background p-3"
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-semibold text-muted-foreground">
                  Section {i + 1}
                </span>
                <button
                  onClick={() => removeSection(i)}
                  className="inline-flex items-center gap-1 rounded-md px-2 py-1 text-xs text-red-600 hover:bg-red-50"
                >
                  <Trash2 className="h-3 w-3" /> Remove
                </button>
              </div>
              <div className="space-y-2">
                <input
                  type="text"
                  value={section.title}
                  onChange={(e) => updateSection(i, "title", e.target.value)}
                  placeholder="Section title"
                  className="w-full rounded-md border border-input bg-background px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                />
                <textarea
                  value={section.description}
                  onChange={(e) =>
                    updateSection(i, "description", e.target.value)
                  }
                  placeholder="Section description"
                  rows={2}
                  className="w-full rounded-md border border-input bg-background px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                />
                <textarea
                  value={section.prompt_hint}
                  onChange={(e) =>
                    updateSection(i, "prompt_hint", e.target.value)
                  }
                  placeholder="Prompt hint for AI generation"
                  rows={2}
                  className="w-full rounded-md border border-input bg-background px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                />
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Actions */}
      <div className="flex items-center justify-end gap-2 pt-2">
        <button
          onClick={onCancel}
          className="rounded-md border border-input px-3 py-1.5 text-sm font-medium hover:bg-accent"
        >
          Cancel
        </button>
        <button
          onClick={handleSave}
          disabled={isSaving || !name.trim() || !contentType.trim()}
          className="inline-flex items-center gap-1.5 rounded-md bg-primary px-3 py-1.5 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
        >
          {isSaving ? (
            <Loader2 className="h-3.5 w-3.5 animate-spin" />
          ) : (
            <Save className="h-3.5 w-3.5" />
          )}
          Save
        </button>
      </div>
    </div>
  );
}

function ContentTemplatesSection() {
  const { data: templates, isLoading } = useContentTemplates();
  const createTemplate = useCreateContentTemplate();
  const updateTemplate = useUpdateContentTemplate();
  const deleteTemplate = useDeleteContentTemplate();
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [isCreating, setIsCreating] = useState(false);

  const handleToggleActive = (template: ContentTemplate) => {
    updateTemplate.mutate({
      id: template.id,
      template: { is_active: !template.is_active },
    });
  };

  return (
    <section className="rounded-lg border border-border p-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <FileText className="h-5 w-5 text-muted-foreground" />
          <h2 className="text-lg font-semibold">Content Templates</h2>
        </div>
        <button
          onClick={() => {
            setIsCreating(true);
            setExpandedId(null);
          }}
          className="inline-flex items-center gap-1.5 rounded-md border border-input px-3 py-1.5 text-sm font-medium hover:bg-accent"
        >
          <Plus className="h-3.5 w-3.5" /> Add Template
        </button>
      </div>

      {isLoading && (
        <div className="flex justify-center py-8">
          <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
        </div>
      )}

      {isCreating && (
        <TemplateEditor
          template={{
            name: "",
            content_type: "",
            description: "",
            doc_name_pattern: "",
            sections: [],
            is_active: true,
          }}
          onSave={(t) => {
            createTemplate.mutate(t, {
              onSuccess: () => setIsCreating(false),
            });
          }}
          onCancel={() => setIsCreating(false)}
          isSaving={createTemplate.isPending}
        />
      )}

      {templates && templates.length === 0 && !isCreating && (
        <p className="text-sm text-muted-foreground">
          No content templates yet. Add one to get started.
        </p>
      )}

      {templates && templates.length > 0 && (
        <div className="space-y-2">
          {templates.map((template) => (
            <div key={template.id}>
              <div
                className="flex items-center justify-between rounded-md border border-border px-4 py-3 cursor-pointer hover:bg-muted/30"
                onClick={() =>
                  setExpandedId(
                    expandedId === template.id ? null : template.id
                  )
                }
              >
                <div className="flex items-center gap-3">
                  {expandedId === template.id ? (
                    <ChevronDown className="h-4 w-4 text-muted-foreground" />
                  ) : (
                    <ChevronRight className="h-4 w-4 text-muted-foreground" />
                  )}
                  <div>
                    <span className="text-sm font-semibold">
                      {template.name}
                    </span>
                    <div className="flex items-center gap-2 mt-0.5">
                      <span className="rounded-full bg-muted px-2 py-0.5 text-xs font-medium text-muted-foreground">
                        {template.content_type.replace(/_/g, " ")}
                      </span>
                      <span className="text-xs text-muted-foreground">
                        {template.sections?.length ?? 0} section
                        {(template.sections?.length ?? 0) !== 1 ? "s" : ""}
                      </span>
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleToggleActive(template);
                    }}
                    className={cn(
                      "relative inline-flex h-5 w-9 items-center rounded-full transition-colors",
                      template.is_active ? "bg-green-500" : "bg-gray-300"
                    )}
                  >
                    <span
                      className={cn(
                        "inline-block h-3.5 w-3.5 rounded-full bg-white transition-transform",
                        template.is_active
                          ? "translate-x-4.5"
                          : "translate-x-0.5"
                      )}
                    />
                  </button>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      if (
                        confirm(
                          `Delete template "${template.name}"?`
                        )
                      ) {
                        deleteTemplate.mutate(template.id);
                      }
                    }}
                    className="rounded-md p-1 text-muted-foreground hover:bg-red-50 hover:text-red-600"
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </button>
                </div>
              </div>
              {expandedId === template.id && (
                <TemplateEditor
                  template={template}
                  onSave={(t) => {
                    updateTemplate.mutate(
                      { id: template.id, template: t },
                      { onSuccess: () => setExpandedId(null) }
                    );
                  }}
                  onCancel={() => setExpandedId(null)}
                  isSaving={updateTemplate.isPending}
                />
              )}
            </div>
          ))}
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
          <ContentTemplatesSection />
          <GoogleDriveFolderSection />
          <AdminsSection admins={(settings as Record<string, unknown>).admins as string[] ?? []} />
        </div>
      )}
    </div>
  );
}

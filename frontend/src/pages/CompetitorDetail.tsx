import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  useCompetitor,
  useUpdateCompetitor,
  useDeleteCompetitor,
  useApproveCompetitor,
  useRejectCompetitor,
} from "@/hooks/use-competitors";
import {
  ArrowLeft,
  Save,
  Loader2,
  CheckCircle2,
  XCircle,
  Trash2,
  Sparkles,
  RefreshCw,
} from "lucide-react";

const CONTENT_TYPE_OPTIONS = [
  "Blog Post",
  "Case Study",
  "Competitive Battle Card",
  "Email Sequence",
  "FAQ / Objection Handling",
  "Feature Comparison",
  "Landing Page Copy",
  "One-Pager",
  "Sales Deck",
  "Social Media Post",
  "Webinar Talking Points",
  "White Paper",
];

const TEXT_FIELDS = [
  { key: "description", label: "Description", placeholder: "Company overview and market position..." },
  { key: "key_products", label: "Key Products", placeholder: "Main products and services..." },
  { key: "target_customers", label: "Target Customers", placeholder: "Who they sell to..." },
  { key: "known_strengths", label: "Known Strengths", placeholder: "What they do well..." },
  { key: "known_weaknesses", label: "Known Weaknesses", placeholder: "Where they fall short..." },
  { key: "augment_overlap", label: "Augment Overlap", placeholder: "Where they compete with Augment..." },
] as const;

type FormData = {
  name: string;
  description: string;
  key_products: string;
  target_customers: string;
  known_strengths: string;
  known_weaknesses: string;
  augment_overlap: string;
  pricing: string;
  content_types: string[];
};

export default function CompetitorDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { data: competitor, isLoading, error, refetch } = useCompetitor(id!);
  const updateMutation = useUpdateCompetitor();
  const deleteMutation = useDeleteCompetitor();
  const approveMutation = useApproveCompetitor();
  const rejectMutation = useRejectCompetitor();

  const [activeTab, setActiveTab] = useState<"profile" | "analysis">("profile");
  const [saved, setSaved] = useState(false);
  const [form, setForm] = useState<FormData>({
    name: "",
    description: "",
    key_products: "",
    target_customers: "",
    known_strengths: "",
    known_weaknesses: "",
    augment_overlap: "",
    pricing: "",
    content_types: [],
  });

  useEffect(() => {
    if (competitor) {
      setForm({
        name: competitor.name ?? "",
        description: competitor.description ?? "",
        key_products: competitor.key_products ?? "",
        target_customers: competitor.target_customers ?? "",
        known_strengths: competitor.known_strengths ?? "",
        known_weaknesses: competitor.known_weaknesses ?? "",
        augment_overlap: competitor.augment_overlap ?? "",
        pricing: competitor.pricing ?? "",
        content_types: competitor.content_types ?? [],
      });
    }
  }, [competitor]);

  const handleSave = async () => {
    if (!id) return;
    setSaved(false);
    await updateMutation.mutateAsync({ id, competitor: form });
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  };

  const handleDelete = async () => {
    if (!id || !confirm(`Delete "${competitor?.name}"?`)) return;
    await deleteMutation.mutateAsync(id);
    navigate("/competitors");
  };

  const handleApprove = async () => {
    if (!id) return;
    await approveMutation.mutateAsync(id);
  };

  const handleReject = async () => {
    if (!id) return;
    await rejectMutation.mutateAsync(id);
    navigate("/competitors");
  };

  const toggleContentType = (ct: string) => {
    setForm((prev) => ({
      ...prev,
      content_types: prev.content_types.includes(ct)
        ? prev.content_types.filter((t) => t !== ct)
        : [...prev.content_types, ct],
    }));
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (error || !competitor) {
    return (
      <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-4 text-destructive">
        <div className="flex items-center justify-between">
          <span>Competitor not found.</span>
          <button onClick={() => refetch()} className="inline-flex items-center gap-1.5 rounded-md border border-destructive/30 px-3 py-1.5 text-sm font-medium hover:bg-destructive/10">
            <RefreshCw className="h-3.5 w-3.5" /> Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <button
          onClick={() => navigate("/competitors")}
          className="rounded-md p-1.5 hover:bg-muted"
        >
          <ArrowLeft className="h-5 w-5" />
        </button>
        <div className="flex-1">
          <input
            value={form.name}
            onChange={(e) => setForm((prev) => ({ ...prev, name: e.target.value }))}
            className="w-full border-none bg-transparent text-2xl font-bold focus:outline-none"
          />
        </div>
      </div>


      {/* Suggested competitor banner */}
      {competitor.is_suggested && (
        <div className="flex items-center justify-between rounded-lg border border-yellow-200 bg-yellow-50/50 p-4">
          <div className="flex items-center gap-2">
            <Sparkles className="h-4 w-4 text-yellow-500" />
            <span className="text-sm font-medium">LLM-Suggested Competitor</span>
            {competitor.suggested_reason && (
              <span className="text-sm text-muted-foreground">
                — {competitor.suggested_reason}
              </span>
            )}
          </div>
          <div className="flex gap-2">
            <button
              onClick={handleApprove}
              disabled={approveMutation.isPending}
              className="inline-flex items-center gap-1 rounded-md bg-green-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-green-700 disabled:opacity-50"
            >
              <CheckCircle2 className="h-3 w-3" />
              Approve
            </button>
            <button
              onClick={handleReject}
              disabled={rejectMutation.isPending}
              className="inline-flex items-center gap-1 rounded-md border border-input px-3 py-1.5 text-xs font-medium hover:bg-muted disabled:opacity-50"
            >
              <XCircle className="h-3 w-3" />
              Reject
            </button>
          </div>
        </div>
      )}

      {/* Action bar */}
      <div className="flex items-center justify-between">
        <p className="text-xs text-muted-foreground">
          Last updated: {new Date(competitor.updated_at).toLocaleString()}
        </p>
        <div className="flex gap-2">
          <button
            onClick={handleDelete}
            disabled={deleteMutation.isPending}
            className="inline-flex items-center gap-1 rounded-md border border-input px-3 py-2 text-sm hover:bg-destructive/10 hover:text-destructive disabled:opacity-50"
          >
            <Trash2 className="h-4 w-4" />
            Delete
          </button>
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
            {updateMutation.isPending ? "Saving..." : saved ? "Saved" : "Save"}
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 border-b border-border">
        <button
          onClick={() => setActiveTab("profile")}
          className={`px-4 py-2 text-sm font-medium transition-colors ${
            activeTab === "profile"
              ? "border-b-2 border-primary text-primary"
              : "text-muted-foreground hover:text-foreground"
          }`}
        >
          Profile
        </button>
        <button
          onClick={() => setActiveTab("analysis")}
          className={`px-4 py-2 text-sm font-medium transition-colors ${
            activeTab === "analysis"
              ? "border-b-2 border-primary text-primary"
              : "text-muted-foreground hover:text-foreground"
          }`}
        >
          Related Analysis Cards
        </button>
      </div>

      {activeTab === "profile" ? (
        <div className="space-y-6">
          {/* Text fields */}
          {TEXT_FIELDS.map(({ key, label, placeholder }) => (
            <div key={key} className="space-y-2">
              <label className="text-sm font-medium">{label}</label>
              <textarea
                value={form[key]}
                onChange={(e) =>
                  setForm((prev) => ({ ...prev, [key]: e.target.value }))
                }
                placeholder={placeholder}
                rows={4}
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
              />
            </div>
          ))}

          {/* Pricing (rich text area) */}
          <div className="space-y-2">
            <label className="text-sm font-medium">Pricing</label>
            <p className="text-xs text-muted-foreground">
              Freeform pricing information.
            </p>
            <textarea
              value={form.pricing}
              onChange={(e) =>
                setForm((prev) => ({ ...prev, pricing: e.target.value }))
              }
              placeholder="Pricing tiers, models, and notes..."
              rows={6}
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
            />
          </div>

          {/* Content Types checkboxes */}
          <div className="space-y-3">
            <label className="text-sm font-medium">Content Types</label>
            <p className="text-xs text-muted-foreground">
              Select the types of content to generate for this competitor.
            </p>
            <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
              {CONTENT_TYPE_OPTIONS.map((ct) => (
                <label
                  key={ct}
                  className="flex cursor-pointer items-center gap-2 rounded-md border border-input p-2 text-sm hover:bg-muted"
                >
                  <input
                    type="checkbox"
                    checked={form.content_types.includes(ct)}
                    onChange={() => toggleContentType(ct)}
                    className="h-4 w-4 rounded border-input"
                  />
                  {ct}
                </label>
              ))}
            </div>
          </div>
        </div>
      ) : (
        <div className="py-12 text-center text-muted-foreground">
          <p>Related analysis cards will appear here.</p>
          <p className="mt-1 text-xs">This feature is coming soon.</p>
        </div>
      )}

      {updateMutation.isError && (
        <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-3 text-sm text-destructive">
          Failed to save changes. Please try again.
        </div>
      )}
    </div>
  );
}
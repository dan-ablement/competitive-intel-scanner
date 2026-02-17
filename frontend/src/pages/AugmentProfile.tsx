import { useState, useEffect } from "react";
import { useAugmentProfile, useUpdateAugmentProfile } from "@/hooks/use-augment-profile";
import { Save, Loader2, CheckCircle2, RefreshCw } from "lucide-react";

const FIELDS = [
  { key: "company_description", label: "Company Description", placeholder: "Describe Augment Code's mission, products, and market position..." },
  { key: "key_differentiators", label: "Key Differentiators", placeholder: "What sets Augment apart from competitors..." },
  { key: "target_customer_segments", label: "Target Customer Segments", placeholder: "Who are Augment's ideal customers..." },
  { key: "product_capabilities", label: "Product Capabilities", placeholder: "Core product features and capabilities..." },
  { key: "strategic_priorities", label: "Strategic Priorities", placeholder: "Current strategic focus areas..." },
] as const;

type FieldKey = (typeof FIELDS)[number]["key"] | "pricing";

export default function AugmentProfile() {
  const { data: profile, isLoading, error, refetch } = useAugmentProfile();
  const updateMutation = useUpdateAugmentProfile();
  const [form, setForm] = useState<Record<FieldKey, string>>({
    company_description: "",
    key_differentiators: "",
    target_customer_segments: "",
    product_capabilities: "",
    strategic_priorities: "",
    pricing: "",
  });
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    if (profile) {
      setForm({
        company_description: profile.company_description ?? "",
        key_differentiators: profile.key_differentiators ?? "",
        target_customer_segments: profile.target_customer_segments ?? "",
        product_capabilities: profile.product_capabilities ?? "",
        strategic_priorities: profile.strategic_priorities ?? "",
        pricing: profile.pricing ?? "",
      });
    }
  }, [profile]);

  const handleSave = async () => {
    setSaved(false);
    await updateMutation.mutateAsync(form);
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
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
          <span>Failed to load profile.</span>
          <button onClick={() => refetch()} className="inline-flex items-center gap-1.5 rounded-md border border-destructive/30 px-3 py-1.5 text-sm font-medium hover:bg-destructive/10">
            <RefreshCw className="h-3.5 w-3.5" /> Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Augment Profile</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Manage Augment Code&apos;s company profile for competitive analysis context.
          </p>
        </div>
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

      {profile?.updated_at && (
        <p className="text-xs text-muted-foreground">
          Last updated: {new Date(profile.updated_at).toLocaleString()}
        </p>
      )}

      <div className="space-y-6">
        {FIELDS.map(({ key, label, placeholder }) => (
          <div key={key} className="space-y-2">
            <label className="text-sm font-medium">{label}</label>
            <textarea
              value={form[key]}
              onChange={(e) => setForm((prev) => ({ ...prev, [key]: e.target.value }))}
              placeholder={placeholder}
              rows={4}
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
            />
          </div>
        ))}

        {/* Pricing — rich text area (freeform) */}
        <div className="space-y-2">
          <label className="text-sm font-medium">Pricing</label>
          <p className="text-xs text-muted-foreground">
            Freeform pricing information — use any format that makes sense.
          </p>
          <textarea
            value={form.pricing}
            onChange={(e) => setForm((prev) => ({ ...prev, pricing: e.target.value }))}
            placeholder="Pricing tiers, models, and competitive pricing notes..."
            rows={6}
            className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
          />
        </div>
      </div>

      {updateMutation.isError && (
        <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-3 text-sm text-destructive">
          Failed to save changes. Please try again.
        </div>
      )}
    </div>
  );
}

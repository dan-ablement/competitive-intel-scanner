import { Shield, Send, CheckCircle2, Archive } from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";
import type { AnalysisCard, CardStatus } from "@/types";
import { cn } from "@/lib/utils";

interface ApprovalWorkflowProps {
  card: AnalysisCard;
  onStatusChange: (status: CardStatus) => void;
  isUpdating?: boolean;
}

const STATUS_CONFIG: Record<CardStatus, { label: string; color: string; bgColor: string }> = {
  draft: { label: "Draft", color: "text-gray-700", bgColor: "bg-gray-100" },
  in_review: { label: "In Review", color: "text-blue-700", bgColor: "bg-blue-100" },
  approved: { label: "Approved", color: "text-green-700", bgColor: "bg-green-100" },
  archived: { label: "Archived", color: "text-amber-700", bgColor: "bg-amber-100" },
};

const STATUS_ORDER: CardStatus[] = ["draft", "in_review", "approved", "archived"];

export function ApprovalWorkflow({ card, onStatusChange, isUpdating }: ApprovalWorkflowProps) {
  const { user } = useAuth();
  const isAdmin = user?.role === "admin";
  const currentStatus = card.status as CardStatus;
  const config = STATUS_CONFIG[currentStatus];

  return (
    <div className="space-y-4">
      {/* Current status badge */}
      <div className="flex items-center gap-3">
        <span className="text-sm font-medium text-muted-foreground">Status:</span>
        <span className={cn("inline-flex items-center rounded-full px-3 py-1 text-xs font-semibold", config.bgColor, config.color)}>
          {config.label}
        </span>
      </div>

      {/* Status progress bar */}
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
                <div className={cn("mx-1 h-0.5 flex-1", isCompleted && index < currentIndex ? "bg-primary/50" : "bg-muted")} />
              )}
            </div>
          );
        })}
      </div>
      <div className="flex justify-between text-xs text-muted-foreground">
        {STATUS_ORDER.map((status) => (
          <span key={status} className="w-8 text-center">{STATUS_CONFIG[status].label}</span>
        ))}
      </div>

      {/* Approval info */}
      {currentStatus === "approved" && card.approved_at && (
        <div className="rounded-md border border-green-200 bg-green-50 p-3">
          <div className="flex items-center gap-2 text-sm text-green-800">
            <CheckCircle2 className="h-4 w-4" />
            <span>
              Approved on {new Date(card.approved_at).toLocaleDateString()}
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
          <p className="text-xs text-muted-foreground italic">Only admins can approve cards.</p>
        )}

        {currentStatus !== "archived" && (
          <button
            onClick={() => onStatusChange("archived")}
            disabled={isUpdating}
            className="inline-flex items-center gap-2 rounded-md border border-input bg-background px-4 py-2 text-sm font-medium text-muted-foreground transition-colors hover:bg-muted disabled:opacity-50"
          >
            <Archive className="h-4 w-4" />
            Archive
          </button>
        )}
      </div>
    </div>
  );
}


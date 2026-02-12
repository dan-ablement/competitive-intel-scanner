import { History, ArrowRight } from "lucide-react";
import { useCardHistory } from "@/hooks/use-cards";
import type { CardEditResponse } from "@/api/cards";

interface EditHistoryProps {
  cardId: string;
}

const FIELD_LABELS: Record<string, string> = {
  title: "Title",
  summary: "Summary",
  impact_assessment: "Impact Assessment",
  suggested_counter_moves: "Counter Moves",
  event_type: "Event Type",
  priority: "Priority",
};

function EditItem({ edit }: { edit: CardEditResponse }) {
  const fieldLabel = FIELD_LABELS[edit.field_changed] ?? edit.field_changed;
  const isLongText = edit.previous_value.length > 80 || edit.new_value.length > 80;

  return (
    <div className="relative flex gap-3 pb-6 last:pb-0">
      {/* Timeline line */}
      <div className="absolute left-[13px] top-7 h-[calc(100%-12px)] w-px bg-border last:hidden" />

      {/* Timeline dot */}
      <div className="relative z-10 mt-1 flex h-7 w-7 shrink-0 items-center justify-center rounded-full border bg-background">
        <div className="h-2 w-2 rounded-full bg-primary" />
      </div>

      <div className="flex-1 space-y-1">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium">{edit.user_name}</span>
          <span className="text-xs text-muted-foreground">
            edited <span className="font-medium text-foreground">{fieldLabel}</span>
          </span>
        </div>
        <p className="text-xs text-muted-foreground">
          {new Date(edit.created_at).toLocaleString()}
        </p>

        {/* Diff display */}
        {isLongText ? (
          <div className="mt-2 space-y-1">
            <div className="rounded border border-red-200 bg-red-50 p-2">
              <p className="text-xs text-red-800 line-through">{truncate(edit.previous_value, 200)}</p>
            </div>
            <div className="rounded border border-green-200 bg-green-50 p-2">
              <p className="text-xs text-green-800">{truncate(edit.new_value, 200)}</p>
            </div>
          </div>
        ) : (
          <div className="mt-1 flex items-center gap-2 text-xs">
            <span className="rounded bg-red-100 px-1.5 py-0.5 text-red-700 line-through">
              {edit.previous_value || "(empty)"}
            </span>
            <ArrowRight className="h-3 w-3 text-muted-foreground" />
            <span className="rounded bg-green-100 px-1.5 py-0.5 text-green-700">
              {edit.new_value || "(empty)"}
            </span>
          </div>
        )}
      </div>
    </div>
  );
}

function truncate(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength) + "…";
}

export function EditHistory({ cardId }: EditHistoryProps) {
  const { data: edits, isLoading } = useCardHistory(cardId);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="h-6 w-6 animate-spin rounded-full border-2 border-primary border-t-transparent" />
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center gap-2 border-b px-4 py-3">
        <History className="h-5 w-5 text-muted-foreground" />
        <h3 className="text-sm font-semibold">Edit History</h3>
        <span className="text-xs text-muted-foreground">({edits?.length ?? 0})</span>
      </div>

      <div className="flex-1 overflow-auto p-4">
        {edits && edits.length > 0 ? (
          <div className="space-y-0">
            {edits.map((edit) => (
              <EditItem key={edit.id} edit={edit} />
            ))}
          </div>
        ) : (
          <p className="py-8 text-center text-sm text-muted-foreground">No edits recorded yet</p>
        )}
      </div>
    </div>
  );
}


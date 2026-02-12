export type SuggestionTargetType = "competitor" | "augment";

export type SuggestionStatus = "pending" | "approved" | "rejected";

export interface ProfileUpdateSuggestion {
  id: string;
  target_type: SuggestionTargetType;
  competitor_id: string | null;
  field: string;
  current_value: string;
  suggested_value: string;
  reason: string;
  source_card_ids: string[];
  status: SuggestionStatus;
  reviewed_by: string | null;
  reviewed_at: string | null;
  created_at: string;
}


export type EventType =
  | "new_feature"
  | "product_announcement"
  | "partnership"
  | "acquisition"
  | "acquired"
  | "funding"
  | "pricing_change"
  | "leadership_change"
  | "expansion"
  | "other";

export type Priority = "red" | "yellow" | "green";

export type CardStatus = "draft" | "in_review" | "approved" | "archived";

export interface CompetitorBrief {
  id: string;
  name: string;
}

export interface AnalysisCard {
  id: string;
  feed_item_id: string | null;
  event_type: EventType;
  priority: Priority;
  title: string;
  summary: string;
  impact_assessment?: string;
  suggested_counter_moves?: string;
  raw_llm_output: Record<string, unknown>;
  status: CardStatus;
  approved_by: string | null;
  approved_at: string | null;
  check_run_id: string | null;
  competitors: CompetitorBrief[];
  created_at: string;
  updated_at: string;
}

export interface AnalysisCardEdit {
  id: string;
  analysis_card_id: string;
  user_id: string;
  field_changed: string;
  previous_value: string;
  new_value: string;
  created_at: string;
}

export interface AnalysisCardComment {
  id: string;
  analysis_card_id: string;
  user_id: string;
  content: string;
  parent_comment_id: string | null;
  resolved: boolean;
  created_at: string;
  updated_at: string;
}


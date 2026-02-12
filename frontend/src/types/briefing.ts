export type BriefingStatus = "draft" | "in_review" | "approved" | "archived";

export interface Briefing {
  id: string;
  date: string;
  content: string;
  raw_llm_output: Record<string, unknown>;
  status: BriefingStatus;
  approved_by: string | null;
  approved_at: string | null;
  card_ids: string[];
  created_at: string;
  updated_at: string;
}


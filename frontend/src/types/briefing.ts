export type BriefingStatus = "draft" | "in_review" | "approved" | "archived";

export interface BriefingCard {
  id: string;
  title: string;
  priority: "red" | "yellow" | "green";
  event_type: string;
  status: string;
}

export interface Briefing {
  id: string;
  date: string;
  content: string;
  raw_llm_output: Record<string, unknown>;
  status: BriefingStatus;
  approved_by: string | null;
  approved_at: string | null;
  cards: BriefingCard[];
  created_at: string;
  updated_at: string;
}


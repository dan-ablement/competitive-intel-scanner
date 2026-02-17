export type ContentOutputStatus = "draft" | "approved" | "published";

export interface ContentOutput {
  id: string;
  competitor_id: string;
  content_type: string;
  content: string;
  source_card_ids: string[];
  version: number;
  status: ContentOutputStatus;
  created_at: string;
  updated_at: string;
}


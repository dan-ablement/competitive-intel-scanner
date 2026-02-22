export type ContentOutputStatus =
  | "draft"
  | "generating"
  | "in_review"
  | "approved"
  | "published"
  | "failed";

export interface ContentOutput {
  id: string;
  competitor_id: string;
  content_type: string;
  title: string;
  content: string;
  template_id: string | null;
  source_card_ids: string[];
  version: number;
  status: ContentOutputStatus;
  google_doc_id: string | null;
  google_doc_url: string | null;
  approved_by: string | null;
  approved_by_name: string | null;
  approved_at: string | null;
  published_at: string | null;
  raw_llm_output: Record<string, unknown> | null;
  error_message: string | null;
  competitor_name: string | null;
  created_at: string;
  updated_at: string;
}


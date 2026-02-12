export interface RssFeed {
  id: string;
  name: string;
  url: string;
  competitor_id: string | null;
  competitor_name: string | null;
  is_active: boolean;
  last_checked_at: string | null;
  last_successful_at: string | null;
  error_count: number;
  last_error: string | null;
  created_by: string;
  created_at: string;
  updated_at: string;
}


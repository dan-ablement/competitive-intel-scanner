export interface RssFeed {
  id: string;
  name: string;
  url: string;
  feed_type: 'rss' | 'web_scrape' | 'twitter';
  css_selector: string | null;
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
  // Twitter-specific fields (populated when feed_type === 'twitter')
  x_username?: string;
  x_user_id?: string;
  backfill_completed?: boolean;
  include_retweets?: boolean;
  include_replies?: boolean;
}


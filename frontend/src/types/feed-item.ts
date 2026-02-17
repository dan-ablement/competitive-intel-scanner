export interface FeedItem {
  id: string;
  feed_id: string;
  guid: string;
  title: string;
  url: string;
  author: string | null;
  published_at: string;
  raw_content: string;
  is_processed: boolean;
  is_relevant: boolean | null;
  irrelevance_reason: string | null;
  created_at: string;
}


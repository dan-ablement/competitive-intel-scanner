import { apiClient } from "./client";
import type { RssFeed } from "@/types";

export interface TestFeedResult {
  success: boolean;
  message: string;
  item_count: number;
}

export async function listFeeds(): Promise<RssFeed[]> {
  const { data } = await apiClient.get<RssFeed[]>("/feeds");
  return data;
}

export async function createFeed(feed: Partial<RssFeed>): Promise<RssFeed> {
  const { data } = await apiClient.post<RssFeed>("/feeds", feed);
  return data;
}

export async function updateFeed(id: string, feed: Partial<RssFeed>): Promise<RssFeed> {
  const { data } = await apiClient.put<RssFeed>(`/feeds/${id}`, feed);
  return data;
}

export async function deleteFeed(id: string): Promise<void> {
  await apiClient.delete(`/feeds/${id}`);
}

export async function testFeed(id: string): Promise<TestFeedResult> {
  const { data } = await apiClient.post<TestFeedResult>(`/feeds/${id}/test`);
  return data;
}

export interface TestFeedUrlPayload {
  url: string;
  feed_type?: 'rss' | 'web_scrape' | 'twitter';
  css_selector?: string | null;
}

export async function testFeedUrl(payload: TestFeedUrlPayload): Promise<TestFeedResult> {
  const { data } = await apiClient.post<TestFeedResult>("/feeds/test-url", payload);
  return data;
}

// ---------------------------------------------------------------------------
// Twitter validation
// ---------------------------------------------------------------------------

export interface TwitterValidationResult {
  valid: boolean;
  user_id: string;
  username: string;
  name: string;
  profile_image_url: string;
  description: string;
  followers_count: number;
  tweet_count: number;
  error?: string;
}

export async function validateTwitterUsername(
  username: string,
): Promise<TwitterValidationResult> {
  const { data } = await apiClient.post<TwitterValidationResult>(
    "/feeds/validate-twitter",
    { username },
  );
  return data;
}

// ---------------------------------------------------------------------------
// Re-backfill
// ---------------------------------------------------------------------------

export async function rebackfillFeed(
  feedId: string,
  days: number,
): Promise<{ message: string }> {
  const { data } = await apiClient.post<{ message: string }>(
    `/feeds/${feedId}/rebackfill`,
    { days },
  );
  return data;
}


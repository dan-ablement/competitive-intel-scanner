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

export async function testFeedUrl(url: string): Promise<TestFeedResult> {
  const { data } = await apiClient.post<TestFeedResult>("/feeds/test-url", { url });
  return data;
}


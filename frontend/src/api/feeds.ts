import { apiClient } from "./client";
import type { RssFeed } from "@/types";

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

export async function testFeed(id: string): Promise<{ success: boolean; message: string }> {
  const { data } = await apiClient.post<{ success: boolean; message: string }>(`/feeds/${id}/test`);
  return data;
}


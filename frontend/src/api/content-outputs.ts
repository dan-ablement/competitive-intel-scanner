import { apiClient } from "./client";
import type { ContentOutput, ContentOutputStatus } from "@/types";

export interface ContentOutputFilters {
  competitor_id?: string;
  content_type?: string;
  status?: ContentOutputStatus;
  template_id?: string;
}

export interface StaleContentItem {
  competitor_id: string;
  competitor_name: string;
  template_id: string;
  template_name: string;
  content_type: string;
  last_output_id: string | null;
  last_output_at: string | null;
  status: ContentOutputStatus | null;
}

export async function listContentOutputs(filters?: ContentOutputFilters): Promise<ContentOutput[]> {
  const { data } = await apiClient.get<ContentOutput[]>("/content-outputs", { params: filters });
  return data;
}

export async function getContentOutput(id: string): Promise<ContentOutput> {
  const { data } = await apiClient.get<ContentOutput>(`/content-outputs/${id}`);
  return data;
}

export async function generateDraft(competitorId: string, templateId: string): Promise<ContentOutput> {
  const { data } = await apiClient.post<ContentOutput>("/content-outputs/generate", {
    competitor_id: competitorId,
    template_id: templateId,
  });
  return data;
}

export async function updateContentOutput(id: string, output: Partial<ContentOutput>): Promise<ContentOutput> {
  const { data } = await apiClient.put<ContentOutput>(`/content-outputs/${id}`, output);
  return data;
}

export async function changeContentOutputStatus(id: string, status: ContentOutputStatus): Promise<ContentOutput> {
  const { data } = await apiClient.patch<ContentOutput>(`/content-outputs/${id}/status`, { status });
  return data;
}

export async function getStaleContent(): Promise<StaleContentItem[]> {
  const { data } = await apiClient.get<StaleContentItem[]>("/content-outputs/stale");
  return data;
}


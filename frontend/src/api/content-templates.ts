import { apiClient } from "./client";
import type { ContentTemplate } from "@/types";

export async function listContentTemplates(): Promise<ContentTemplate[]> {
  const { data } = await apiClient.get<ContentTemplate[]>("/content-templates");
  return data;
}

export async function getContentTemplate(id: string): Promise<ContentTemplate> {
  const { data } = await apiClient.get<ContentTemplate>(`/content-templates/${id}`);
  return data;
}

export async function createContentTemplate(
  template: Omit<ContentTemplate, "id" | "created_at" | "updated_at">,
): Promise<ContentTemplate> {
  const { data } = await apiClient.post<ContentTemplate>("/content-templates", template);
  return data;
}

export async function updateContentTemplate(
  id: string,
  template: Partial<ContentTemplate>,
): Promise<ContentTemplate> {
  const { data } = await apiClient.put<ContentTemplate>(`/content-templates/${id}`, template);
  return data;
}

export async function deleteContentTemplate(id: string): Promise<void> {
  await apiClient.delete(`/content-templates/${id}`);
}


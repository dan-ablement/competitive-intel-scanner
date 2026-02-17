import { apiClient } from "./client";
import type { ProfileUpdateSuggestion } from "@/types";

export async function listSuggestions(): Promise<ProfileUpdateSuggestion[]> {
  const { data } = await apiClient.get<ProfileUpdateSuggestion[]>("/suggestions");
  return data;
}

export async function approveSuggestion(id: string): Promise<ProfileUpdateSuggestion> {
  const { data } = await apiClient.post<ProfileUpdateSuggestion>(`/suggestions/${id}/approve`);
  return data;
}

export async function rejectSuggestion(id: string): Promise<ProfileUpdateSuggestion> {
  const { data } = await apiClient.post<ProfileUpdateSuggestion>(`/suggestions/${id}/reject`);
  return data;
}


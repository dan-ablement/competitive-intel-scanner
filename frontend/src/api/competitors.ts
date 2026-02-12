import { apiClient } from "./client";
import type { Competitor } from "@/types";

export async function listCompetitors(params?: { is_suggested?: boolean }): Promise<Competitor[]> {
  const { data } = await apiClient.get<Competitor[]>("/competitors", { params });
  return data;
}

export async function getCompetitor(id: string): Promise<Competitor> {
  const { data } = await apiClient.get<Competitor>(`/competitors/${id}`);
  return data;
}

export async function createCompetitor(competitor: Partial<Competitor>): Promise<Competitor> {
  const { data } = await apiClient.post<Competitor>("/competitors", competitor);
  return data;
}

export async function updateCompetitor(id: string, competitor: Partial<Competitor>): Promise<Competitor> {
  const { data } = await apiClient.put<Competitor>(`/competitors/${id}`, competitor);
  return data;
}

export async function deleteCompetitor(id: string): Promise<void> {
  await apiClient.delete(`/competitors/${id}`);
}

export async function approveCompetitor(id: string): Promise<Competitor> {
  const { data } = await apiClient.post<Competitor>(`/competitors/${id}/approve`);
  return data;
}

export async function rejectCompetitor(id: string): Promise<void> {
  await apiClient.post(`/competitors/${id}/reject`);
}


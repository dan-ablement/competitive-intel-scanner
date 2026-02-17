import { apiClient } from "./client";
import type { Briefing, BriefingStatus } from "@/types";

export async function listBriefings(): Promise<Briefing[]> {
  const { data } = await apiClient.get<Briefing[]>("/briefings");
  return data;
}

export async function getBriefing(id: string): Promise<Briefing> {
  const { data } = await apiClient.get<Briefing>(`/briefings/${id}`);
  return data;
}

export async function updateBriefing(id: string, briefing: Partial<Briefing>): Promise<Briefing> {
  const { data } = await apiClient.put<Briefing>(`/briefings/${id}`, briefing);
  return data;
}

export async function changeBriefingStatus(id: string, status: BriefingStatus): Promise<Briefing> {
  const { data } = await apiClient.post<Briefing>(`/briefings/${id}/status`, { status });
  return data;
}


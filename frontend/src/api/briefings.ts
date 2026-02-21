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

export interface ApproveAllResponse {
  message: string;
  cards_approved: number;
}

export async function approveAllBriefingCards(briefingId: string): Promise<ApproveAllResponse> {
  const { data } = await apiClient.post<ApproveAllResponse>(`/briefings/${briefingId}/approve-all`);
  return data;
}


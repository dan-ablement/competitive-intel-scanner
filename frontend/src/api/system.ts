import { apiClient } from "./client";
import type { CheckRun } from "@/types";

export async function triggerFeedCheck(generateBriefing = false): Promise<CheckRun> {
  const params = generateBriefing ? { generate_briefing: true } : {};
  const { data } = await apiClient.post<CheckRun>("/check-feeds", null, { params });
  return data;
}

export async function triggerProfileReview(): Promise<{ message: string }> {
  const { data } = await apiClient.post<{ message: string }>("/maintenance/review-profiles");
  return data;
}

export async function listCheckRuns(): Promise<CheckRun[]> {
  const { data } = await apiClient.get<CheckRun[]>("/check-runs");
  return data;
}

export interface SystemSettings {
  [key: string]: unknown;
}

export async function getSettings(): Promise<SystemSettings> {
  const { data } = await apiClient.get<SystemSettings>("/settings");
  return data;
}

export async function updateSettings(settings: SystemSettings): Promise<SystemSettings> {
  const { data } = await apiClient.put<SystemSettings>("/settings", settings);
  return data;
}


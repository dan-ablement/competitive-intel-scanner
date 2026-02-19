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

export interface KVSetting {
  key: string;
  value: string | null;
}

export async function getKVSetting(key: string): Promise<KVSetting> {
  const { data } = await apiClient.get<KVSetting>(`/settings/kv/${key}`);
  return data;
}

export async function setKVSetting(key: string, value: string | null): Promise<KVSetting> {
  const { data } = await apiClient.put<KVSetting>(`/settings/kv/${key}`, { value });
  return data;
}


import { apiClient } from "./client";
import type { User } from "@/types";

export async function getCurrentUser(): Promise<User> {
  const { data } = await apiClient.get<User>("/auth/me");
  return data;
}

export async function logout(): Promise<void> {
  await apiClient.post("/auth/logout");
}

export function getGoogleAuthUrl(): string {
  return "/api/auth/google";
}


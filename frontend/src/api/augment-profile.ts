import { apiClient } from "./client";
import type { AugmentProfile } from "@/types";

export async function getAugmentProfile(): Promise<AugmentProfile> {
  const { data } = await apiClient.get<AugmentProfile>("/augment-profile");
  return data;
}

export async function updateAugmentProfile(profile: Partial<AugmentProfile>): Promise<AugmentProfile> {
  const { data } = await apiClient.put<AugmentProfile>("/augment-profile", profile);
  return data;
}


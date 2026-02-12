import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getAugmentProfile, updateAugmentProfile } from "@/api/augment-profile";
import type { AugmentProfile } from "@/types";

export function useAugmentProfile() {
  return useQuery({
    queryKey: ["augment-profile"],
    queryFn: getAugmentProfile,
  });
}

export function useUpdateAugmentProfile() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (profile: Partial<AugmentProfile>) => updateAugmentProfile(profile),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["augment-profile"] }),
  });
}


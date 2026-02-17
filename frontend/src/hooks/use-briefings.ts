import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { listBriefings, getBriefing, updateBriefing, changeBriefingStatus } from "@/api/briefings";
import type { Briefing, BriefingStatus } from "@/types";

export function useBriefings() {
  return useQuery({
    queryKey: ["briefings"],
    queryFn: listBriefings,
  });
}

export function useBriefing(id: string) {
  return useQuery({
    queryKey: ["briefings", id],
    queryFn: () => getBriefing(id),
    enabled: !!id,
  });
}

export function useUpdateBriefing() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, briefing }: { id: string; briefing: Partial<Briefing> }) => updateBriefing(id, briefing),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["briefings"] }),
  });
}

export function useChangeBriefingStatus() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, status }: { id: string; status: BriefingStatus }) => changeBriefingStatus(id, status),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["briefings"] }),
  });
}


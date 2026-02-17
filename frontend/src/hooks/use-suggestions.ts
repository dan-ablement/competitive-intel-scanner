import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { listSuggestions, approveSuggestion, rejectSuggestion } from "@/api/suggestions";

export function useSuggestions() {
  return useQuery({
    queryKey: ["suggestions"],
    queryFn: listSuggestions,
  });
}

export function useApproveSuggestion() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: approveSuggestion,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["suggestions"] }),
  });
}

export function useRejectSuggestion() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: rejectSuggestion,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["suggestions"] }),
  });
}


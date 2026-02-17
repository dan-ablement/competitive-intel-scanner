import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { listCompetitors, getCompetitor, createCompetitor, updateCompetitor, deleteCompetitor, approveCompetitor, rejectCompetitor } from "@/api/competitors";
import type { Competitor } from "@/types";

export function useCompetitors(params?: { is_suggested?: boolean }) {
  return useQuery({
    queryKey: ["competitors", params],
    queryFn: () => listCompetitors(params),
  });
}

export function useCompetitor(id: string) {
  return useQuery({
    queryKey: ["competitors", id],
    queryFn: () => getCompetitor(id),
    enabled: !!id,
  });
}

export function useCreateCompetitor() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (competitor: Partial<Competitor>) => createCompetitor(competitor),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["competitors"] }),
  });
}

export function useUpdateCompetitor() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, competitor }: { id: string; competitor: Partial<Competitor> }) => updateCompetitor(id, competitor),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["competitors"] }),
  });
}

export function useDeleteCompetitor() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: deleteCompetitor,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["competitors"] }),
  });
}

export function useApproveCompetitor() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: approveCompetitor,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["competitors"] }),
  });
}

export function useRejectCompetitor() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: rejectCompetitor,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["competitors"] }),
  });
}


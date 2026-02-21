import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  listContentOutputs,
  getContentOutput,
  generateDraft,
  updateContentOutput,
  changeContentOutputStatus,
  deleteContentOutput,
  publishContentOutput,
  getStaleContent,
  type ContentOutputFilters,
} from "@/api/content-outputs";
import type { ContentOutput, ContentOutputStatus } from "@/types";

export function useContentOutputs(filters?: ContentOutputFilters) {
  return useQuery({
    queryKey: ["content-outputs", filters],
    queryFn: () => listContentOutputs(filters),
  });
}

export function useContentOutput(id: string) {
  return useQuery({
    queryKey: ["content-outputs", id],
    queryFn: () => getContentOutput(id),
    enabled: !!id,
  });
}

export function useGenerateDraft() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ competitorId, templateId }: { competitorId: string; templateId: string }) =>
      generateDraft(competitorId, templateId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["content-outputs"] });
      queryClient.invalidateQueries({ queryKey: ["content-templates"] });
    },
  });
}

export function useUpdateContentOutput() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, output }: { id: string; output: Partial<ContentOutput> }) =>
      updateContentOutput(id, output),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: ["content-outputs"] });
      queryClient.invalidateQueries({ queryKey: ["content-outputs", variables.id] });
    },
  });
}

export function useChangeContentOutputStatus() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, status }: { id: string; status: ContentOutputStatus }) =>
      changeContentOutputStatus(id, status),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["content-outputs"] });
      queryClient.invalidateQueries({ queryKey: ["content-templates"] });
    },
  });
}

export function useDeleteContentOutput() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => deleteContentOutput(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["content-outputs"] });
    },
  });
}

export function usePublishContentOutput() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => publishContentOutput(id),
    onSuccess: (_data, id) => {
      queryClient.invalidateQueries({ queryKey: ["content-outputs"] });
      queryClient.invalidateQueries({ queryKey: ["content-outputs", id] });
    },
  });
}

export function useStaleContent() {
  return useQuery({
    queryKey: ["content-outputs", "stale"],
    queryFn: () => getStaleContent(),
  });
}


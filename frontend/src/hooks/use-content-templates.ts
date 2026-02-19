import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  listContentTemplates,
  getContentTemplate,
  createContentTemplate,
  updateContentTemplate,
  deleteContentTemplate,
} from "@/api/content-templates";
import type { ContentTemplate } from "@/types";

export function useContentTemplates() {
  return useQuery({
    queryKey: ["content-templates"],
    queryFn: () => listContentTemplates(),
  });
}

export function useContentTemplate(id: string) {
  return useQuery({
    queryKey: ["content-templates", id],
    queryFn: () => getContentTemplate(id),
    enabled: !!id,
  });
}

export function useCreateContentTemplate() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (template: Omit<ContentTemplate, "id" | "created_at" | "updated_at">) =>
      createContentTemplate(template),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["content-templates"] }),
  });
}

export function useUpdateContentTemplate() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, template }: { id: string; template: Partial<ContentTemplate> }) =>
      updateContentTemplate(id, template),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: ["content-templates"] });
      queryClient.invalidateQueries({ queryKey: ["content-templates", variables.id] });
    },
  });
}

export function useDeleteContentTemplate() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => deleteContentTemplate(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["content-templates"] });
      queryClient.invalidateQueries({ queryKey: ["content-outputs"] });
    },
  });
}


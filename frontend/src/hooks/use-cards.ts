import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  listCards,
  getCard,
  updateCard,
  changeCardStatus,
  getCardHistory,
  listCardComments,
  addCardComment,
  updateCardComment,
  resolveCardComment,
  type CardFilters,
} from "@/api/cards";
import type { AnalysisCard, CardStatus } from "@/types";

export function useCards(filters?: CardFilters) {
  return useQuery({
    queryKey: ["cards", filters],
    queryFn: () => listCards(filters),
  });
}

export function useCard(id: string) {
  return useQuery({
    queryKey: ["cards", id],
    queryFn: () => getCard(id),
    enabled: !!id,
  });
}

export function useUpdateCard() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, card }: { id: string; card: Partial<AnalysisCard> }) => updateCard(id, card),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: ["cards"] });
      queryClient.invalidateQueries({ queryKey: ["cards", variables.id, "history"] });
    },
  });
}

export function useChangeCardStatus() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, status }: { id: string; status: CardStatus }) => changeCardStatus(id, status),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["cards"] }),
  });
}

export function useCardHistory(id: string) {
  return useQuery({
    queryKey: ["cards", id, "history"],
    queryFn: () => getCardHistory(id),
    enabled: !!id,
  });
}

export function useCardComments(id: string) {
  return useQuery({
    queryKey: ["cards", id, "comments"],
    queryFn: () => listCardComments(id),
    enabled: !!id,
  });
}

export function useAddCardComment() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, comment }: { id: string; comment: { content: string; parent_comment_id?: string } }) =>
      addCardComment(id, comment),
    onSuccess: (_data, variables) =>
      queryClient.invalidateQueries({ queryKey: ["cards", variables.id, "comments"] }),
  });
}

export function useUpdateCardComment() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ cardId, commentId, content }: { cardId: string; commentId: string; content: string }) =>
      updateCardComment(cardId, commentId, { content }),
    onSuccess: (_data, variables) =>
      queryClient.invalidateQueries({ queryKey: ["cards", variables.cardId, "comments"] }),
  });
}

export function useResolveCardComment() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ cardId, commentId }: { cardId: string; commentId: string }) =>
      resolveCardComment(cardId, commentId),
    onSuccess: (_data, variables) =>
      queryClient.invalidateQueries({ queryKey: ["cards", variables.cardId, "comments"] }),
  });
}


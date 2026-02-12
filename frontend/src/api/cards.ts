import { apiClient } from "./client";
import type { AnalysisCard, AnalysisCardComment, AnalysisCardEdit, CardStatus, Priority } from "@/types";

export interface CardFilters {
  status?: CardStatus;
  priority?: Priority;
  competitor_id?: string;
  date_from?: string;
  date_to?: string;
}

export async function listCards(filters?: CardFilters): Promise<AnalysisCard[]> {
  const { data } = await apiClient.get<AnalysisCard[]>("/cards", { params: filters });
  return data;
}

export async function getCard(id: string): Promise<AnalysisCard> {
  const { data } = await apiClient.get<AnalysisCard>(`/cards/${id}`);
  return data;
}

export async function updateCard(id: string, card: Partial<AnalysisCard>): Promise<AnalysisCard> {
  const { data } = await apiClient.put<AnalysisCard>(`/cards/${id}`, card);
  return data;
}

export async function changeCardStatus(id: string, status: CardStatus): Promise<AnalysisCard> {
  const { data } = await apiClient.post<AnalysisCard>(`/cards/${id}/status`, { status });
  return data;
}

export async function getCardHistory(id: string): Promise<AnalysisCardEdit[]> {
  const { data } = await apiClient.get<AnalysisCardEdit[]>(`/cards/${id}/history`);
  return data;
}

export async function addCardComment(id: string, comment: { content: string; parent_comment_id?: string }): Promise<AnalysisCardComment> {
  const { data } = await apiClient.post<AnalysisCardComment>(`/cards/${id}/comments`, comment);
  return data;
}

export async function updateCardComment(cardId: string, commentId: string, comment: { content: string }): Promise<AnalysisCardComment> {
  const { data } = await apiClient.put<AnalysisCardComment>(`/cards/${cardId}/comments/${commentId}`, comment);
  return data;
}

export async function resolveCardComment(cardId: string, commentId: string): Promise<AnalysisCardComment> {
  const { data } = await apiClient.post<AnalysisCardComment>(`/cards/${cardId}/comments/${commentId}/resolve`);
  return data;
}


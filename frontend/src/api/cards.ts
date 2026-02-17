import { apiClient } from "./client";
import type { AnalysisCard, CardStatus, Priority } from "@/types";

export interface CardFilters {
  status?: CardStatus;
  priority?: Priority;
  competitor_id?: string;
  date_from?: string;
  date_to?: string;
}

/** Comment response from the API includes user_name and nested replies. */
export interface CardCommentResponse {
  id: string;
  analysis_card_id: string;
  user_id: string;
  user_name: string;
  content: string;
  parent_comment_id: string | null;
  resolved: boolean;
  created_at: string;
  updated_at: string;
  replies: CardCommentResponse[];
}

/** Edit response from the API includes user_name. */
export interface CardEditResponse {
  id: string;
  analysis_card_id: string;
  user_id: string;
  user_name: string;
  field_changed: string;
  previous_value: string;
  new_value: string;
  created_at: string;
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

export async function getCardHistory(id: string): Promise<CardEditResponse[]> {
  const { data } = await apiClient.get<CardEditResponse[]>(`/cards/${id}/history`);
  return data;
}

export async function listCardComments(id: string): Promise<CardCommentResponse[]> {
  const { data } = await apiClient.get<CardCommentResponse[]>(`/cards/${id}/comments`);
  return data;
}

export async function addCardComment(id: string, comment: { content: string; parent_comment_id?: string }): Promise<CardCommentResponse> {
  const { data } = await apiClient.post<CardCommentResponse>(`/cards/${id}/comments`, comment);
  return data;
}

export async function updateCardComment(cardId: string, commentId: string, comment: { content: string }): Promise<CardCommentResponse> {
  const { data } = await apiClient.put<CardCommentResponse>(`/cards/${cardId}/comments/${commentId}`, comment);
  return data;
}

export async function resolveCardComment(cardId: string, commentId: string): Promise<CardCommentResponse> {
  const { data } = await apiClient.post<CardCommentResponse>(`/cards/${cardId}/comments/${commentId}/resolve`);
  return data;
}


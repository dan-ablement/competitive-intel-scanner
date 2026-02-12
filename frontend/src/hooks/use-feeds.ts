import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { listFeeds, createFeed, updateFeed, deleteFeed, testFeed, testFeedUrl } from "@/api/feeds";
import type { RssFeed } from "@/types";

export function useFeeds() {
  return useQuery({
    queryKey: ["feeds"],
    queryFn: listFeeds,
  });
}

export function useCreateFeed() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (feed: Partial<RssFeed>) => createFeed(feed),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["feeds"] }),
  });
}

export function useUpdateFeed() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, feed }: { id: string; feed: Partial<RssFeed> }) => updateFeed(id, feed),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["feeds"] }),
  });
}

export function useDeleteFeed() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: deleteFeed,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["feeds"] }),
  });
}

export function useTestFeed() {
  return useMutation({
    mutationFn: testFeed,
  });
}

export function useTestFeedUrl() {
  return useMutation({
    mutationFn: testFeedUrl,
  });
}


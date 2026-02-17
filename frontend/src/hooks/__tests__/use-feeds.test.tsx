import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type { ReactNode } from "react";
import { useFeeds, useCreateFeed, useValidateTwitter } from "../use-feeds";

// Mock the API module
vi.mock("@/api/feeds", () => ({
  listFeeds: vi.fn(),
  createFeed: vi.fn(),
  updateFeed: vi.fn(),
  deleteFeed: vi.fn(),
  testFeed: vi.fn(),
  testFeedUrl: vi.fn(),
  validateTwitterUsername: vi.fn(),
  rebackfillFeed: vi.fn(),
}));

import {
  listFeeds,
  createFeed,
  validateTwitterUsername,
} from "@/api/feeds";

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });
  return function Wrapper({ children }: { children: ReactNode }) {
    return (
      <QueryClientProvider client={queryClient}>
        {children}
      </QueryClientProvider>
    );
  };
}

beforeEach(() => {
  vi.clearAllMocks();
});

describe("useFeeds", () => {
  it("fetches feeds using listFeeds", async () => {
    const mockFeeds = [{ id: "1", name: "Feed 1" }];
    vi.mocked(listFeeds).mockResolvedValue(mockFeeds as any);

    const { result } = renderHook(() => useFeeds(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual(mockFeeds);
    expect(listFeeds).toHaveBeenCalledOnce();
  });
});

describe("useCreateFeed", () => {
  it("calls createFeed and returns result", async () => {
    const newFeed = { id: "2", name: "New Feed" };
    vi.mocked(createFeed).mockResolvedValue(newFeed as any);

    const { result } = renderHook(() => useCreateFeed(), {
      wrapper: createWrapper(),
    });

    result.current.mutate({ name: "New Feed", url: "https://example.com" } as any);

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual(newFeed);
    expect(createFeed).toHaveBeenCalledWith({
      name: "New Feed",
      url: "https://example.com",
    });
  });
});

describe("useValidateTwitter", () => {
  it("calls validateTwitterUsername with the username", async () => {
    const mockResult = {
      valid: true,
      user_id: "123",
      username: "testuser",
      name: "Test",
      profile_image_url: "",
      description: "",
      followers_count: 0,
      tweet_count: 0,
    };
    vi.mocked(validateTwitterUsername).mockResolvedValue(mockResult);

    const { result } = renderHook(() => useValidateTwitter(), {
      wrapper: createWrapper(),
    });

    result.current.mutate("testuser");

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual(mockResult);
    expect(validateTwitterUsername).toHaveBeenCalledWith("testuser");
  });
});


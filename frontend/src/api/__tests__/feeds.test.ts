import { describe, it, expect, vi, beforeEach } from "vitest";
import { apiClient } from "../client";
import {
  listFeeds,
  createFeed,
  testFeedUrl,
  validateTwitterUsername,
  rebackfillFeed,
} from "../feeds";
import type { RssFeed } from "@/types";

vi.mock("../client", () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  },
}));

const mockFeed: RssFeed = {
  id: "feed-1",
  name: "Test Feed",
  url: "https://example.com/rss",
  feed_type: "rss",
  css_selector: null,
  competitor_id: null,
  competitor_name: null,
  is_active: true,
  last_checked_at: null,
  last_successful_at: null,
  error_count: 0,
  last_error: null,
  created_by: "user-1",
  created_at: "2025-01-01T00:00:00Z",
  updated_at: "2025-01-01T00:00:00Z",
};

beforeEach(() => {
  vi.clearAllMocks();
});

describe("listFeeds", () => {
  it("calls GET /feeds and returns data", async () => {
    vi.mocked(apiClient.get).mockResolvedValue({ data: [mockFeed] });

    const result = await listFeeds();

    expect(apiClient.get).toHaveBeenCalledWith("/feeds");
    expect(result).toEqual([mockFeed]);
  });
});

describe("createFeed", () => {
  it("calls POST /feeds with the feed payload", async () => {
    const payload: Partial<RssFeed> = { name: "New Feed", url: "https://example.com/rss" };
    vi.mocked(apiClient.post).mockResolvedValue({ data: mockFeed });

    const result = await createFeed(payload);

    expect(apiClient.post).toHaveBeenCalledWith("/feeds", payload);
    expect(result).toEqual(mockFeed);
  });
});

describe("validateTwitterUsername", () => {
  it("calls POST /feeds/validate-twitter with username", async () => {
    const mockResult = {
      valid: true,
      user_id: "123",
      username: "testuser",
      name: "Test User",
      profile_image_url: "https://example.com/img.jpg",
      description: "A test user",
      followers_count: 100,
      tweet_count: 50,
    };
    vi.mocked(apiClient.post).mockResolvedValue({ data: mockResult });

    const result = await validateTwitterUsername("testuser");

    expect(apiClient.post).toHaveBeenCalledWith("/feeds/validate-twitter", {
      username: "testuser",
    });
    expect(result).toEqual(mockResult);
  });
});

describe("testFeedUrl", () => {
  it("calls POST /feeds/test-url with the payload", async () => {
    const payload = { url: "https://example.com/rss", feed_type: "rss" as const };
    const mockResult = { success: true, message: "OK", item_count: 5 };
    vi.mocked(apiClient.post).mockResolvedValue({ data: mockResult });

    const result = await testFeedUrl(payload);

    expect(apiClient.post).toHaveBeenCalledWith("/feeds/test-url", payload);
    expect(result).toEqual(mockResult);
  });
});

describe("rebackfillFeed", () => {
  it("calls POST /feeds/{id}/rebackfill with days", async () => {
    const mockResult = { message: "Rebackfill started" };
    vi.mocked(apiClient.post).mockResolvedValue({ data: mockResult });

    const result = await rebackfillFeed("feed-1", 7);

    expect(apiClient.post).toHaveBeenCalledWith("/feeds/feed-1/rebackfill", { days: 7 });
    expect(result).toEqual(mockResult);
  });
});


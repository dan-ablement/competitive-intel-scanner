import { describe, it, expect } from "vitest";
import { cn } from "../utils";

describe("cn()", () => {
  it("returns empty string with no arguments", () => {
    expect(cn()).toBe("");
  });

  it("returns a single class unchanged", () => {
    expect(cn("text-red-500")).toBe("text-red-500");
  });

  it("merges multiple classes", () => {
    const result = cn("px-2 py-1", "font-bold");
    expect(result).toContain("px-2");
    expect(result).toContain("py-1");
    expect(result).toContain("font-bold");
  });

  it("handles conditional classes (falsy values ignored)", () => {
    const isActive = false;
    const result = cn("base", isActive && "active-class");
    expect(result).toContain("base");
    expect(result).not.toContain("active-class");
  });

  it("resolves tailwind conflicts (last wins)", () => {
    // twMerge should resolve conflicting utilities
    const result = cn("text-red-500", "text-blue-500");
    expect(result).toBe("text-blue-500");
  });
});


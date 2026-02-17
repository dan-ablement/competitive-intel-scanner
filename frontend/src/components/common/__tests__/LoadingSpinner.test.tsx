import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { LoadingSpinner } from "../LoadingSpinner";

describe("LoadingSpinner", () => {
  it("renders without crashing (full page by default)", () => {
    const { container } = render(<LoadingSpinner />);
    // The full-page wrapper div should be present
    const wrapper = container.querySelector("div.flex");
    expect(wrapper).toBeInTheDocument();
    // An SVG spinner should be rendered
    const svg = container.querySelector("svg");
    expect(svg).toBeInTheDocument();
  });

  it("renders inline when fullPage is false", () => {
    const { container } = render(<LoadingSpinner fullPage={false} />);
    // No wrapper div — the SVG should be the root element
    const wrapper = container.querySelector("div.flex");
    expect(wrapper).not.toBeInTheDocument();
    const svg = container.querySelector("svg");
    expect(svg).toBeInTheDocument();
  });
});


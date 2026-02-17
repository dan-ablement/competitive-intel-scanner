import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { EmptyState } from "../EmptyState";
import { Inbox } from "lucide-react";

describe("EmptyState", () => {
  it("renders with title and icon", () => {
    render(<EmptyState icon={Inbox} title="No items found" />);
    expect(screen.getByText("No items found")).toBeInTheDocument();
  });

  it("renders with description when provided", () => {
    render(
      <EmptyState
        icon={Inbox}
        title="No items"
        description="Try adding some items."
      />,
    );
    expect(screen.getByText("No items")).toBeInTheDocument();
    expect(screen.getByText("Try adding some items.")).toBeInTheDocument();
  });

  it("does not render description when not provided", () => {
    const { container } = render(
      <EmptyState icon={Inbox} title="Empty" />,
    );
    // Only one <p> (the title), no description paragraph
    const paragraphs = container.querySelectorAll("p");
    expect(paragraphs).toHaveLength(1);
  });
});


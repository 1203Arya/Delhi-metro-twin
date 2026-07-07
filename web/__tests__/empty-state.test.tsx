import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { EmptyState } from "@/components/ui/EmptyState";

describe("EmptyState", () => {
  it("renders title and description", () => {
    render(<EmptyState title="Nothing here" description="Try again later" />);
    expect(screen.getByText("Nothing here")).toBeDefined();
    expect(screen.getByText("Try again later")).toBeDefined();
  });

  it("renders action button", () => {
    render(<EmptyState title="No data" action={{ label: "Refresh", onClick: () => {} }} />);
    expect(screen.getByText("Refresh")).toBeDefined();
  });
});

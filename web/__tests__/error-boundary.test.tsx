import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { ErrorBoundary } from "@/components/ui/ErrorBoundary";

function Buggy(): React.ReactNode {
  throw new Error("Test error");
}

describe("ErrorBoundary", () => {
  it("catches errors and shows fallback", () => {
    const spy = vi.spyOn(console, "error").mockImplementation(() => {});
    render(
      <ErrorBoundary>
        <Buggy />
      </ErrorBoundary>,
    );
    expect(screen.getByText("Something went wrong")).toBeDefined();
    expect(screen.getByText("Test error")).toBeDefined();
    spy.mockRestore();
  });
});

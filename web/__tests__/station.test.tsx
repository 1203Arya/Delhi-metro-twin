import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { StationPanel } from "@/components/panels/StationPanel";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type { ReactNode } from "react";

const wrapper = ({ children }: { children: ReactNode }) => {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return <QueryClientProvider client={qc}>{children}</QueryClientProvider>;
};

describe("StationPanel", () => {
  it("renders loading state", () => {
    render(<StationPanel stationId="test-id" onClose={() => {}} />, { wrapper });
    expect(screen.getByText("Station Details")).toBeDefined();
  });
});

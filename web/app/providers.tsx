"use client";

import type { ReactNode } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState, useEffect } from "react";
import { useThemeStore } from "@/stores/theme";
import { ErrorBoundary } from "@/components/ui/ErrorBoundary";

function ThemeInitializer({ children }: { children: ReactNode }) {
  const { setTheme } = useThemeStore();
  useEffect(() => {
    setTheme("dark");
  }, [setTheme]);
  return <>{children}</>;
}

export function Providers({ children }: { children: ReactNode }) {
  const [qc] = useState(() => new QueryClient({ defaultOptions: { queries: { staleTime: 10_000, retry: 1 } } }));

  return (
    <QueryClientProvider client={qc}>
      <ThemeInitializer>
        <ErrorBoundary>{children}</ErrorBoundary>
      </ThemeInitializer>
    </QueryClientProvider>
  );
}

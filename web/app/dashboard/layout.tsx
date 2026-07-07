"use client";

import { DashboardLayout } from "@/components/layout/DashboardLayout";
import type { ReactNode } from "react";

export default function DashboardPageLayout({ children }: { children: ReactNode }) {
  return <DashboardLayout>{children}</DashboardLayout>;
}

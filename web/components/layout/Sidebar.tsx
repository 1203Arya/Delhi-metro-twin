"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuthStore } from "@/stores/auth";
import { useThemeStore } from "@/stores/theme";
import { useState } from "react";

const NAV_ITEMS = [
  { href: "/", label: "Live Map", icon: "🗺" },
  { href: "/dashboard/timetable", label: "Timetable", icon: "📋" },
  { href: "/dashboard/delays", label: "Delay Analytics", icon: "⏱" },
  { href: "/dashboard/ai/eta", label: "ETA Prediction", icon: "🚄" },
  { href: "/dashboard/ai/delay", label: "Delay Prediction", icon: "📊" },
  { href: "/dashboard/ai/demand", label: "Demand Forecast", icon: "📈" },
  { href: "/dashboard/ai/crowd", label: "Crowd Forecast", icon: "👥" },
  { href: "/dashboard/ai/incident", label: "Incident Risk", icon: "⚠" },
];

export function Sidebar() {
  const pathname = usePathname();
  const { isAuthenticated, logout } = useAuthStore();
  const { theme, toggle } = useThemeStore();
  const [collapsed, setCollapsed] = useState(false);

  return (
    <aside
      className={`flex flex-col border-r border-surface-200 bg-white transition-all dark:border-surface-700 dark:bg-surface-900 ${
        collapsed ? "w-16" : "w-56"
      }`}
    >
      <div className="flex h-14 items-center border-b border-surface-200 px-4 dark:border-surface-700">
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="btn-ghost rounded-md p-1.5 text-lg"
        >
          {collapsed ? "☰" : "✕"}
        </button>
        {!collapsed && (
          <span className="ml-2 text-sm font-bold tracking-tight">
            DMDT Control
          </span>
        )}
      </div>

      <nav className="flex-1 overflow-y-auto p-2 scrollbar-thin">
        {NAV_ITEMS.map((item) => {
          const active = item.href === "/"
            ? pathname === "/"
            : pathname.startsWith(item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 rounded-md px-3 py-2 text-sm transition-colors ${
                active
                  ? "bg-blue-50 text-blue-700 dark:bg-blue-900/20 dark:text-blue-400"
                  : "text-surface-600 hover:bg-surface-100 dark:text-surface-400 dark:hover:bg-surface-800"
              }`}
              title={collapsed ? item.label : undefined}
            >
              <span className="text-base">{item.icon}</span>
              {!collapsed && <span>{item.label}</span>}
            </Link>
          );
        })}
      </nav>

      <div className="border-t border-surface-200 p-2 dark:border-surface-700">
        <button
          onClick={toggle}
          className="btn-ghost w-full justify-start gap-3 rounded-md px-3 py-2 text-sm"
          title="Toggle theme"
        >
          <span className="text-base">{theme === "dark" ? "☀️" : "🌙"}</span>
          {!collapsed && <span>{theme === "dark" ? "Light" : "Dark"}</span>}
        </button>
        {isAuthenticated && (
          <button
            onClick={() => { logout(); window.location.href = "/login"; }}
            className="btn-ghost w-full justify-start gap-3 rounded-md px-3 py-2 text-sm"
            title="Logout"
          >
            <span className="text-base">🚪</span>
            {!collapsed && <span>Logout</span>}
          </button>
        )}
      </div>
    </aside>
  );
}

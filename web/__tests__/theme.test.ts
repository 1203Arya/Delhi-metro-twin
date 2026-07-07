import { describe, it, expect } from "vitest";
import { useThemeStore } from "@/stores/theme";

describe("Theme Store", () => {
  it("defaults to dark", () => {
    expect(useThemeStore.getState().theme).toBe("dark");
  });

  it("toggle switches theme", () => {
    useThemeStore.getState().toggle();
    expect(useThemeStore.getState().theme).toBe("light");
    useThemeStore.getState().toggle();
    expect(useThemeStore.getState().theme).toBe("dark");
  });
});

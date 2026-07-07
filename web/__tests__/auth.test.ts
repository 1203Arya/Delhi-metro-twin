import { describe, it, expect } from "vitest";
import { useAuthStore } from "@/stores/auth";

describe("Auth Store", () => {
  it("starts unauthenticated", () => {
    const state = useAuthStore.getState();
    expect(state.isAuthenticated).toBe(false);
    expect(state.token).toBeNull();
  });

  it("login sets tokens", () => {
    const { login } = useAuthStore.getState();
    login({ access_token: "abc", refresh_token: "def", token_type: "bearer" });
    const state = useAuthStore.getState();
    expect(state.isAuthenticated).toBe(true);
    expect(state.token).toBe("abc");
    expect(state.refreshToken).toBe("def");
  });

  it("logout clears tokens", () => {
    const { logout } = useAuthStore.getState();
    logout();
    const state = useAuthStore.getState();
    expect(state.isAuthenticated).toBe(false);
    expect(state.token).toBeNull();
  });
});

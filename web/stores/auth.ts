import { create } from "zustand";
import type { TokenResponse } from "@/types/api";

interface AuthState {
  token: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  login: (tokens: TokenResponse) => void;
  logout: () => void;
  loadFromStorage: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  token: null,
  refreshToken: null,
  isAuthenticated: false,
  login: (tokens) => {
    localStorage.setItem("access_token", tokens.access_token);
    localStorage.setItem("refresh_token", tokens.refresh_token);
    set({ token: tokens.access_token, refreshToken: tokens.refresh_token, isAuthenticated: true });
  },
  logout: () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    set({ token: null, refreshToken: null, isAuthenticated: false });
  },
  loadFromStorage: () => {
    const token = localStorage.getItem("access_token");
    const refreshToken = localStorage.getItem("refresh_token");
    set({ token, refreshToken, isAuthenticated: !!token });
  },
}));

"use client";

import { useAuthStore } from "@/stores/auth";
import { api } from "@/lib/api";
import { useCallback, useEffect } from "react";
import { useRouter } from "next/navigation";

export function useAuth() {
  const { isAuthenticated, login, logout, loadFromStorage, token } = useAuthStore();
  const router = useRouter();

  useEffect(() => {
    loadFromStorage();
  }, [loadFromStorage]);

  const signIn = useCallback(
    async (username: string, password: string) => {
      const tokens = await api.auth.login({ username, password });
      login(tokens);
      router.push("/");
    },
    [login, router],
  );

  const signOut = useCallback(() => {
    logout();
    router.push("/login");
  }, [logout, router]);

  return { isAuthenticated, token, signIn, signOut };
}

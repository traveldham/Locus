"use client";

import { authApi, type AuthUser } from "@/services/api/auth";
import { getAccessToken, setAccessToken } from "@/services/api/client";
import { usePathname, useRouter } from "next/navigation";
import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";

interface AuthContextValue {
  user: AuthUser | null;
  activeOrganization: AuthUser["organizations"][number] | null;
  isLoading: boolean;
  login(email: string, password: string, nextPath?: string): Promise<void>;
  register(input: { full_name: string; email: string; password: string; organization_name: string }): Promise<void>;
  logout(): Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const [user, setUser] = useState<AuthUser | null>(null);
  const [isLoading, setIsLoading] = useState(
    () => pathname !== "/login" && pathname !== "/register",
  );

  const loadUser = useCallback(async () => {
    try {
      if (!getAccessToken()) {
        const response = await authApi.refresh();
        setAccessToken(response.access_token);
        setUser(response.user);
      } else {
        setUser(await authApi.me());
      }
    } catch {
      setAccessToken(null);
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    if ((pathname === "/login" || pathname === "/register") && !getAccessToken()) {
      return;
    }
    const timeout = window.setTimeout(() => void loadUser(), 0);
    return () => window.clearTimeout(timeout);
  }, [loadUser, pathname]);

  const value = useMemo<AuthContextValue>(() => ({
    user,
    activeOrganization: user?.organizations[0] ?? null,
    isLoading,
    login: async (email, password, nextPath = "/") => {
      const response = await authApi.login(email, password);
      setAccessToken(response.access_token);
      setUser(response.user);
      router.replace(nextPath);
      router.refresh();
    },
    register: async (input) => {
      const response = await authApi.register(input);
      setAccessToken(response.access_token);
      setUser(response.user);
      router.replace("/");
      router.refresh();
    },
    logout: async () => {
      try { await authApi.logout(); } catch { /* Local logout must always succeed. */ }
      setAccessToken(null);
      setUser(null);
      router.replace("/login");
      router.refresh();
    },
  }), [isLoading, router, user]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used inside AuthProvider");
  return context;
}

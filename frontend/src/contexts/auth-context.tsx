"use client";

import { authApi, type AuthUser } from "@/services/api/auth";
import { getAccessToken, setAccessToken } from "@/services/api/client";
import { usePathname, useRouter } from "next/navigation";
import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";

/** Routes that render for signed-out visitors and must not block on a session lookup. */
const PUBLIC_PATHS = new Set(["/login"]);

interface AuthContextValue {
  user: AuthUser | null;
  activeOrganization: AuthUser["organizations"][number] | null;
  isLoading: boolean;
  login(email: string, password: string, nextPath?: string): Promise<void>;
  logout(): Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const [user, setUser] = useState<AuthUser | null>(null);
  const [isLoading, setIsLoading] = useState(() => !PUBLIC_PATHS.has(pathname));

  const refreshSession = useCallback(async () => {
    try {
      const response = await authApi.refresh();
      setAccessToken(response.access_token);
      setUser(response.user);
    } catch {
      setAccessToken(null);
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const loadUser = useCallback(async () => {
    if (!getAccessToken()) {
      await refreshSession();
      return;
    }
    try {
      setUser(await authApi.me());
    } catch {
      setAccessToken(null);
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  }, [refreshSession]);

  useEffect(() => {
    if (PUBLIC_PATHS.has(pathname) && !getAccessToken()) return;
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

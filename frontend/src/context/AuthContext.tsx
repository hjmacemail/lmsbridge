import { createContext, useContext, useState, type ReactNode } from "react";
import type { AuthToken } from "../types";
import { api, clearToken, loadToken, saveToken } from "../api/client";

interface AuthCtx {
  auth: AuthToken | null;
  login: (email: string, password: string) => Promise<void>;
  adoptToken: (token: AuthToken) => void;
  logout: () => void;
}

const Ctx = createContext<AuthCtx | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [auth, setAuth] = useState<AuthToken | null>(() => loadToken());

  async function login(email: string, password: string) {
    const token = await api.login(email, password);
    saveToken(token);
    setAuth(token);
  }
  function adoptToken(token: AuthToken) {
    // Used by the LTI single-sign-on landing to establish a session from a launch token.
    saveToken(token);
    setAuth(token);
  }
  function logout() {
    clearToken();
    setAuth(null);
  }
  return (
    <Ctx.Provider value={{ auth, login, adoptToken, logout }}>{children}</Ctx.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}

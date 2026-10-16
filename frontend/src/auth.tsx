import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { api } from "./api";
import type { User } from "./types";

interface AuthState {
  token: string | null;
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, fullName: string, lang: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(() => localStorage.getItem("rg_token"));
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!token) {
      setLoading(false);
      return;
    }
    let active = true;
    setLoading(true);
    api
      .me(token)
      .then((data) => { if (active) setUser(data); })
      .catch(() => {
        if (!active) return;
        setUser(null);
        localStorage.removeItem("rg_token");
        setToken(null);
      })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [token]);

  const login = useCallback(async (email: string, password: string) => {
    const res = await api.login({ email, password });
    localStorage.setItem("rg_token", res.access_token);
    setToken(res.access_token);
    setUser(res.user as User);
  }, []);

  const register = useCallback(
    async (email: string, password: string, fullName: string, lang: string) => {
      const res = await api.register({
        email,
        password,
        full_name: fullName,
        preferred_language: lang,
      });
      localStorage.setItem("rg_token", res.access_token);
      setToken(res.access_token);
      setUser(res.user as User);
    },
    []
  );

  const logout = useCallback(() => {
    localStorage.removeItem("rg_token");
    setToken(null);
    setUser(null);
  }, []);

  const value = useMemo(
    () => ({ token, user, loading, login, register, logout }),
    [token, user, loading, login, register, logout]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth outside provider");
  return ctx;
}

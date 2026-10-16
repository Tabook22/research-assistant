import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { api, ApiError } from "./api";
import type { User } from "./types";

interface AuthState {
  token: string | null;
  user: User | null;
  loading: boolean;
  error: string | null;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, fullName: string, lang: string) => Promise<void>;
  logout: () => void;
  setSession: (session:{access_token:string;user:User})=>void;
  can: (page:string)=>boolean;
}

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(() => localStorage.getItem("rg_token"));
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error,setError]=useState<string|null>(null);

  useEffect(() => {
    if (!token) {
      setLoading(false);
      return;
    }
    let active = true;
    setLoading(true);
    setError(null);
    api
      .me(token)
      .then((data) => { if (active) setUser(data); })
      .catch((e) => {
        if (!active) return;
        setUser(null);
        if(e instanceof ApiError&&e.status===401){localStorage.removeItem("rg_token");setToken(null);}
        else setError(e.message);
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
    setError(null);
    localStorage.removeItem("rg_token");
    setToken(null);
    setUser(null);
  }, []);

  const setSession=useCallback((session:{access_token:string;user:User})=>{
    setError(null);
    localStorage.setItem('rg_token',session.access_token);setToken(session.access_token);setUser(session.user);
  },[]);
  const can=useCallback((page:string)=>!!user && (user.is_superuser || (user.permissions||[]).includes(page)),[user]);

  const value = useMemo(
    () => ({ token, user, loading, error, login, register, logout, setSession, can }),
    [token, user, loading, error, login, register, logout, setSession, can]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth outside provider");
  return ctx;
}

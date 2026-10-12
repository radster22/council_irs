import { createContext, createElement, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import { api } from '../api/client';
import type { AuthUser } from '../types';

const STORAGE_KEY = 'council-auth-token';

type AuthContextValue = {
  token: string | null;
  user: AuthUser | null;
  loading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<AuthUser>;
  logout: () => void;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [token, setToken] = useState<string | null>(null);
  const [user, setUser] = useState<AuthUser | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    const storedToken = localStorage.getItem(STORAGE_KEY);
    if (!storedToken) {
      setLoading(false);
      return () => { active = false; };
    }

    api.me(storedToken)
      .then((currentUser) => {
        if (!active) return;
        setToken(storedToken);
        setUser(currentUser);
      })
      .catch(() => {
        if (active) {
          localStorage.removeItem(STORAGE_KEY);
          setToken(null);
          setUser(null);
        }
      })
      .finally(() => { if (active) setLoading(false); });

    return () => { active = false; };
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const response = await api.login(email, password);
    try {
      const currentUser = await api.me(response.access_token);
      localStorage.setItem(STORAGE_KEY, response.access_token);
      setToken(response.access_token);
      setUser(currentUser);
      return currentUser;
    } catch (error) {
      localStorage.removeItem(STORAGE_KEY);
      setToken(null);
      setUser(null);
      throw error;
    }
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem(STORAGE_KEY);
    setToken(null);
    setUser(null);
  }, []);

  const value = useMemo(() => ({
    token,
    user,
    loading,
    isAuthenticated: Boolean(token && user),
    login,
    logout,
  }), [loading, login, logout, token, user]);

  return createElement(AuthContext.Provider, { value }, children);
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used inside AuthProvider.');
  return context;
}

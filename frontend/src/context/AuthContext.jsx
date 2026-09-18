import { createContext, useContext, useEffect, useMemo, useState } from 'react';
import { api } from '../services/api';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem('phc_user') || 'null');
    } catch {
      return null;
    }
  });

  const [token, setToken] = useState(() => localStorage.getItem('phc_token'));

  useEffect(() => {
    const handleUnauthorized = () => {
      setUser(null);
      setToken(null);
      localStorage.removeItem('phc_token');
      localStorage.removeItem('phc_user');
    };

    window.addEventListener('phc:unauthorized', handleUnauthorized);
    return () => window.removeEventListener('phc:unauthorized', handleUnauthorized);
  }, []);

  const value = useMemo(() => ({
    user,
    token,
    isAuthenticated: Boolean(token),

    async login(credentials) {
      const result = await api.login(credentials);
      localStorage.setItem('phc_token', result.token);
      localStorage.setItem('phc_user', JSON.stringify(result.user));
      setToken(result.token);
      setUser(result.user);
      return result;
    },

    async register(credentials) {
      const result = await api.register(credentials);
      localStorage.setItem('phc_token', result.token);
      localStorage.setItem('phc_user', JSON.stringify(result.user));
      setToken(result.token);
      setUser(result.user);
      return result;
    },

    logout() {
      localStorage.removeItem('phc_token');
      localStorage.removeItem('phc_user');
      setToken(null);
      setUser(null);
    },
  }), [token, user]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export const useAuth = () => useContext(AuthContext);

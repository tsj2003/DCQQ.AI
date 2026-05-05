/**
 * Auth context — manages JWT authentication state globally.
 */

import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';
import { authApi } from '../api/client';

interface User {
  id: string;
  email: string;
  name: string | null;
  avatar_url: string | null;
  provider: string;
}

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: () => void;
  guestLogin: () => Promise<void>;
  logout: () => void;
  setToken: (token: string) => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const fetchUser = useCallback(async () => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      setIsLoading(false);
      return;
    }

    try {
      const response = await authApi.getMe();
      setUser(response.data);
    } catch {
      localStorage.removeItem('access_token');
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchUser();
  }, [fetchUser]);

  const login = () => {
    window.location.href = authApi.getGoogleAuthUrl();
  };

  const guestLogin = async () => {
    try {
      const response = await authApi.guestLogin();
      setToken(response.data.access_token);
    } catch (err) {
      console.error('Guest login failed:', err);
    }
  };

  const logout = () => {
    localStorage.removeItem('access_token');
    setUser(null);
  };

  const setToken = (token: string) => {
    localStorage.setItem('access_token', token);
    fetchUser();
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoading,
        isAuthenticated: !!user,
        login,
        guestLogin,
        logout,
        setToken,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

import React, { createContext, useContext, useState, useEffect } from 'react';
import { registerUser, loginUser } from './api';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const storedToken = localStorage.getItem('finae_token');
    const storedUser = localStorage.getItem('finae_user');
    if (storedToken && storedUser) {
      setToken(storedToken);
      setUser(JSON.parse(storedUser));
    }
    setLoading(false);
  }, []);

  const login = async (email, password) => {
    const res = await loginUser(email, password);
    const { token: t, user: u } = res.data;
    localStorage.setItem('finae_token', t);
    localStorage.setItem('finae_user', JSON.stringify(u));
    setToken(t);
    setUser(u);
    return u;
  };

  const register = async (email, password, name) => {
    const res = await registerUser(email, password, name);
    const { token: t, user: u } = res.data;
    localStorage.setItem('finae_token', t);
    localStorage.setItem('finae_user', JSON.stringify(u));
    setToken(t);
    setUser(u);
    return u;
  };

  const logout = () => {
    localStorage.removeItem('finae_token');
    localStorage.removeItem('finae_user');
    setToken(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, token, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}

// src/contexts/AuthContext.js
import React, { createContext, useState, useContext, useEffect } from 'react';
import axios from 'axios';
const AuthContext = createContext(null);
export const AuthProvider = ({ children }) => {
const [user, setUser] = useState(null);
const [loading, setLoading] = useState(true);
useEffect(() => {
checkAuth();
}, []);
const checkAuth = async () => {
  const token = localStorage.getItem('access_token');
  if (token) {
    try {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      // Change this line:
      const response = await axios.get('http://localhost:5000/api/v1/users/me');
      setUser(response.data);
    } catch (error) {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
    }
  }
  setLoading(false);
};


const login = () => {
  window.location.href = 'http://localhost:5000/api/v1/auth/login';
};
const logout = async () => {
  try {
    // Change this line:
    await axios.post('http://localhost:5000/api/v1/auth/logout');
  } catch (error) {
    console.error('Logout error:', error);
  }
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
  setUser(null);
};
return (
<AuthContext.Provider value={{ user, login, logout, loading }}>
{children}
</AuthContext.Provider>
);
};
export const useAuth = () => useContext(AuthContext);
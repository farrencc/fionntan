// src/contexts/AuthContext.js

import React, { createContext, useState, useContext, useEffect } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);
    const navigate = useNavigate();

    useEffect(() => {
        checkAuth();
    }, []);

    const checkAuth = async () => {
        try {
            const token = localStorage.getItem('access_token');
            if (token) {
                axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
                const response = await axios.get('/api/v1/users/me');
                setUser(response.data);
            }
        } catch (error) {
            console.error('Auth check error:', error);
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
        } finally {
            setLoading(false);
        }
    };

    const login = () => {
        // Redirect to backend login route
        window.location.href = '/api/v1/auth/login';
    };

    const handleAuthCallback = async (token) => {
        try {
            localStorage.setItem('access_token', token);
            await checkAuth();
            navigate('/dashboard');
        } catch (error) {
            console.error('Auth callback error:', error);
            navigate('/login');
        }
    };

    const logout = async () => {
        try {
            await axios.post('/api/v1/auth/logout');
        } catch (error) {
            console.error('Logout error:', error);
        }
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        setUser(null);
        navigate('/login');
    };

    return (
        <AuthContext.Provider value={{ 
            user, 
            login, 
            logout, 
            loading,
            handleAuthCallback 
        }}>
            {children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => useContext(AuthContext);
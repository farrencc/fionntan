// src/pages/AuthCallback.js
import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { CircularProgress, Box } from '@mui/material';
import axios from 'axios';

const AuthCallback = () => {
  const navigate = useNavigate();
  const { setUser } = useAuth();

  useEffect(() => {
    const handleCallback = async () => {
      try {
        console.log('AuthCallback: Starting...');
        
        // Get tokens from session with credentials
        const response = await axios.get('http://localhost:5000/api/v1/auth/session/tokens', {
          withCredentials: true  // This is crucial for session cookies
        });
        
        const { access_token, refresh_token } = response.data;
        
        // Store tokens in localStorage
        localStorage.setItem('access_token', access_token);
        localStorage.setItem('refresh_token', refresh_token);
        
        // Set axios default header
        axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
        
        // Get user info
        const userResponse = await axios.get('http://localhost:5000/api/v1/users/me');
        setUser(userResponse.data);
        
        // Redirect to dashboard
        navigate('/dashboard');
      } catch (error) {
        console.error('AuthCallback: Error:', error);
        navigate('/login');
      }
    };

    handleCallback();
  }, [navigate, setUser]);

  return (
    <Box display="flex" justifyContent="center" alignItems="center" minHeight="100vh">
      <CircularProgress />
    </Box>
  );
};

export default AuthCallback;
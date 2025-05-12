// src/pages/AuthError.js
import React from 'react';
import { Box, Typography, Button } from '@mui/material';
import { useNavigate } from 'react-router-dom';

const AuthError = () => {
  const navigate = useNavigate();

  return (
    <Box 
      display="flex" 
      flexDirection="column" 
      alignItems="center" 
      justifyContent="center" 
      minHeight="100vh"
      sx={{ padding: 3 }}
    >
      <Typography variant="h4" gutterBottom color="error">
        Authentication Error
      </Typography>
      <Typography variant="body1" gutterBottom align="center">
        There was an error during sign in. Please try again.
      </Typography>
      <Button 
        variant="contained" 
        onClick={() => navigate('/login')}
        sx={{ mt: 2 }}
      >
        Back to Login
      </Button>
    </Box>
  );
};

export default AuthError;
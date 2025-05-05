// src/pages/Login.js
import React from 'react';
import { Box, Button, Typography, Paper } from '@mui/material';
import { Google as GoogleIcon } from '@mui/icons-material';
import { useAuth } from '../contexts/AuthContext';
const Login = () => {
const { login } = useAuth();
return (
<Box
display="flex"
justifyContent="center"
alignItems="center"
minHeight="100vh"
sx={{ background: 'linear-gradient(45deg, #1976d2 30%, #21cbf3 90%)' }}
>
<Paper elevation={6} sx={{ p: 4, maxWidth: 400, width: '100%', m: 2 }}>
<Typography variant="h4" align="center" gutterBottom>
Fionntán
</Typography>
<Typography variant="subtitle1" align="center" gutterBottom color="textSecondary">
Research Paper Podcast Generator
</Typography>
<Box mt={4}>
<Button
variant="contained"
fullWidth
startIcon={<GoogleIcon />}
onClick={login}
size="large"
sx={{ py: 1.5 }}
>
Sign in with Google
</Button>
</Box>
</Paper>
</Box>
);
};
export default Login;
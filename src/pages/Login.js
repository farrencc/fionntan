// src/pages/Login.js
import React from 'react';
import { Box, Button, Typography, Paper, Container, Divider } from '@mui/material';
import { Google as GoogleIcon, AutoStories, Headset, Speed } from '@mui/icons-material';
import { useAuth } from '../contexts/AuthContext';

const Login = () => {
  const { login } = useAuth();

  const features = [
    {
      icon: <AutoStories sx={{ fontSize: 32 }} />,
      title: 'Academic Excellence',
      description: 'Transform peer-reviewed research into accessible audio',
    },
    {
      icon: <Headset sx={{ fontSize: 32 }} />,
      title: 'Professional Narration',
      description: 'AI-powered voices that bring papers to life',
    },
    {
      icon: <Speed sx={{ fontSize: 32 }} />,
      title: 'Efficient Learning',
      description: 'Stay current with research while multitasking',
    },
  ];

  return (
    <Box
      sx={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        background: (theme) =>
          theme.palette.mode === 'dark'
            ? 'linear-gradient(135deg, #0f1419 0%, #1a2027 50%, #0d2f4e 100%)'
            : 'linear-gradient(135deg, #fafafa 0%, #e8eaf6 50%, #c5cae9 100%)',
      }}
    >
      <Container maxWidth="md">
        <Paper
          elevation={8}
          sx={{
            p: { xs: 3, sm: 5, md: 6 },
            borderRadius: 3,
            textAlign: 'center',
            bgcolor: 'background.paper',
            backdropFilter: 'blur(10px)',
          }}
        >
          {/* Logo / Brand Name */}
          <Box sx={{ mb: 4 }}>
            <Typography
              variant="h2"
              component="h1"
              sx={{
                fontFamily: '"Playfair Display", "Georgia", serif',
                fontWeight: 700,
                background: (theme) =>
                  `linear-gradient(90deg, ${theme.palette.primary.main} 0%, ${theme.palette.secondary.main} 100%)`,
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                backgroundClip: 'text',
                mb: 2,
                fontSize: { xs: '2.5rem', sm: '3rem', md: '3.5rem' },
              }}
            >
              Fionntán
            </Typography>
            <Typography
              variant="h5"
              color="text.primary"
              sx={{
                fontWeight: 400,
                mb: 1,
                fontSize: { xs: '1.1rem', sm: '1.3rem' },
                lineHeight: 1.4,
              }}
            >
              Transform Research Papers into Professional Podcasts
            </Typography>
            <Typography
              variant="body1"
              color="text.secondary"
              sx={{
                maxWidth: 500,
                mx: 'auto',
                lineHeight: 1.7,
              }}
            >
              Stay ahead in your field by listening to the latest research papers,
              converted into engaging audio format by advanced AI technology.
            </Typography>
          </Box>

          {/* Sign In Button */}
          <Box sx={{ my: 4 }}>
            <Button
              variant="contained"
              size="large"
              startIcon={<GoogleIcon />}
              onClick={login}
              sx={{
                py: 1.5,
                px: 4,
                fontSize: '1.1rem',
                borderRadius: 2,
                textTransform: 'none',
                fontWeight: 600,
                boxShadow: 3,
                '&:hover': {
                  boxShadow: 6,
                  transform: 'translateY(-2px)',
                },
                transition: 'all 0.3s ease',
              }}
            >
              Sign in with Google
            </Button>
            <Typography
              variant="caption"
              color="text.secondary"
              display="block"
              sx={{ mt: 2 }}
            >
              Secure authentication powered by Google
            </Typography>
          </Box>

          <Divider sx={{ my: 4 }} />

          {/* Features Grid */}
          <Box
            sx={{
              display: 'grid',
              gridTemplateColumns: { xs: '1fr', sm: 'repeat(3, 1fr)' },
              gap: 3,
              mt: 4,
            }}
          >
            {features.map((feature, index) => (
              <Box
                key={index}
                sx={{
                  textAlign: 'center',
                  p: 2,
                }}
              >
                <Box
                  sx={{
                    color: 'primary.main',
                    mb: 1.5,
                    display: 'flex',
                    justifyContent: 'center',
                  }}
                >
                  {feature.icon}
                </Box>
                <Typography
                  variant="h6"
                  gutterBottom
                  sx={{
                    fontWeight: 600,
                    fontSize: '1rem',
                  }}
                >
                  {feature.title}
                </Typography>
                <Typography
                  variant="body2"
                  color="text.secondary"
                  sx={{ lineHeight: 1.6 }}
                >
                  {feature.description}
                </Typography>
              </Box>
            ))}
          </Box>

          {/* Footer Note */}
          <Box sx={{ mt: 5, pt: 3, borderTop: 1, borderColor: 'divider' }}>
            <Typography variant="caption" color="text.secondary">
              Trusted by researchers and academics worldwide
            </Typography>
          </Box>
        </Paper>
      </Container>
    </Box>
  );
};

export default Login;

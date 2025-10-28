// src/theme/theme.js
import { createTheme } from '@mui/material/styles';

// Scholarly color palette
const scholarlyColors = {
  // Primary - Deep academic blue with gradient capability
  primaryMain: '#1a4d7a',
  primaryLight: '#4a7ba7',
  primaryDark: '#0d2f4e',

  // Accent - Refined gold for highlights
  accentMain: '#b8860b',
  accentLight: '#daa520',
  accentDark: '#8b6508',

  // Semantic colors
  success: '#2e7d32',
  warning: '#ed6c02',
  error: '#d32f2f',
  info: '#0288d1',
};

// Typography - Professional and readable
const typography = {
  fontFamily: '"Crimson Text", "Georgia", "Times New Roman", serif',
  h1: {
    fontFamily: '"Playfair Display", "Georgia", serif',
    fontWeight: 700,
    fontSize: '3rem',
    lineHeight: 1.2,
    letterSpacing: '-0.01em',
  },
  h2: {
    fontFamily: '"Playfair Display", "Georgia", serif',
    fontWeight: 600,
    fontSize: '2.5rem',
    lineHeight: 1.3,
    letterSpacing: '-0.01em',
  },
  h3: {
    fontFamily: '"Playfair Display", "Georgia", serif',
    fontWeight: 600,
    fontSize: '2rem',
    lineHeight: 1.4,
  },
  h4: {
    fontFamily: '"Lato", "Helvetica", "Arial", sans-serif',
    fontWeight: 600,
    fontSize: '1.5rem',
    lineHeight: 1.4,
  },
  h5: {
    fontFamily: '"Lato", "Helvetica", "Arial", sans-serif',
    fontWeight: 600,
    fontSize: '1.25rem',
    lineHeight: 1.5,
  },
  h6: {
    fontFamily: '"Lato", "Helvetica", "Arial", sans-serif',
    fontWeight: 600,
    fontSize: '1rem',
    lineHeight: 1.5,
  },
  body1: {
    fontFamily: '"Lato", "Helvetica", "Arial", sans-serif',
    fontSize: '1rem',
    lineHeight: 1.7,
    letterSpacing: '0.00938em',
  },
  body2: {
    fontFamily: '"Lato", "Helvetica", "Arial", sans-serif',
    fontSize: '0.875rem',
    lineHeight: 1.6,
  },
  button: {
    fontFamily: '"Lato", "Helvetica", "Arial", sans-serif',
    fontWeight: 600,
    textTransform: 'none',
    letterSpacing: '0.02em',
  },
  caption: {
    fontFamily: '"Lato", "Helvetica", "Arial", sans-serif',
    fontSize: '0.75rem',
    lineHeight: 1.5,
    color: 'text.secondary',
  },
  overline: {
    fontFamily: '"Lato", "Helvetica", "Arial", sans-serif',
    fontSize: '0.75rem',
    fontWeight: 600,
    textTransform: 'uppercase',
    letterSpacing: '0.08em',
  },
};

// Light theme
export const lightTheme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: scholarlyColors.primaryMain,
      light: scholarlyColors.primaryLight,
      dark: scholarlyColors.primaryDark,
      contrastText: '#ffffff',
    },
    secondary: {
      main: scholarlyColors.accentMain,
      light: scholarlyColors.accentLight,
      dark: scholarlyColors.accentDark,
      contrastText: '#ffffff',
    },
    success: {
      main: scholarlyColors.success,
    },
    warning: {
      main: scholarlyColors.warning,
    },
    error: {
      main: scholarlyColors.error,
    },
    info: {
      main: scholarlyColors.info,
    },
    background: {
      default: '#fafafa',
      paper: '#ffffff',
    },
    text: {
      primary: '#1a1a1a',
      secondary: '#5a5a5a',
    },
    divider: 'rgba(0, 0, 0, 0.08)',
  },
  typography,
  shape: {
    borderRadius: 8,
  },
  shadows: [
    'none',
    '0px 2px 4px rgba(0, 0, 0, 0.05)',
    '0px 4px 8px rgba(0, 0, 0, 0.08)',
    '0px 8px 16px rgba(0, 0, 0, 0.1)',
    '0px 12px 24px rgba(0, 0, 0, 0.12)',
    '0px 16px 32px rgba(0, 0, 0, 0.14)',
    '0px 20px 40px rgba(0, 0, 0, 0.16)',
    '0px 24px 48px rgba(0, 0, 0, 0.18)',
    '0px 28px 56px rgba(0, 0, 0, 0.2)',
    '0px 32px 64px rgba(0, 0, 0, 0.22)',
    '0px 36px 72px rgba(0, 0, 0, 0.24)',
    '0px 40px 80px rgba(0, 0, 0, 0.26)',
    '0px 44px 88px rgba(0, 0, 0, 0.28)',
    '0px 48px 96px rgba(0, 0, 0, 0.3)',
    '0px 52px 104px rgba(0, 0, 0, 0.32)',
    '0px 56px 112px rgba(0, 0, 0, 0.34)',
    '0px 60px 120px rgba(0, 0, 0, 0.36)',
    '0px 64px 128px rgba(0, 0, 0, 0.38)',
    '0px 68px 136px rgba(0, 0, 0, 0.4)',
    '0px 72px 144px rgba(0, 0, 0, 0.42)',
    '0px 76px 152px rgba(0, 0, 0, 0.44)',
    '0px 80px 160px rgba(0, 0, 0, 0.46)',
    '0px 84px 168px rgba(0, 0, 0, 0.48)',
    '0px 88px 176px rgba(0, 0, 0, 0.5)',
  ],
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          padding: '10px 24px',
          fontSize: '1rem',
          transition: 'all 300ms cubic-bezier(0.4, 0, 0.2, 1)',
          '&:hover': {
            transform: 'translateY(-2px)',
            boxShadow: '0px 8px 16px rgba(0, 0, 0, 0.15)',
          },
        },
        contained: {
          boxShadow: '0px 4px 8px rgba(0, 0, 0, 0.1)',
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 12,
          transition: 'all 300ms cubic-bezier(0.4, 0, 0.2, 1)',
          '&:hover': {
            transform: 'translateY(-4px)',
            boxShadow: '0px 12px 24px rgba(0, 0, 0, 0.15)',
          },
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          transition: 'all 300ms cubic-bezier(0.4, 0, 0.2, 1)',
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: {
          fontWeight: 500,
          borderRadius: 6,
        },
      },
    },
    MuiTab: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          fontSize: '1rem',
          fontWeight: 500,
          minHeight: 48,
        },
      },
    },
  },
});

// Dark theme
export const darkTheme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#5a9fd4',
      light: '#8ec5f0',
      dark: '#3d7ba8',
      contrastText: '#ffffff',
    },
    secondary: {
      main: '#daa520',
      light: '#f4c542',
      dark: '#b8860b',
      contrastText: '#1a1a1a',
    },
    success: {
      main: '#66bb6a',
    },
    warning: {
      main: '#ffa726',
    },
    error: {
      main: '#f44336',
    },
    info: {
      main: '#29b6f6',
    },
    background: {
      default: '#0f1419',
      paper: '#1a2027',
    },
    text: {
      primary: '#e0e0e0',
      secondary: '#a0a0a0',
    },
    divider: 'rgba(255, 255, 255, 0.08)',
  },
  typography,
  shape: {
    borderRadius: 8,
  },
  shadows: [
    'none',
    '0px 2px 4px rgba(0, 0, 0, 0.3)',
    '0px 4px 8px rgba(0, 0, 0, 0.35)',
    '0px 8px 16px rgba(0, 0, 0, 0.4)',
    '0px 12px 24px rgba(0, 0, 0, 0.45)',
    '0px 16px 32px rgba(0, 0, 0, 0.5)',
    '0px 20px 40px rgba(0, 0, 0, 0.55)',
    '0px 24px 48px rgba(0, 0, 0, 0.6)',
    '0px 28px 56px rgba(0, 0, 0, 0.65)',
    '0px 32px 64px rgba(0, 0, 0, 0.7)',
    '0px 36px 72px rgba(0, 0, 0, 0.75)',
    '0px 40px 80px rgba(0, 0, 0, 0.8)',
    '0px 44px 88px rgba(0, 0, 0, 0.85)',
    '0px 48px 96px rgba(0, 0, 0, 0.9)',
    '0px 52px 104px rgba(0, 0, 0, 0.95)',
    '0px 56px 112px rgba(0, 0, 0, 1)',
    '0px 60px 120px rgba(0, 0, 0, 1)',
    '0px 64px 128px rgba(0, 0, 0, 1)',
    '0px 68px 136px rgba(0, 0, 0, 1)',
    '0px 72px 144px rgba(0, 0, 0, 1)',
    '0px 76px 152px rgba(0, 0, 0, 1)',
    '0px 80px 160px rgba(0, 0, 0, 1)',
    '0px 84px 168px rgba(0, 0, 0, 1)',
    '0px 88px 176px rgba(0, 0, 0, 1)',
  ],
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          padding: '10px 24px',
          fontSize: '1rem',
          transition: 'all 300ms cubic-bezier(0.4, 0, 0.2, 1)',
          '&:hover': {
            transform: 'translateY(-2px)',
            boxShadow: '0px 8px 16px rgba(0, 0, 0, 0.4)',
          },
        },
        contained: {
          boxShadow: '0px 4px 8px rgba(0, 0, 0, 0.3)',
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 12,
          transition: 'all 300ms cubic-bezier(0.4, 0, 0.2, 1)',
          '&:hover': {
            transform: 'translateY(-4px)',
            boxShadow: '0px 12px 24px rgba(0, 0, 0, 0.5)',
          },
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          transition: 'all 300ms cubic-bezier(0.4, 0, 0.2, 1)',
          backgroundImage: 'none',
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: {
          fontWeight: 500,
          borderRadius: 6,
        },
      },
    },
    MuiTab: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          fontSize: '1rem',
          fontWeight: 500,
          minHeight: 48,
        },
      },
    },
  },
});

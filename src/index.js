// src/index.js
import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from 'react-query';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import App from './App';
import { AuthProvider } from './contexts/AuthContext';
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
const theme = createTheme({
palette: {
primary: {
main: '#1976d2',
},
secondary: {
main: '#dc004e',
},
},
typography: {
fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
},
});
const queryClient = new QueryClient();
const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
<React.StrictMode>
<BrowserRouter>
<QueryClientProvider client={queryClient}>
<ThemeProvider theme={theme}>
<CssBaseline />
<AuthProvider>
<App />
<ToastContainer position="bottom-center" />
</AuthProvider>
</ThemeProvider>
</QueryClientProvider>
</BrowserRouter>
</React.StrictMode>
);
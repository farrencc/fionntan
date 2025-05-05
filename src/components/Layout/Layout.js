// src/components/Layout/Layout.js
import React from 'react';
import { Outlet } from 'react-router-dom';
import { Box } from '@mui/material';
import Navbar from './Navbar';
import Sidebar from './Sidebar';
const Layout = () => {
const [mobileOpen, setMobileOpen] = React.useState(false);
return (
<Box sx={{ display: 'flex' }}>
<Navbar onMenuClick={() => setMobileOpen(!mobileOpen)} />
<Sidebar mobileOpen={mobileOpen} onMobileClose={() => setMobileOpen(false)} />
<Box
component="main"
sx={{
flexGrow: 1,
p: 3,
width: { sm: `calc(100% - 240px)` },
mt: { xs: 7, sm: 8 },
}}
>
<Outlet />
</Box>
</Box>
);
};
export default Layout;
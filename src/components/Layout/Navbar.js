// src/components/Layout/Navbar.js
import React from 'react';
import { AppBar, Toolbar, IconButton, Typography, Avatar, Menu, MenuItem } from '@mui/material';
import { Menu as MenuIcon, AccountCircle } from '@mui/icons-material';
import { useAuth } from '../../contexts/AuthContext';
const Navbar = ({ onMenuClick }) => {
const { user, logout } = useAuth();
const [anchorEl, setAnchorEl] = React.useState(null);
const handleMenu = (event) => {
setAnchorEl(event.currentTarget);
};
const handleClose = () => {
setAnchorEl(null);
};
return (
<AppBar position="fixed" sx={{ zIndex: (theme) => theme.zIndex.drawer + 1 }}>
<Toolbar>
<IconButton
color="inherit"
edge="start"
onClick={onMenuClick}
sx={{ mr: 2, display: { sm: 'none' } }}
>
<MenuIcon />
</IconButton>
<Typography variant="h6" noWrap component="div" sx={{ flexGrow: 1 }}>
Fionntan
</Typography>
<div>
<IconButton color="inherit" onClick={handleMenu}>
{user?.profile_pic ? (
<Avatar src={user.profile_pic} sx={{ width: 32, height: 32 }} />
) : (
<AccountCircle />
)}
</IconButton>
<Menu
         anchorEl={anchorEl}
         open={Boolean(anchorEl)}
         onClose={handleClose}
       >
<MenuItem disabled>{user?.email}</MenuItem>
<MenuItem onClick={logout}>Logout</MenuItem>
</Menu>
</div>
</Toolbar>
</AppBar>
);
};
export default Navbar;
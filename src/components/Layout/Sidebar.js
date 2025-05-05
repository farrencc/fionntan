// src/components/Layout/Sidebar.js
import React from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import {
Box,
Drawer,
List,
ListItem,
ListItemIcon,
ListItemText,
Toolbar,
useTheme,
useMediaQuery,
} from '@mui/material';
import {
Dashboard as DashboardIcon,
Settings as SettingsIcon,
Podcasts as PodcastsIcon,
Add as AddIcon,
} from '@mui/icons-material';
const drawerWidth = 240;
const menuItems = [
{ text: 'Dashboard', icon: <DashboardIcon />, path: '/dashboard' },
{ text: 'Podcasts', icon: <PodcastsIcon />, path: '/podcasts' },
{ text: 'Create Podcast', icon: <AddIcon />, path: '/create' },
{ text: 'Preferences', icon: <SettingsIcon />, path: '/preferences' },
];
const Sidebar = ({ mobileOpen, onMobileClose }) => {
const theme = useTheme();
const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
const location = useLocation();
const navigate = useNavigate();
const drawer = (
<div>
<Toolbar />
<List>
{menuItems.map((item) => (
<ListItem
button
key={item.text}
selected={location.pathname === item.path}
onClick={() => {
navigate(item.path);
if (isMobile) onMobileClose();
}}
>
<ListItemIcon sx={{ color: location.pathname === item.path ? 'primary.main' : 'inherit' }}>
{item.icon}
</ListItemIcon>
<ListItemText primary={item.text} />
</ListItem>
))}
</List>
</div>
);
return (
<Box
component="nav"
sx={{ width: { sm: drawerWidth }, flexShrink: { sm: 0 } }}
>
{/* Mobile drawer /}
<Drawer
variant="temporary"
open={mobileOpen}
onClose={onMobileClose}
ModalProps={{ keepMounted: true }}
sx={{
display: { xs: 'block', sm: 'none' },
'& .MuiDrawer-paper': { boxSizing: 'border-box', width: drawerWidth },
}}
>
{drawer}
</Drawer>
{/ Desktop drawer */}
<Drawer
variant="permanent"
sx={{
display: { xs: 'none', sm: 'block' },
'& .MuiDrawer-paper': { boxSizing: 'border-box', width: drawerWidth },
}}
open
>
{drawer}
</Drawer>
</Box>
);
};
export default Sidebar;
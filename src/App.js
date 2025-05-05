// src/App.js
import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/Layout/Layout';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Preferences from './pages/Preferences';
import Podcasts from './pages/Podcasts';
import PodcastDetail from './pages/PodcastDetail';
import CreatePodcast from './pages/CreatePodcast';
import PrivateRoute from './components/Auth/PrivateRoute';
function App() {
return (
<Routes>
<Route path="/login" element={<Login />} />
<Route
path="/"
element={
<PrivateRoute>
<Layout />
</PrivateRoute>
}
>
<Route index element={<Navigate to="/dashboard" replace />} />
<Route path="dashboard" element={<Dashboard />} />
<Route path="preferences" element={<Preferences />} />
<Route path="podcasts" element={<Podcasts />} />
<Route path="podcasts/" element={<PodcastDetail />} />
<Route path="create" element={<CreatePodcast />} />
</Route>
</Routes>
);
}
export default App;
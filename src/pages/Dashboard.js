// src/pages/Dashboard.js
import React from 'react';
import { Box, Grid, Paper, Typography, CircularProgress } from '@mui/material';
import { useQuery } from 'react-query';
import axios from 'axios';
import PodcastCard from '../components/Podcast/PodcastCard';
const Dashboard = () => {
const { data: dashboardData, isLoading } = useQuery('dashboard', async () => {
const response = await axios.get('/api/v1/users/dashboard');
return response.data;
});
if (isLoading) {
return (
<Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
<CircularProgress />
</Box>
);
}
return (
<Box>
<Typography variant="h4" gutterBottom>
Dashboard
</Typography>
<Grid container spacing={3}>
    <Grid item xs={12} sm={6} md={3}>
      <Paper sx={{ p: 2 }}>
        <Typography variant="h6">Total Podcasts</Typography>
        <Typography variant="h3">{dashboardData?.stats.total_podcasts || 0}</Typography>
      </Paper>
    </Grid>
    <Grid item xs={12} sm={6} md={3}>
      <Paper sx={{ p: 2 }}>
        <Typography variant="h6">Completed</Typography>
        <Typography variant="h3">{dashboardData?.stats.completed_podcasts || 0}</Typography>
      </Paper>
    </Grid>
    <Grid item xs={12} sm={6} md={3}>
      <Paper sx={{ p: 2 }}>
        <Typography variant="h6">Processing</Typography>
        <Typography variant="h3">{dashboardData?.stats.processing_podcasts || 0}</Typography>
      </Paper>
    </Grid>
    <Grid item xs={12} sm={6} md={3}>
      <Paper sx={{ p: 2 }}>
        <Typography variant="h6">Failed</Typography>
        <Typography variant="h3">{dashboardData?.stats.failed_podcasts || 0}</Typography>
      </Paper>
    </Grid>
  </Grid>

  <Box mt={4}>
    <Typography variant="h5" gutterBottom>
      Recent Podcasts
    </Typography>
    <Grid container spacing={3}>
      {dashboardData?.recent_podcasts?.map((podcast) => (
        <Grid item xs={12} sm={6} md={4} key={podcast.id}>
          <PodcastCard podcast={podcast} />
        </Grid>
      ))}
    </Grid>
  </Box>
</Box>
);
};
export default Dashboard;
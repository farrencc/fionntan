// src/pages/Podcasts.js
import React, { useState } from 'react';
import {
Box,
Typography,
Grid,
CircularProgress,
FormControl,
InputLabel,
Select,
MenuItem,
Pagination,
} from '@mui/material';
import { useQuery } from 'react-query';
import axios from 'axios';
import PodcastCard from '../components/Podcast/PodcastCard';
const Podcasts = () => {
const [page, setPage] = useState(1);
const [status, setStatus] = useState('');
const { data, isLoading } = useQuery(
['podcasts', page, status],
async () => {
const params = {
page,
limit: 9,
};
if (status) params.status = status;
const response = await axios.get('/api/v1/podcasts', { params });
  return response.data;
},
{
  keepPreviousData: true,
}
);
if (isLoading && !data) {
return (
<Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
<CircularProgress />
</Box>
);
}
return (
<Box>
<Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
<Typography variant="h4">
My Podcasts
</Typography>
<FormControl sx={{ minWidth: 200 }}>
<InputLabel>Filter by Status</InputLabel>
<Select
value={status}
label="Filter by Status"
onChange={(e) => {
setStatus(e.target.value);
setPage(1);
}}
>
<MenuItem value="">All</MenuItem>
<MenuItem value="completed">Completed</MenuItem>
<MenuItem value="processing">Processing</MenuItem>
<MenuItem value="failed">Failed</MenuItem>
</Select>
</FormControl>
</Box>
<Grid container spacing={3}>
    {data?.podcasts?.map((podcast) => (
      <Grid item xs={12} sm={6} md={4} key={podcast.id}>
        <PodcastCard podcast={podcast} />
      </Grid>
    ))}
  </Grid>

  {data?.pages > 1 && (
    <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
      <Pagination
        count={data.pages}
        page={page}
        onChange={(e, value) => setPage(value)}
        color="primary"
      />
    </Box>
  )}
</Box>
);
};
export default Podcasts;
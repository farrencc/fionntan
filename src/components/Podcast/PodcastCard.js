// src/components/Podcast/PodcastCard.js
import React from 'react';
import { Card, CardContent, Typography, CardActions, Button, Chip, Box } from '@mui/material';
import { PlayArrow, Download, Settings } from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
const PodcastCard = ({ podcast }) => {
const navigate = useNavigate();
const getStatusColor = (status) => {
switch (status) {
case 'completed':
return 'success';
case 'processing':
return 'primary';
case 'failed':
return 'error';
default:
return 'default';
}
};
return (
<Card>
<CardContent>
<Typography variant="h6" gutterBottom noWrap>
{podcast.title}
</Typography>
<Box mb={2}>
<Chip
         label={podcast.status}
         color={getStatusColor(podcast.status)}
         size="small"
       />
<Chip
label={podcast.technical_level}
size="small"
sx={{ ml: 1 }}
/>
</Box>
<Typography variant="body2" color="textSecondary">
Created: {new Date(podcast.created_at).toLocaleDateString()}
</Typography>
</CardContent>
<CardActions>
<Button
size="small"
startIcon={<PlayArrow />}
onClick={() => navigate(`/podcasts/${podcast.id}`)}
>
View
</Button>
{podcast.status === 'completed' && podcast.audio && (
<Button
size="small"
startIcon={<Download />}
href={`/api/v1/podcasts/${podcast.id}/audio`}
download
>
Download
</Button>
)}
</CardActions>
</Card>
);
};
export default PodcastCard;
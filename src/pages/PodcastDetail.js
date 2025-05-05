// src/pages/PodcastDetail.js
import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import {
Box,
Paper,
Typography,
CircularProgress,
Chip,
Grid,
Button,
Card,
CardContent,
LinearProgress,
} from '@mui/material';
import { useQuery } from 'react-query';
import axios from 'axios';
import AudioPlayer from '../components/Audio/AudioPlayer';
import { Download } from '@mui/icons-material';
const PodcastDetail = () => {
const { id } = useParams();
const { data: podcast, isLoading } = useQuery(['podcast', id], async () => {
const response = await axios.get(`/api/v1/podcasts/${id}`);
return response.data;
});
const { data: taskStatus, isLoading: isTaskLoading } = useQuery(
['task', podcast?.tasks?.[0]?.task_id],
async () => {
if (!podcast?.tasks?.[0]?.task_id) return null;
const response = await axios.get(`/api/v1/tasks/${podcast.tasks[0].task_id}`);
return response.data;
},
{
enabled: !!podcast?.tasks?.[0]?.task_id,
refetchInterval: podcast?.status === 'processing' ? 5000 : false,
}
);
if (isLoading) {
return (
<Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
<CircularProgress />
</Box>
);
}
if (!podcast) {
return <Typography>Podcast not found</Typography>;
}
return (
<Box>
<Paper sx={{ p: 3, mb: 3 }}>
<Typography variant="h4" gutterBottom>
{podcast.title}
</Typography>
<Box mb={2}>
<Chip
label={podcast.status}
color={
podcast.status === 'completed'
? 'success'
: podcast.status === 'processing'
? 'primary'
: 'error'
}
sx={{ mr: 1 }}
/>
<Chip label={podcast.technical_level} sx={{ mr: 1 }} />
<Chip label={`${podcast.target_length} minutes`} />
</Box>
<Typography variant="body1" color="textSecondary">
Created: {new Date(podcast.created_at).toLocaleString()}
</Typography>
</Paper>
{podcast.status === 'processing' && taskStatus && (
    <Paper sx={{ p: 3, mb: 3 }}>
      <Typography variant="h6" gutterBottom>
        Generation Progress
      </Typography>
      <LinearProgress
        variant="determinate"
        value={taskStatus.progress || 0}
        sx={{ height: 10, borderRadius: 5, mb: 2 }}
      />
      <Typography>
        {taskStatus.task_type === 'script_generation' ? 'Generating script...' : 'Creating audio...'}
      </Typography>
    </Paper>
  )}

  {podcast.status === 'completed' && podcast.audio && (
    <Paper sx={{ p: 3, mb: 3 }}>
      <Typography variant="h6" gutterBottom>
        Audio Player
      </Typography>
      <AudioPlayer audioUrl={`/api/v1/podcasts/${id}/audio?stream=true`} />
      <Box mt={2}>
        <Button
          variant="contained"
          startIcon={<Download />}
          href={`/api/v1/podcasts/${id}/audio`}
          download
        >
          Download Podcast
        </Button>
      </Box>
    </Paper>
  )}

  {podcast.script && (
    <Paper sx={{ p: 3 }}>
      <Typography variant="h6" gutterBottom>
        Paper Sources
      </Typography>
      <Grid container spacing={2}>
        {podcast.script.paper_ids?.map((paperId, index) => (
          <Grid item xs={12} sm={6} md={4} key={paperId}>
            <Card variant="outlined">
              <CardContent>
                <Typography variant="subtitle1">
                  Paper {index + 1}
                </Typography>
                <Typography variant="body2" color="textSecondary">
                  arXiv ID: {paperId}
                </Typography>
                <Button
                  size="small"
                  color="primary"
                  href={`https://arxiv.org/abs/${paperId}`}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  View on arXiv
                </Button>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
    </Paper>
  )}
</Box>
);
};
export default PodcastDetail;
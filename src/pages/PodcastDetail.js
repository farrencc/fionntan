// src/pages/PodcastDetail.js
import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Box,
  Container,
  Grid,
  Typography,
  CircularProgress,
  Button,
  IconButton,
  Chip,
  Divider,
  Paper,
} from '@mui/material';
import {
  ArrowBack,
  Share,
  Bookmark,
  BookmarkBorder,
  Download,
  MoreVert,
} from '@mui/icons-material';
import { useQuery } from 'react-query';
import axios from 'axios';
import AudioPlayer from '../components/Audio/AudioPlayer';
import PaperMetadata from '../components/Paper/PaperMetadata';
import GenerationProgress from '../components/Progress/GenerationProgress';

const PodcastDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [isSaved, setIsSaved] = useState(false);

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

  const handleShare = () => {
    if (navigator.share) {
      navigator.share({
        title: podcast?.title,
        text: `Listen to this podcast about: ${podcast?.title}`,
        url: window.location.href,
      });
    }
  };

  const handleDownload = () => {
    window.location.href = `/api/v1/podcasts/${id}/audio`;
  };

  if (isLoading) {
    return (
      <Box
        display="flex"
        justifyContent="center"
        alignItems="center"
        minHeight="80vh"
      >
        <CircularProgress size={60} />
      </Box>
    );
  }

  if (!podcast) {
    return (
      <Container>
        <Box textAlign="center" py={8}>
          <Typography variant="h5" color="text.secondary">
            Podcast not found
          </Typography>
          <Button
            variant="contained"
            onClick={() => navigate('/dashboard')}
            sx={{ mt: 2 }}
          >
            Back to Dashboard
          </Button>
        </Box>
      </Container>
    );
  }

  // Mock paper data - in real app, this would come from the podcast.script.paper_ids
  const paperData = {
    title: podcast.title,
    authors: ['Research Author A', 'Research Author B', 'Research Author C'],
    abstract:
      'This is a sample abstract for the research paper. In a real implementation, this would contain the actual abstract from the arXiv paper. The abstract provides a concise summary of the research objectives, methodology, results, and conclusions.',
    arxivId: podcast.script?.paper_ids?.[0] || '2301.00000',
    arxivUrl: podcast.script?.paper_ids?.[0]
      ? `https://arxiv.org/abs/${podcast.script.paper_ids[0]}`
      : 'https://arxiv.org',
    pdfUrl: podcast.script?.paper_ids?.[0]
      ? `https://arxiv.org/pdf/${podcast.script.paper_ids[0]}.pdf`
      : null,
    publishedDate: podcast.created_at,
    categories: ['Machine Learning', 'Computer Science'],
    journal: 'arXiv preprint',
  };

  // Mock chapter data - in real app, parse from podcast.script
  const chapters = [
    { title: 'Introduction', start: 0 },
    { title: 'Background & Related Work', start: 180 },
    { title: 'Methodology', start: 420 },
    { title: 'Experimental Results', start: 660 },
    { title: 'Discussion', start: 900 },
    { title: 'Conclusion', start: 1080 },
  ];

  return (
    <Box sx={{ bgcolor: 'background.default', minHeight: '100vh', pb: 4 }}>
      <Container maxWidth="xl">
        {/* Header */}
        <Box sx={{ pt: 3, pb: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
            <IconButton onClick={() => navigate('/dashboard')} size="large">
              <ArrowBack />
            </IconButton>
            <Box sx={{ flex: 1 }}>
              <Typography variant="h4" fontWeight={700} gutterBottom>
                {podcast.title}
              </Typography>
              <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', alignItems: 'center' }}>
                <Chip
                  label={podcast.status}
                  color={
                    podcast.status === 'completed'
                      ? 'success'
                      : podcast.status === 'processing'
                      ? 'primary'
                      : 'error'
                  }
                  size="small"
                />
                <Chip label={podcast.technical_level || 'Intermediate'} size="small" variant="outlined" />
                <Chip label={`${podcast.target_length || 15} minutes`} size="small" variant="outlined" />
                <Typography variant="caption" color="text.secondary" sx={{ ml: 1 }}>
                  Created {new Date(podcast.created_at).toLocaleDateString()}
                </Typography>
              </Box>
            </Box>
            <Box sx={{ display: 'flex', gap: 1 }}>
              <IconButton onClick={() => setIsSaved(!isSaved)} color={isSaved ? 'primary' : 'default'}>
                {isSaved ? <Bookmark /> : <BookmarkBorder />}
              </IconButton>
              <IconButton onClick={handleShare}>
                <Share />
              </IconButton>
              <IconButton>
                <MoreVert />
              </IconButton>
            </Box>
          </Box>
        </Box>

        <Divider sx={{ mb: 4 }} />

        {/* Main Content */}
        {podcast.status === 'processing' ? (
          /* Processing State */
          <Box sx={{ maxWidth: 800, mx: 'auto' }}>
            <GenerationProgress
              currentStage={taskStatus?.task_type === 'script_generation' ? 'processing' : 'generation'}
              progress={taskStatus?.progress || 0}
              estimatedTime={taskStatus?.estimated_time || 120}
              compact={false}
            />
          </Box>
        ) : podcast.status === 'completed' && podcast.audio ? (
          /* Completed State - Player and Metadata */
          <Grid container spacing={4}>
            {/* Main Player Area */}
            <Grid item xs={12} lg={8}>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
                {/* Audio Player */}
                <AudioPlayer
                  audioUrl={`/api/v1/podcasts/${id}/audio?stream=true`}
                  chapters={chapters}
                  showChapters={true}
                  autoPlay={false}
                />

                {/* Download Section */}
                <Paper sx={{ p: 3 }}>
                  <Typography variant="h6" gutterBottom fontWeight={600}>
                    Download & Share
                  </Typography>
                  <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
                    <Button
                      variant="contained"
                      startIcon={<Download />}
                      onClick={handleDownload}
                      size="large"
                    >
                      Download Podcast
                    </Button>
                    <Button
                      variant="outlined"
                      startIcon={<Share />}
                      onClick={handleShare}
                      size="large"
                    >
                      Share
                    </Button>
                  </Box>
                  {podcast.audio?.file_size && (
                    <Typography variant="caption" color="text.secondary" sx={{ mt: 2, display: 'block' }}>
                      File size: {(podcast.audio.file_size / (1024 * 1024)).toFixed(2)} MB •{' '}
                      Duration: {Math.floor((podcast.audio.duration || 900) / 60)} minutes
                    </Typography>
                  )}
                </Paper>

                {/* Script Preview (Optional) */}
                {podcast.script?.script_content && (
                  <Paper sx={{ p: 3 }}>
                    <Typography variant="h6" gutterBottom fontWeight={600}>
                      Podcast Script
                    </Typography>
                    <Typography variant="body2" color="text.secondary" paragraph>
                      View the generated conversational script for this podcast
                    </Typography>
                    <Button variant="outlined" size="small">
                      View Full Script
                    </Button>
                  </Paper>
                )}
              </Box>
            </Grid>

            {/* Metadata Sidebar */}
            <Grid item xs={12} lg={4}>
              <Box sx={{ position: { lg: 'sticky' }, top: { lg: 24 } }}>
                <PaperMetadata paper={paperData} />
              </Box>
            </Grid>
          </Grid>
        ) : (
          /* Failed or Other States */
          <Paper sx={{ p: 4, textAlign: 'center' }}>
            <Typography variant="h6" color="error" gutterBottom>
              Podcast generation failed
            </Typography>
            <Typography variant="body2" color="text.secondary" paragraph>
              There was an error generating this podcast. Please try again.
            </Typography>
            <Button variant="contained" onClick={() => navigate('/create')}>
              Generate New Podcast
            </Button>
          </Paper>
        )}
      </Container>
    </Box>
  );
};

export default PodcastDetail;

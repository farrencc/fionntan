// src/pages/Dashboard.js
import React, { useState } from 'react';
import {
  Box,
  Container,
  Tabs,
  Tab,
  Typography,
  Grid,
  Paper,
  Button,
  TextField,
  InputAdornment,
  Chip,
  IconButton,
  CircularProgress,
  Divider,
  Card,
  CardContent,
  LinearProgress,
} from '@mui/material';
import {
  LibraryBooks,
  Explore,
  Add,
  Person,
  Search,
  TrendingUp,
  AccessTime,
  Bookmark,
  Settings,
  Logout,
  DarkMode,
  LightMode,
  Headset,
  Assessment,
} from '@mui/icons-material';
import { useQuery } from 'react-query';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import PodcastCard from '../components/Podcast/PodcastCard';
import GenerationProgress from '../components/Progress/GenerationProgress';
import { useAuth } from '../contexts/AuthContext';
import { useTheme as useCustomTheme } from '../contexts/ThemeContext';

const Dashboard = () => {
  const [currentTab, setCurrentTab] = useState(0);
  const [searchQuery, setSearchQuery] = useState('');
  const [arxivUrl, setArxivUrl] = useState('');
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const { mode, toggleTheme, isDark } = useCustomTheme();

  const { data: dashboardData, isLoading } = useQuery('dashboard', async () => {
    const response = await axios.get('/api/v1/users/dashboard');
    return response.data;
  });

  const { data: podcasts, isLoading: podcastsLoading } = useQuery('podcasts', async () => {
    const response = await axios.get('/api/v1/podcasts');
    return response.data;
  });

  const handleTabChange = (event, newValue) => {
    setCurrentTab(newValue);
  };

  const handleGeneratePodcast = () => {
    navigate('/create');
  };

  // Tab Panel Component
  const TabPanel = ({ children, value, index }) => {
    return (
      <div role="tabpanel" hidden={value !== index}>
        {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
      </div>
    );
  };

  // Library Tab Content
  const LibraryTab = () => {
    const recentPodcasts = podcasts?.podcasts || dashboardData?.recent_podcasts || [];
    const savedPodcasts = recentPodcasts.filter((p) => p.saved);

    return (
      <Box>
        {/* Search Bar */}
        <Box sx={{ mb: 4 }}>
          <TextField
            fullWidth
            placeholder="Search your podcasts..."
            variant="outlined"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <Search />
                </InputAdornment>
              ),
            }}
          />
        </Box>

        {/* Recently Generated Podcasts Section */}
        <Box sx={{ mb: 5 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
            <Typography variant="h5" fontWeight={600}>
              Recently Generated Podcasts
            </Typography>
            <Button
              variant="contained"
              startIcon={<Add />}
              onClick={handleGeneratePodcast}
              sx={{ textTransform: 'none' }}
            >
              Generate New
            </Button>
          </Box>

          {podcastsLoading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
              <CircularProgress />
            </Box>
          ) : recentPodcasts.length === 0 ? (
            <Paper sx={{ p: 4, textAlign: 'center' }}>
              <Typography variant="h6" color="text.secondary" gutterBottom>
                No podcasts yet
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                Generate your first podcast from a research paper
              </Typography>
              <Button variant="contained" onClick={handleGeneratePodcast}>
                Get Started
              </Button>
            </Paper>
          ) : (
            <Grid container spacing={3}>
              {recentPodcasts.slice(0, 6).map((podcast) => (
                <Grid item xs={12} sm={6} md={4} key={podcast.id}>
                  <PodcastCard
                    id={podcast.id}
                    paperTitle={podcast.title}
                    authors={podcast.authors || []}
                    duration={podcast.duration || 900}
                    playCount={podcast.play_count || 0}
                    category={podcast.category || 'Research'}
                    status={podcast.status}
                    qualityIndicator="high"
                    createdAt={podcast.created_at}
                  />
                </Grid>
              ))}
            </Grid>
          )}
        </Box>

        {/* Saved Podcasts Section */}
        {savedPodcasts.length > 0 && (
          <Box sx={{ mb: 5 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 3 }}>
              <Bookmark color="primary" />
              <Typography variant="h5" fontWeight={600}>
                Your Saved Podcasts
              </Typography>
            </Box>
            <Grid container spacing={3}>
              {savedPodcasts.map((podcast) => (
                <Grid item xs={12} sm={6} md={4} key={podcast.id}>
                  <PodcastCard
                    id={podcast.id}
                    paperTitle={podcast.title}
                    authors={podcast.authors || []}
                    duration={podcast.duration || 900}
                    playCount={podcast.play_count || 0}
                    category={podcast.category || 'Research'}
                    status={podcast.status}
                    qualityIndicator="high"
                  />
                </Grid>
              ))}
            </Grid>
          </Box>
        )}

        {/* Trending Section */}
        <Box>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 3 }}>
            <TrendingUp color="primary" />
            <Typography variant="h5" fontWeight={600}>
              Trending in Your Field
            </Typography>
          </Box>
          <Grid container spacing={3}>
            {[...Array(3)].map((_, index) => (
              <Grid item xs={12} sm={6} md={4} key={index}>
                <PodcastCard
                  id={`trending-${index}`}
                  paperTitle="Sample Trending Paper Title"
                  authors={['Author A', 'Author B']}
                  duration={1200}
                  playCount={Math.floor(Math.random() * 10000) + 1000}
                  category="ML"
                  status="completed"
                  qualityIndicator="high"
                  isLoading={false}
                />
              </Grid>
            ))}
          </Grid>
        </Box>
      </Box>
    );
  };

  // Discover Tab Content
  const DiscoverTab = () => {
    const categories = ['Machine Learning', 'Physics', 'Biology', 'Computer Science', 'Mathematics', 'Chemistry'];

    return (
      <Box>
        <Typography variant="h5" fontWeight={600} gutterBottom>
          Discover Research Podcasts
        </Typography>
        <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
          Explore podcasts across different academic fields
        </Typography>

        {/* Category Filter */}
        <Box sx={{ mb: 4, display: 'flex', flexWrap: 'wrap', gap: 1 }}>
          <Chip label="All" color="primary" onClick={() => {}} />
          {categories.map((cat) => (
            <Chip key={cat} label={cat} variant="outlined" onClick={() => {}} />
          ))}
        </Box>

        {/* Featured Podcasts */}
        <Grid container spacing={3}>
          {[...Array(9)].map((_, index) => (
            <Grid item xs={12} sm={6} md={4} key={index}>
              <PodcastCard
                id={`discover-${index}`}
                paperTitle="Featured Research Paper Title"
                authors={['Researcher A', 'Researcher B', 'Researcher C']}
                duration={Math.floor(Math.random() * 1200) + 600}
                playCount={Math.floor(Math.random() * 5000) + 500}
                category={categories[index % categories.length]}
                status="completed"
                qualityIndicator="high"
              />
            </Grid>
          ))}
        </Grid>
      </Box>
    );
  };

  // Generate Tab Content
  const GenerateTab = () => {
    return (
      <Box>
        <Typography variant="h5" fontWeight={600} gutterBottom>
          Generate New Podcast
        </Typography>
        <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
          Convert a research paper from arXiv into an audio podcast
        </Typography>

        <Grid container spacing={4}>
          {/* Input Section */}
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
                Paper Source
              </Typography>
              <TextField
                fullWidth
                label="arXiv URL or ID"
                placeholder="https://arxiv.org/abs/2301.xxxxx or 2301.xxxxx"
                variant="outlined"
                value={arxivUrl}
                onChange={(e) => setArxivUrl(e.target.value)}
                sx={{ mb: 2 }}
              />
              <Button
                variant="contained"
                fullWidth
                size="large"
                onClick={handleGeneratePodcast}
                sx={{ textTransform: 'none' }}
              >
                Generate Podcast
              </Button>

              <Divider sx={{ my: 3 }} />

              <Typography variant="body2" color="text.secondary" gutterBottom>
                Or browse by preferences
              </Typography>
              <Button
                variant="outlined"
                fullWidth
                onClick={() => navigate('/preferences')}
                sx={{ textTransform: 'none' }}
              >
                Configure Preferences
              </Button>
            </Paper>
          </Grid>

          {/* Processing Queue Section */}
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
                Processing Queue
              </Typography>
              {podcastsLoading ? (
                <CircularProgress />
              ) : (
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                  {(podcasts?.podcasts || [])
                    .filter((p) => p.status === 'processing' || p.status === 'pending')
                    .slice(0, 3)
                    .map((podcast) => (
                      <GenerationProgress
                        key={podcast.id}
                        currentStage="processing"
                        progress={50}
                        estimatedTime={120}
                        compact={true}
                      />
                    ))}
                  {(podcasts?.podcasts || []).filter(
                    (p) => p.status === 'processing' || p.status === 'pending'
                  ).length === 0 && (
                    <Typography variant="body2" color="text.secondary" sx={{ textAlign: 'center', py: 2 }}>
                      No podcasts currently processing
                    </Typography>
                  )}
                </Box>
              )}
            </Paper>
          </Grid>
        </Grid>

        {/* Recent Generations */}
        <Box sx={{ mt: 4 }}>
          <Typography variant="h6" gutterBottom>
            Recent Generations
          </Typography>
          <Grid container spacing={2}>
            {(podcasts?.podcasts || []).slice(0, 3).map((podcast) => (
              <Grid item xs={12} key={podcast.id}>
                <Card variant="outlined">
                  <CardContent sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Box>
                      <Typography variant="subtitle1" fontWeight={600}>
                        {podcast.title}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {new Date(podcast.created_at).toLocaleString()}
                      </Typography>
                    </Box>
                    <Chip
                      label={podcast.status}
                      color={podcast.status === 'completed' ? 'success' : 'default'}
                      size="small"
                    />
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        </Box>
      </Box>
    );
  };

  // Profile Tab Content
  const ProfileTab = () => {
    const stats = dashboardData?.stats || {};

    return (
      <Box>
        <Grid container spacing={4}>
          {/* User Info */}
          <Grid item xs={12} md={4}>
            <Paper sx={{ p: 3, textAlign: 'center' }}>
              <Box
                sx={{
                  width: 100,
                  height: 100,
                  borderRadius: '50%',
                  bgcolor: 'primary.main',
                  color: 'white',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '2.5rem',
                  fontWeight: 600,
                  mx: 'auto',
                  mb: 2,
                }}
              >
                {user?.name?.charAt(0) || 'U'}
              </Box>
              <Typography variant="h6" gutterBottom>
                {user?.name || 'User'}
              </Typography>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                {user?.email || 'user@example.com'}
              </Typography>
              <Chip label="Free Plan" size="small" sx={{ mt: 1 }} />
            </Paper>
          </Grid>

          {/* Usage Statistics */}
          <Grid item xs={12} md={8}>
            <Paper sx={{ p: 3 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 3 }}>
                <Assessment color="primary" />
                <Typography variant="h6" fontWeight={600}>
                  Usage Statistics
                </Typography>
              </Box>

              <Grid container spacing={3}>
                <Grid item xs={6} sm={3}>
                  <Box sx={{ textAlign: 'center' }}>
                    <Typography variant="h3" color="primary" fontWeight={600}>
                      {stats.total_podcasts || 0}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Podcasts Generated
                    </Typography>
                  </Box>
                </Grid>
                <Grid item xs={6} sm={3}>
                  <Box sx={{ textAlign: 'center' }}>
                    <Typography variant="h3" color="success.main" fontWeight={600}>
                      {Math.floor((stats.total_podcasts || 0) * 15 / 60)}h
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Hours Listened
                    </Typography>
                  </Box>
                </Grid>
                <Grid item xs={6} sm={3}>
                  <Box sx={{ textAlign: 'center' }}>
                    <Typography variant="h3" color="secondary.main" fontWeight={600}>
                      {stats.completed_podcasts || 0}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Completed
                    </Typography>
                  </Box>
                </Grid>
                <Grid item xs={6} sm={3}>
                  <Box sx={{ textAlign: 'center' }}>
                    <Typography variant="h3" color="info.main" fontWeight={600}>
                      {stats.processing_podcasts || 0}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      In Progress
                    </Typography>
                  </Box>
                </Grid>
              </Grid>
            </Paper>
          </Grid>

          {/* Settings */}
          <Grid item xs={12}>
            <Paper sx={{ p: 3 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 3 }}>
                <Settings color="primary" />
                <Typography variant="h6" fontWeight={600}>
                  Settings
                </Typography>
              </Box>

              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                {/* Theme Toggle */}
                <Box
                  sx={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    p: 2,
                    border: 1,
                    borderColor: 'divider',
                    borderRadius: 2,
                  }}
                >
                  <Box>
                    <Typography variant="subtitle1" fontWeight={600}>
                      Theme
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Switch between light and dark mode
                    </Typography>
                  </Box>
                  <IconButton onClick={toggleTheme} color="primary">
                    {isDark ? <LightMode /> : <DarkMode />}
                  </IconButton>
                </Box>

                {/* Preferences Link */}
                <Box
                  sx={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    p: 2,
                    border: 1,
                    borderColor: 'divider',
                    borderRadius: 2,
                  }}
                >
                  <Box>
                    <Typography variant="subtitle1" fontWeight={600}>
                      Research Preferences
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Configure your research interests and topics
                    </Typography>
                  </Box>
                  <Button variant="outlined" onClick={() => navigate('/preferences')}>
                    Configure
                  </Button>
                </Box>

                {/* Logout */}
                <Box
                  sx={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    p: 2,
                    border: 1,
                    borderColor: 'divider',
                    borderRadius: 2,
                  }}
                >
                  <Box>
                    <Typography variant="subtitle1" fontWeight={600}>
                      Sign Out
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Log out of your account
                    </Typography>
                  </Box>
                  <Button
                    variant="outlined"
                    color="error"
                    startIcon={<Logout />}
                    onClick={logout}
                  >
                    Logout
                  </Button>
                </Box>
              </Box>
            </Paper>
          </Grid>
        </Grid>
      </Box>
    );
  };

  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" fontWeight={700} gutterBottom>
          Dashboard
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Welcome back, {user?.name || 'User'}
        </Typography>
      </Box>

      {/* Tabs */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs
          value={currentTab}
          onChange={handleTabChange}
          variant="scrollable"
          scrollButtons="auto"
          sx={{
            '& .MuiTab-root': {
              minHeight: 60,
              textTransform: 'none',
              fontSize: '1rem',
              fontWeight: 500,
            },
          }}
        >
          <Tab icon={<LibraryBooks />} iconPosition="start" label="Library" />
          <Tab icon={<Explore />} iconPosition="start" label="Discover" />
          <Tab icon={<Add />} iconPosition="start" label="Generate" />
          <Tab icon={<Person />} iconPosition="start" label="Profile" />
        </Tabs>
      </Box>

      {/* Tab Panels */}
      <TabPanel value={currentTab} index={0}>
        <LibraryTab />
      </TabPanel>
      <TabPanel value={currentTab} index={1}>
        <DiscoverTab />
      </TabPanel>
      <TabPanel value={currentTab} index={2}>
        <GenerateTab />
      </TabPanel>
      <TabPanel value={currentTab} index={3}>
        <ProfileTab />
      </TabPanel>
    </Container>
  );
};

export default Dashboard;

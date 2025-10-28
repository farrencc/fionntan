// src/components/Podcast/PodcastCard.js
import React, { useState } from 'react';
import {
  Card,
  CardContent,
  CardActions,
  Typography,
  Box,
  IconButton,
  Chip,
  LinearProgress,
  Skeleton,
} from '@mui/material';
import {
  PlayArrow,
  Pause,
  Visibility,
  Bookmark,
  BookmarkBorder,
  Share,
  MoreVert,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';

const PodcastCard = ({
  id,
  paperTitle,
  authors = [],
  venue,
  duration,
  playCount = 0,
  category,
  status = 'completed',
  qualityIndicator = 'high',
  isPlaying = false,
  onPlayPause,
  isLoading = false,
  createdAt,
  waveformData,
}) => {
  const navigate = useNavigate();
  const [isSaved, setIsSaved] = useState(false);
  const [isHovered, setIsHovered] = useState(false);

  const handleCardClick = (e) => {
    // Don't navigate if clicking on action buttons
    if (e.target.closest('.card-actions')) return;
    navigate(`/podcasts/${id}`);
  };

  const handlePlayPause = (e) => {
    e.stopPropagation();
    if (onPlayPause) {
      onPlayPause(id);
    }
  };

  const handleSaveToggle = (e) => {
    e.stopPropagation();
    setIsSaved(!isSaved);
  };

  const handleShare = (e) => {
    e.stopPropagation();
    // Share functionality
    if (navigator.share) {
      navigator.share({
        title: paperTitle,
        text: `Listen to this podcast about: ${paperTitle}`,
        url: window.location.origin + `/podcasts/${id}`,
      });
    }
  };

  const formatDuration = (seconds) => {
    if (!seconds) return '0:00';
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const getQualityColor = () => {
    switch (qualityIndicator) {
      case 'high':
        return 'success';
      case 'medium':
        return 'warning';
      case 'low':
        return 'error';
      default:
        return 'default';
    }
  };

  const truncateAuthors = (authorsList) => {
    if (!authorsList || authorsList.length === 0) return 'Unknown Author';
    if (authorsList.length === 1) return authorsList[0];
    if (authorsList.length === 2) return authorsList.join(' & ');
    return `${authorsList[0]} et al.`;
  };

  if (isLoading) {
    return (
      <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
        <CardContent sx={{ flexGrow: 1 }}>
          <Skeleton variant="text" width="60%" height={32} />
          <Skeleton variant="text" width="80%" />
          <Skeleton variant="rectangular" height={60} sx={{ mt: 2, mb: 2 }} />
          <Skeleton variant="text" width="40%" />
        </CardContent>
      </Card>
    );
  }

  return (
    <Card
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      onClick={handleCardClick}
      sx={{
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        cursor: 'pointer',
        position: 'relative',
        border: (theme) =>
          isPlaying ? `2px solid ${theme.palette.primary.main}` : 'none',
        transition: 'all 300ms cubic-bezier(0.4, 0, 0.2, 1)',
        '&:hover': {
          transform: 'translateY(-4px)',
          boxShadow: (theme) =>
            theme.palette.mode === 'dark'
              ? '0px 12px 24px rgba(0, 0, 0, 0.5)'
              : '0px 12px 24px rgba(0, 0, 0, 0.15)',
        },
      }}
    >
      {status === 'processing' && (
        <LinearProgress
          sx={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            borderTopLeftRadius: 12,
            borderTopRightRadius: 12,
          }}
        />
      )}

      <CardContent sx={{ flexGrow: 1, pb: 1 }}>
        {/* Category and Quality Indicator */}
        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1.5 }}>
          {category && (
            <Chip
              label={category}
              size="small"
              sx={{
                fontWeight: 600,
                fontSize: '0.75rem',
                textTransform: 'uppercase',
                letterSpacing: '0.05em',
              }}
            />
          )}
          <Chip
            label={qualityIndicator}
            size="small"
            color={getQualityColor()}
            sx={{ ml: 'auto', fontWeight: 600, textTransform: 'capitalize' }}
          />
        </Box>

        {/* Paper Title */}
        <Typography
          variant="h6"
          component="h3"
          gutterBottom
          sx={{
            fontWeight: 600,
            fontSize: '1.1rem',
            lineHeight: 1.3,
            display: '-webkit-box',
            WebkitLineClamp: 2,
            WebkitBoxOrient: 'vertical',
            overflow: 'hidden',
            mb: 1,
          }}
        >
          {paperTitle}
        </Typography>

        {/* Authors */}
        <Typography
          variant="body2"
          color="text.secondary"
          sx={{
            mb: 1.5,
            fontSize: '0.875rem',
            fontStyle: 'italic',
          }}
        >
          {truncateAuthors(authors)}
        </Typography>

        {/* Waveform Visualization */}
        <Box
          sx={{
            height: 60,
            bgcolor: (theme) =>
              theme.palette.mode === 'dark' ? 'rgba(255,255,255,0.03)' : 'rgba(0,0,0,0.02)',
            borderRadius: 1,
            mb: 1.5,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            position: 'relative',
            overflow: 'hidden',
          }}
        >
          {/* Simple waveform visualization */}
          <Box
            sx={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '2px',
              height: '100%',
              width: '100%',
              px: 2,
            }}
          >
            {Array.from({ length: 40 }).map((_, i) => (
              <Box
                key={i}
                sx={{
                  flex: 1,
                  height: `${Math.random() * 60 + 20}%`,
                  bgcolor: (theme) =>
                    isPlaying
                      ? theme.palette.primary.main
                      : theme.palette.mode === 'dark'
                      ? 'rgba(255,255,255,0.2)'
                      : 'rgba(0,0,0,0.2)',
                  borderRadius: '2px',
                  transition: 'all 0.3s ease',
                  opacity: isPlaying && i < 20 ? 0.5 + Math.random() * 0.5 : 1,
                }}
              />
            ))}
          </Box>

          {/* Large Play Button Overlay */}
          <Box
            sx={{
              position: 'absolute',
              top: '50%',
              left: '50%',
              transform: 'translate(-50%, -50%)',
              opacity: isHovered || isPlaying ? 1 : 0.7,
              transition: 'all 0.3s ease',
            }}
          >
            <IconButton
              onClick={handlePlayPause}
              sx={{
                bgcolor: (theme) => theme.palette.primary.main,
                color: 'white',
                width: 48,
                height: 48,
                '&:hover': {
                  bgcolor: (theme) => theme.palette.primary.dark,
                  transform: 'scale(1.1)',
                },
                boxShadow: 3,
                transition: 'all 0.3s ease',
                animation: isPlaying ? 'pulse 2s infinite' : 'none',
                '@keyframes pulse': {
                  '0%, 100%': {
                    boxShadow: '0 0 0 0 rgba(26, 77, 122, 0.7)',
                  },
                  '50%': {
                    boxShadow: '0 0 0 10px rgba(26, 77, 122, 0)',
                  },
                },
              }}
            >
              {isPlaying ? <Pause /> : <PlayArrow />}
            </IconButton>
          </Box>
        </Box>

        {/* Metadata */}
        <Box
          sx={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}
        >
          <Typography variant="caption" color="text.secondary">
            {formatDuration(duration)}
          </Typography>
          {playCount > 0 && (
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
              <Visibility sx={{ fontSize: 16 }} />
              <Typography variant="caption" color="text.secondary">
                {playCount >= 1000
                  ? `${(playCount / 1000).toFixed(1)}K`
                  : playCount}{' '}
                plays
              </Typography>
            </Box>
          )}
        </Box>

        {venue && (
          <Typography
            variant="caption"
            color="text.secondary"
            sx={{
              display: 'block',
              mt: 0.5,
              fontWeight: 500,
            }}
          >
            {venue}
          </Typography>
        )}
      </CardContent>

      {/* Actions */}
      <CardActions className="card-actions" sx={{ px: 2, pb: 2, pt: 0 }}>
        <IconButton
          size="small"
          onClick={handleSaveToggle}
          sx={{ color: isSaved ? 'primary.main' : 'text.secondary' }}
        >
          {isSaved ? <Bookmark /> : <BookmarkBorder />}
        </IconButton>
        <IconButton size="small" onClick={handleShare} sx={{ color: 'text.secondary' }}>
          <Share />
        </IconButton>
        <IconButton size="small" sx={{ ml: 'auto', color: 'text.secondary' }}>
          <MoreVert />
        </IconButton>
      </CardActions>
    </Card>
  );
};

export default PodcastCard;

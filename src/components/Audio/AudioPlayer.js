// src/components/Audio/AudioPlayer.js
import React, { useState, useRef, useEffect } from 'react';
import {
  Box,
  IconButton,
  Typography,
  Slider,
  Paper,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Chip,
  Tooltip,
  LinearProgress,
} from '@mui/material';
import {
  PlayArrow,
  Pause,
  FastForward,
  FastRewind,
  VolumeUp,
  VolumeOff,
  SkipNext,
  SkipPrevious,
} from '@mui/icons-material';
import WaveSurfer from 'wavesurfer.js';
import { useTheme as useMuiTheme } from '@mui/material/styles';

const AudioPlayer = ({
  audioUrl,
  chapters = [],
  onChapterChange,
  autoPlay = false,
  showChapters = true,
}) => {
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [volume, setVolume] = useState(0.7);
  const [playbackRate, setPlaybackRate] = useState(1);
  const [currentChapter, setCurrentChapter] = useState(0);
  const [isLoading, setIsLoading] = useState(true);

  const waveformRef = useRef(null);
  const wavesurfer = useRef(null);
  const theme = useMuiTheme();

  // Default chapters based on typical paper structure
  const defaultChapters = [
    { title: 'Introduction', start: 0 },
    { title: 'Background', start: duration * 0.15 },
    { title: 'Methods', start: duration * 0.35 },
    { title: 'Results', start: duration * 0.55 },
    { title: 'Discussion', start: duration * 0.75 },
    { title: 'Conclusion', start: duration * 0.9 },
  ];

  const activeChapters = chapters.length > 0 ? chapters : defaultChapters;

  useEffect(() => {
    if (!waveformRef.current) return;

    const options = {
      container: waveformRef.current,
      waveColor: theme.palette.mode === 'dark'
        ? 'rgba(255, 255, 255, 0.3)'
        : 'rgba(0, 0, 0, 0.3)',
      progressColor: theme.palette.primary.main,
      cursorColor: theme.palette.secondary.main,
      barWidth: 3,
      barRadius: 3,
      barGap: 2,
      responsive: true,
      height: 120,
      normalize: true,
      backend: 'WebAudio',
    };

    wavesurfer.current = WaveSurfer.create(options);
    wavesurfer.current.load(audioUrl);

    wavesurfer.current.on('ready', () => {
      setDuration(wavesurfer.current.getDuration());
      setIsLoading(false);
      if (autoPlay) {
        wavesurfer.current.play();
        setIsPlaying(true);
      }
    });

    wavesurfer.current.on('audioprocess', () => {
      const time = wavesurfer.current.getCurrentTime();
      setCurrentTime(time);
      updateCurrentChapter(time);
    });

    wavesurfer.current.on('finish', () => {
      setIsPlaying(false);
    });

    wavesurfer.current.on('error', (e) => {
      console.error('WaveSurfer error:', e);
      setIsLoading(false);
    });

    return () => {
      if (wavesurfer.current) {
        wavesurfer.current.destroy();
      }
    };
  }, [audioUrl]);

  // Update waveform colors when theme changes
  useEffect(() => {
    if (wavesurfer.current) {
      wavesurfer.current.setWaveColor(
        theme.palette.mode === 'dark'
          ? 'rgba(255, 255, 255, 0.3)'
          : 'rgba(0, 0, 0, 0.3)'
      );
      wavesurfer.current.setProgressColor(theme.palette.primary.main);
      wavesurfer.current.setCursorColor(theme.palette.secondary.main);
    }
  }, [theme.palette.mode]);

  const updateCurrentChapter = (time) => {
    const chapterIndex = activeChapters.findIndex((chapter, index) => {
      const nextChapter = activeChapters[index + 1];
      return time >= chapter.start && (!nextChapter || time < nextChapter.start);
    });
    if (chapterIndex !== -1 && chapterIndex !== currentChapter) {
      setCurrentChapter(chapterIndex);
      if (onChapterChange) {
        onChapterChange(activeChapters[chapterIndex]);
      }
    }
  };

  const handlePlayPause = () => {
    if (wavesurfer.current) {
      wavesurfer.current.playPause();
      setIsPlaying(!isPlaying);
    }
  };

  const handleSkipForward = () => {
    if (wavesurfer.current) {
      wavesurfer.current.skip(15);
    }
  };

  const handleSkipBackward = () => {
    if (wavesurfer.current) {
      wavesurfer.current.skip(-15);
    }
  };

  const handleNextChapter = () => {
    if (currentChapter < activeChapters.length - 1) {
      const nextChapter = activeChapters[currentChapter + 1];
      seekToTime(nextChapter.start);
    }
  };

  const handlePreviousChapter = () => {
    if (currentChapter > 0) {
      const prevChapter = activeChapters[currentChapter - 1];
      seekToTime(prevChapter.start);
    }
  };

  const seekToTime = (time) => {
    if (wavesurfer.current && duration > 0) {
      wavesurfer.current.seekTo(time / duration);
      setCurrentTime(time);
    }
  };

  const handleVolumeChange = (event, newValue) => {
    setVolume(newValue);
    if (wavesurfer.current) {
      wavesurfer.current.setVolume(newValue);
    }
  };

  const handlePlaybackRateChange = (event) => {
    const rate = event.target.value;
    setPlaybackRate(rate);
    if (wavesurfer.current) {
      wavesurfer.current.setPlaybackRate(rate);
    }
  };

  const formatTime = (time) => {
    if (!time || isNaN(time)) return '0:00';
    const hours = Math.floor(time / 3600);
    const minutes = Math.floor((time % 3600) / 60);
    const seconds = Math.floor(time % 60);

    if (hours > 0) {
      return `${hours}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
    }
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
  };

  return (
    <Paper
      elevation={3}
      sx={{
        p: 3,
        borderRadius: 3,
        bgcolor: theme.palette.mode === 'dark' ? 'background.paper' : 'background.default',
      }}
    >
      {/* Waveform */}
      <Box sx={{ position: 'relative', mb: 3 }}>
        {isLoading && (
          <Box sx={{ position: 'absolute', top: 0, left: 0, right: 0 }}>
            <LinearProgress />
          </Box>
        )}
        <Box ref={waveformRef} />
      </Box>

      {/* Chapter Markers */}
      {showChapters && activeChapters.length > 0 && (
        <Box sx={{ mb: 3, display: 'flex', gap: 1, flexWrap: 'wrap' }}>
          {activeChapters.map((chapter, index) => (
            <Chip
              key={index}
              label={chapter.title}
              size="small"
              onClick={() => seekToTime(chapter.start)}
              color={index === currentChapter ? 'primary' : 'default'}
              variant={index === currentChapter ? 'filled' : 'outlined'}
              sx={{
                cursor: 'pointer',
                fontWeight: index === currentChapter ? 600 : 400,
                transition: 'all 0.3s ease',
                '&:hover': {
                  transform: 'translateY(-2px)',
                },
              }}
            />
          ))}
        </Box>
      )}

      {/* Main Controls */}
      <Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          mb: 2,
          gap: 1,
        }}
      >
        <Tooltip title="Previous Chapter">
          <span>
            <IconButton
              onClick={handlePreviousChapter}
              disabled={currentChapter === 0}
              size="large"
            >
              <SkipPrevious fontSize="large" />
            </IconButton>
          </span>
        </Tooltip>

        <Tooltip title="Rewind 15s">
          <IconButton onClick={handleSkipBackward} size="large">
            <FastRewind fontSize="large" />
          </IconButton>
        </Tooltip>

        <IconButton
          onClick={handlePlayPause}
          disabled={isLoading}
          sx={{
            bgcolor: 'primary.main',
            color: 'white',
            width: 64,
            height: 64,
            '&:hover': {
              bgcolor: 'primary.dark',
              transform: 'scale(1.05)',
            },
            '&:disabled': {
              bgcolor: 'action.disabledBackground',
            },
            transition: 'all 0.3s ease',
          }}
        >
          {isPlaying ? <Pause fontSize="large" /> : <PlayArrow fontSize="large" />}
        </IconButton>

        <Tooltip title="Forward 15s">
          <IconButton onClick={handleSkipForward} size="large">
            <FastForward fontSize="large" />
          </IconButton>
        </Tooltip>

        <Tooltip title="Next Chapter">
          <span>
            <IconButton
              onClick={handleNextChapter}
              disabled={currentChapter === activeChapters.length - 1}
              size="large"
            >
              <SkipNext fontSize="large" />
            </IconButton>
          </span>
        </Tooltip>
      </Box>

      {/* Progress Bar */}
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
        <Typography
          variant="body2"
          sx={{
            minWidth: '60px',
            fontFamily: 'monospace',
            fontWeight: 600,
          }}
        >
          {formatTime(currentTime)}
        </Typography>
        <Slider
          value={currentTime}
          max={duration || 100}
          onChange={(e, newValue) => {
            seekToTime(newValue);
          }}
          aria-labelledby="time-slider"
          sx={{
            flexGrow: 1,
            '& .MuiSlider-thumb': {
              width: 16,
              height: 16,
            },
          }}
          disabled={isLoading}
        />
        <Typography
          variant="body2"
          sx={{
            minWidth: '60px',
            fontFamily: 'monospace',
            fontWeight: 600,
          }}
        >
          {formatTime(duration)}
        </Typography>
      </Box>

      {/* Volume and Playback Rate */}
      <Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: 2,
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', minWidth: 200, flex: 1 }}>
          <IconButton
            onClick={() => handleVolumeChange(null, volume > 0 ? 0 : 0.7)}
            size="small"
          >
            {volume > 0 ? <VolumeUp /> : <VolumeOff />}
          </IconButton>
          <Slider
            value={volume}
            onChange={handleVolumeChange}
            aria-labelledby="volume-slider"
            step={0.01}
            min={0}
            max={1}
            sx={{ ml: 1 }}
          />
        </Box>

        <FormControl size="small" sx={{ minWidth: 120 }}>
          <InputLabel>Speed</InputLabel>
          <Select
            value={playbackRate}
            label="Speed"
            onChange={handlePlaybackRateChange}
          >
            <MenuItem value={0.5}>0.5x</MenuItem>
            <MenuItem value={0.75}>0.75x</MenuItem>
            <MenuItem value={1}>Normal</MenuItem>
            <MenuItem value={1.25}>1.25x</MenuItem>
            <MenuItem value={1.5}>1.5x</MenuItem>
            <MenuItem value={1.75}>1.75x</MenuItem>
            <MenuItem value={2}>2x</MenuItem>
          </Select>
        </FormControl>
      </Box>

      {/* Current Chapter Display */}
      {showChapters && activeChapters[currentChapter] && (
        <Box
          sx={{
            mt: 2,
            pt: 2,
            borderTop: 1,
            borderColor: 'divider',
            textAlign: 'center',
          }}
        >
          <Typography variant="overline" color="text.secondary" display="block">
            Now Playing
          </Typography>
          <Typography variant="h6" fontWeight={600}>
            {activeChapters[currentChapter].title}
          </Typography>
        </Box>
      )}
    </Paper>
  );
};

export default AudioPlayer;

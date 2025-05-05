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
} from '@mui/material';
import {
PlayArrow,
Pause,
FastForward,
FastRewind,
VolumeUp,
VolumeOff,
} from '@mui/icons-material';
import WaveSurfer from 'wavesurfer.js';
import { useTheme } from '@mui/material/styles';
const AudioPlayer = ({ audioUrl }) => {
const [isPlaying, setIsPlaying] = useState(false);
const [currentTime, setCurrentTime] = useState(0);
const [duration, setDuration] = useState(0);
const [volume, setVolume] = useState(0.5);
const [playbackRate, setPlaybackRate] = useState(1);
const waveformRef = useRef(null);
const wavesurfer = useRef(null);
const theme = useTheme();
useEffect(() => {
const options = {
container: waveformRef.current,
waveColor: theme.palette.primary.light,
progressColor: theme.palette.primary.main,
cursorColor: theme.palette.primary.dark,
barWidth: 2,
barRadius: 3,
responsive: true,
height: 100,
normalize: true,
};
wavesurfer.current = WaveSurfer.create(options);
wavesurfer.current.load(audioUrl);

wavesurfer.current.on('ready', () => {
  setDuration(wavesurfer.current.getDuration());
});

wavesurfer.current.on('audioprocess', () => {
  setCurrentTime(wavesurfer.current.getCurrentTime());
});

wavesurfer.current.on('finish', () => {
  setIsPlaying(false);
});

return () => {
  if (wavesurfer.current) {
    wavesurfer.current.destroy();
  }
};
}, [audioUrl, theme]);
const handlePlayPause = () => {
wavesurfer.current.playPause();
setIsPlaying(!isPlaying);
};
const handleSkipForward = () => {
wavesurfer.current.skip(10);
};
const handleSkipBackward = () => {
wavesurfer.current.skip(-10);
};
const handleVolumeChange = (event, newValue) => {
setVolume(newValue);
wavesurfer.current.setVolume(newValue);
};
const handlePlaybackRateChange = (event) => {
const rate = event.target.value;
setPlaybackRate(rate);
wavesurfer.current.setPlaybackRate(rate);
};
const formatTime = (time) => {
const minutes = Math.floor(time / 60);
const seconds = Math.floor(time % 60);
return `${minutes}:${seconds.toString().padStart(2, '0')}`;
};
return (
<Paper sx={{ p: 2 }}>
<Box ref={waveformRef} sx={{ mb: 2 }} />
<Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', mb: 2 }}>
    <IconButton onClick={handleSkipBackward} size="large">
      <FastRewind fontSize="large" />
    </IconButton>
    <IconButton onClick={handlePlayPause} size="large">
      {isPlaying ? <Pause fontSize="large" /> : <PlayArrow fontSize="large" />}
    </IconButton>
    <IconButton onClick={handleSkipForward} size="large">
      <FastForward fontSize="large" />
    </IconButton>
  </Box>

  <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
    <Typography variant="body2" sx={{ minWidth: '40px' }}>
      {formatTime(currentTime)}
    </Typography>
    <Slider
      value={currentTime}
      max={duration}
      onChange={(e, newValue) => {
        wavesurfer.current.seekTo(newValue / duration);
        setCurrentTime(newValue);
      }}
      aria-labelledby="continuous-slider"
      sx={{ flexGrow: 1 }}
    />
    <Typography variant="body2" sx={{ minWidth: '40px' }}>
      {formatTime(duration)}
    </Typography>
  </Box>

  <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mt: 2 }}>
    <Box sx={{ display: 'flex', alignItems: 'center', width: 200 }}>
      <IconButton onClick={() => handleVolumeChange(null, volume > 0 ? 0 : 0.5)}>
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
        <MenuItem value={1}>1x</MenuItem>
        <MenuItem value={1.25}>1.25x</MenuItem>
        <MenuItem value={1.5}>1.5x</MenuItem>
        <MenuItem value={2}>2x</MenuItem>
      </Select>
    </FormControl>
  </Box>
</Paper>
);
};
export default AudioPlayer;
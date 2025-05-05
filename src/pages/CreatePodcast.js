// src/pages/CreatePodcast.js
import React, { useState } from 'react';
import {
Box,
Paper,
Typography,
TextField,
Button,
FormControl,
InputLabel,
Select,
MenuItem,
Grid,
FormControlLabel,
Switch,
LinearProgress,
} from '@mui/material';
import { useMutation } from 'react-query';
import axios from 'axios';
import { toast } from 'react-toastify';
import { useNavigate } from 'react-router-dom';
const CreatePodcast = () => {
const navigate = useNavigate();
const [title, setTitle] = useState('');
const [technicalLevel, setTechnicalLevel] = useState('intermediate');
const [targetLength, setTargetLength] = useState(15);
const [usePreferences, setUsePreferences] = useState(true);
const [paperIds, setPaperIds] = useState('');
const createPodcast = useMutation(
async (data) => {
const response = await axios.post('/api/v1/podcasts', data);
return response.data;
},
{
onSuccess: (data) => {
toast.success('Podcast generation started');
navigate(`/podcasts/${data.podcast_id}`);
},
onError: (error) => {
toast.error(error.response?.data?.message || 'Failed to create podcast');
},
}
);

const handleSubmit = (e) => {
e.preventDefault();
createPodcast.mutate({
title: title || undefined,
technical_level: technicalLevel,
target_length: targetLength,
use_preferences: usePreferences,
paper_ids: usePreferences ? [] : paperIds.split(',').map((id) => id.trim()),
});
};
return (
<Box>
<Typography variant="h4" gutterBottom>
Create New Podcast
</Typography>
<Paper sx={{ p: 3, mt: 3 }}>
    <form onSubmit={handleSubmit}>
      <Grid container spacing={3}>
        <Grid item xs={12}>
          <TextField
            fullWidth
            label="Podcast Title"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Leave empty for auto-generated title"
          />
        </Grid>

        <Grid item xs={12} sm={6}>
          <FormControl fullWidth>
            <InputLabel>Technical Level</InputLabel>
            <Select value={technicalLevel} label="Technical Level" onChange={(e) => setTechnicalLevel(e.target.value)}>
              <MenuItem value="beginner">Beginner</MenuItem>
              <MenuItem value="intermediate">Intermediate</MenuItem>
              <MenuItem value="advanced">Advanced</MenuItem>
            </Select>
          </FormControl>
        </Grid>

        <Grid item xs={12} sm={6}>
          <TextField
            fullWidth
            label="Target Length (minutes)"
            type="number"
            value={targetLength}
            onChange={(e) => setTargetLength(parseInt(e.target.value))}
            InputProps={{ inputProps: { min: 5, max: 60 } }}
          />
        </Grid>

        <Grid item xs={12}>
          <FormControlLabel
            control={
              <Switch
                checked={usePreferences}
                onChange={(e) => setUsePreferences(e.target.checked)}
              />
            }
            label="Use my research preferences"
          />
        </Grid>

        {!usePreferences && (
          <Grid item xs={12}>
            <TextField
              fullWidth
              label="ArXiv Paper IDs"
              value={paperIds}
              onChange={(e) => setPaperIds(e.target.value)}
              placeholder="Enter comma-separated ArXiv paper IDs (e.g., 2305.12140, 2305.14314)"
              helperText="Enter specific ArXiv paper IDs to create a podcast from"
            />
          </Grid>
        )}

        <Grid item xs={12}>
          <Button
            variant="contained"
            color="primary"
            size="large"
            type="submit"
            disabled={createPodcast.isLoading}
            fullWidth
          >
            {createPodcast.isLoading ? 'Creating...' : 'Create Podcast'}
          </Button>
        </Grid>
      </Grid>
    </form>
  </Paper>
</Box>
);
};
export default CreatePodcast;
// src/pages/Preferences.js
import React, { useState, useEffect } from 'react';
import {
Box,
Paper,
Typography,
TextField,
Button,
Chip,
CircularProgress,
FormControl,
InputLabel,
Select,
MenuItem,
Grid,
Autocomplete,
} from '@mui/material';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import axios from 'axios';
import { toast } from 'react-toastify';
const ARXIV_CATEGORIES = [
{ id: 'cs.AI', name: 'Artificial Intelligence', description: 'AI algorithms, machine learning, neural networks' },
{ id: 'cs.CL', name: 'Computation and Language', description: 'NLP, text processing, machine translation' },
{ id: 'cs.CV', name: 'Computer Vision', description: 'Image processing, object recognition, visual computing' },
{ id: 'cs.LG', name: 'Machine Learning', description: 'Learning algorithms, deep learning, reinforcement learning' },
{ id: 'cs.RO', name: 'Robotics', description: 'Robot control, motion planning, human-robot interaction' },
{ id: 'physics.comp-ph', name: 'Computational Physics', description: 'Numerical methods, simulation, quantum computing' },
{ id: 'q-bio.BM', name: 'Biomolecules', description: 'Protein structure, molecular dynamics, drug discovery' },
{ id: 'q-fin.CP', name: 'Computational Finance', description: 'Financial modeling, algorithmic trading' },
];
const Preferences = () => {
const queryClient = useQueryClient();
const [topics, setTopics] = useState([]);
const [currentTopic, setCurrentTopic] = useState('');
const [authors, setAuthors] = useState([]);
const [currentAuthor, setCurrentAuthor] = useState('');
const [categories, setCategories] = useState([]);
const [maxResults, setMaxResults] = useState(50);
const [daysBack, setDaysBack] = useState(30);
const [sortBy, setSortBy] = useState('relevance');
const { data: preferences, isLoading } = useQuery(['preferences'], async () => {
const response = await axios.get('/api/v1/users/preferences');
return response.data;
});
useEffect(() => {
if (preferences) {
setTopics(preferences.topics || []);
setAuthors(preferences.authors || []);
setCategories(preferences.categories || []);
setMaxResults(preferences.max_results || 50);
setDaysBack(preferences.days_back || 30);
setSortBy(preferences.sort_by || 'relevance');
}
}, [preferences]);
const updatePreferences = useMutation(
async (data) => {
const response = await axios.put('/api/v1/users/preferences', data);
return response.data;
},
{
onSuccess: () => {
queryClient.invalidateQueries(['preferences']);
toast.success('Preferences updated successfully');
},
onError: (error) => {
toast.error('Failed to update preferences');
},
}
);
const handleAddTopic = () => {
if (currentTopic && !topics.includes(currentTopic)) {
setTopics([...topics, currentTopic]);
setCurrentTopic('');
}
};
const handleAddAuthor = () => {
if (currentAuthor && !authors.includes(currentAuthor)) {
setAuthors([...authors, currentAuthor]);
setCurrentAuthor('');
}
};
const handleSubmit = (e) => {
e.preventDefault();
updatePreferences.mutate({
topics,
authors,
categories,
max_results: maxResults,
days_back: daysBack,
sort_by: sortBy,
});
};
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
Research Preferences
</Typography>
<Paper sx={{ p: 3, mt: 3 }}>
    <form onSubmit={handleSubmit}>
      <Grid container spacing={3}>
        <Grid item xs={12}>
          <Typography variant="h6" gutterBottom>
            Research Topics
          </Typography>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
            <Autocomplete
              freeSolo
              options={topics}
              value={currentTopic}
              onInputChange={(e, newValue) => setCurrentTopic(newValue)}
              renderInput={(params) => (
                <TextField {...params} label="Add topic" variant="outlined" fullWidth />
              )}
              sx={{ flexGrow: 1, mr: 2 }}
            />
            <Button variant="contained" color="primary" onClick={handleAddTopic}>
              Add
            </Button>
          </Box>
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
            {topics.map((topic, index) => (
              <Chip
                key={index}
                label={topic}
                onDelete={() => setTopics(topics.filter((_, i) => i !== index))}
              />
            ))}
          </Box>
        </Grid>

        <Grid item xs={12}>
          <Typography variant="h6" gutterBottom>
            Researchers
          </Typography>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
            <TextField
              fullWidth
              label="Add researcher"
              value={currentAuthor}
              onChange={(e) => setCurrentAuthor(e.target.value)}
              sx={{ mr: 2 }}
              placeholder="e.g., Geoffrey Hinton"
            />
            <Button variant="contained" color="primary" onClick={handleAddAuthor}>
              Add
            </Button>
          </Box>
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
            {authors.map((author, index) => (
              <Chip
                key={index}
                label={author}
                onDelete={() => setAuthors(authors.filter((_, i) => i !== index))}
              />
            ))}
          </Box>
        </Grid>

        <Grid item xs={12}>
          <Typography variant="h6" gutterBottom>
            ArXiv Categories
          </Typography>
          <FormControl fullWidth>
            <InputLabel>Select categories</InputLabel>
            <Select
              multiple
              value={categories}
              onChange={(e) => setCategories(e.target.value)}
              renderValue={(selected) => (
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                  {selected.map((value) => (
                    <Chip key={value} label={value} />
                  ))}
                </Box>
              )}
            >
              {ARXIV_CATEGORIES.map((category) => (
                <MenuItem key={category.id} value={category.id}>
                  <Typography>
                    {category.name}
                    <Typography variant="body2" color="textSecondary">
                      {category.description}
                    </Typography>
                  </Typography>
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Grid>

        <Grid item xs={12} sm={6}>
          <TextField
            fullWidth
            label="Maximum Results"
            type="number"
            value={maxResults}
            onChange={(e) => setMaxResults(parseInt(e.target.value))}
            InputProps={{ inputProps: { min: 1, max: 100 } }}
          />
        </Grid>

        <Grid item xs={12} sm={6}>
          <TextField
            fullWidth
            label="Days Back"
            type="number"
            value={daysBack}
            onChange={(e) => setDaysBack(parseInt(e.target.value))}
            InputProps={{ inputProps: { min: 0, max: 365 } }}
          />
        </Grid>

        <Grid item xs={12}>
          <FormControl fullWidth>
            <InputLabel>Sort By</InputLabel>
            <Select value={sortBy} label="Sort By" onChange={(e) => setSortBy(e.target.value)}>
              <MenuItem value="relevance">Relevance</MenuItem>
              <MenuItem value="lastUpdatedDate">Last Updated Date</MenuItem>
            </Select>
          </FormControl>
        </Grid>

        <Grid item xs={12}>
          <Button
            variant="contained"
            color="primary"
            size="large"
            type="submit"
            disabled={updatePreferences.isLoading}
            fullWidth
          >
            {updatePreferences.isLoading ? 'Saving...' : 'Save Preferences'}
          </Button>
        </Grid>
      </Grid>
    </form>
  </Paper>
</Box>
);
};
export default Preferences;
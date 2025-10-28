// src/components/Progress/GenerationProgress.js
import React from 'react';
import {
  Box,
  Typography,
  LinearProgress,
  Stepper,
  Step,
  StepLabel,
  StepContent,
  Paper,
  Chip,
  CircularProgress,
} from '@mui/material';
import {
  CheckCircle,
  CloudUpload,
  Psychology,
  RecordVoiceOver,
  VerifiedUser,
  Error as ErrorIcon,
  HourglassEmpty,
} from '@mui/icons-material';

const GenerationProgress = ({
  currentStage = 'upload',
  progress = 0,
  estimatedTime,
  error,
  compact = false,
}) => {
  const stages = [
    {
      key: 'upload',
      label: 'Upload',
      description: 'Processing paper upload',
      icon: <CloudUpload />,
    },
    {
      key: 'processing',
      label: 'Processing',
      description: 'Analyzing paper content',
      icon: <Psychology />,
    },
    {
      key: 'generation',
      label: 'Voice Generation',
      description: 'Converting to audio',
      icon: <RecordVoiceOver />,
    },
    {
      key: 'quality',
      label: 'Quality Check',
      description: 'Verifying audio quality',
      icon: <VerifiedUser />,
    },
    {
      key: 'complete',
      label: 'Complete',
      description: 'Podcast ready',
      icon: <CheckCircle />,
    },
  ];

  const getCurrentStageIndex = () => {
    return stages.findIndex((stage) => stage.key === currentStage);
  };

  const getStageStatus = (index) => {
    const currentIndex = getCurrentStageIndex();
    if (error && index === currentIndex) return 'error';
    if (index < currentIndex) return 'completed';
    if (index === currentIndex) return 'active';
    return 'pending';
  };

  const getStageIcon = (stage, index) => {
    const status = getStageStatus(index);

    if (status === 'error') {
      return <ErrorIcon color="error" />;
    }
    if (status === 'completed') {
      return <CheckCircle color="success" />;
    }
    if (status === 'active') {
      return (
        <CircularProgress
          size={24}
          sx={{ color: 'primary.main' }}
        />
      );
    }
    return <HourglassEmpty color="disabled" />;
  };

  const formatTime = (seconds) => {
    if (!seconds) return '';
    if (seconds < 60) return `${seconds}s`;
    const minutes = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${minutes}m ${secs}s`;
  };

  if (compact) {
    return (
      <Box sx={{ width: '100%' }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
          <Typography variant="body2" fontWeight={600}>
            {stages[getCurrentStageIndex()]?.label}
          </Typography>
          {estimatedTime && (
            <Typography variant="caption" color="text.secondary">
              ~{formatTime(estimatedTime)} remaining
            </Typography>
          )}
        </Box>
        <LinearProgress
          variant={progress > 0 ? 'determinate' : 'indeterminate'}
          value={progress}
          sx={{
            height: 8,
            borderRadius: 4,
            bgcolor: (theme) =>
              theme.palette.mode === 'dark' ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)',
          }}
        />
        {error && (
          <Typography variant="caption" color="error" sx={{ mt: 0.5, display: 'block' }}>
            {error}
          </Typography>
        )}
      </Box>
    );
  }

  return (
    <Paper
      elevation={2}
      sx={{
        p: 3,
        borderRadius: 2,
      }}
    >
      {/* Header */}
      <Box sx={{ mb: 3 }}>
        <Typography variant="h6" fontWeight={600} gutterBottom>
          Generation Progress
        </Typography>
        {estimatedTime && (
          <Chip
            icon={<HourglassEmpty />}
            label={`~${formatTime(estimatedTime)} remaining`}
            size="small"
            color="primary"
            variant="outlined"
          />
        )}
      </Box>

      {/* Overall Progress Bar */}
      <Box sx={{ mb: 4 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
          <Typography variant="body2" color="text.secondary">
            Overall Progress
          </Typography>
          <Typography variant="body2" fontWeight={600}>
            {Math.round(progress)}%
          </Typography>
        </Box>
        <LinearProgress
          variant="determinate"
          value={progress}
          sx={{
            height: 12,
            borderRadius: 6,
            bgcolor: (theme) =>
              theme.palette.mode === 'dark' ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)',
            '& .MuiLinearProgress-bar': {
              borderRadius: 6,
              background: (theme) =>
                `linear-gradient(90deg, ${theme.palette.primary.main} 0%, ${theme.palette.secondary.main} 100%)`,
            },
          }}
        />
      </Box>

      {/* Stage Stepper */}
      <Stepper activeStep={getCurrentStageIndex()} orientation="vertical">
        {stages.map((stage, index) => {
          const status = getStageStatus(index);
          return (
            <Step key={stage.key} completed={status === 'completed'}>
              <StepLabel
                error={status === 'error'}
                StepIconComponent={() => (
                  <Box
                    sx={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      width: 40,
                      height: 40,
                      borderRadius: '50%',
                      bgcolor:
                        status === 'completed'
                          ? 'success.light'
                          : status === 'active'
                          ? 'primary.light'
                          : status === 'error'
                          ? 'error.light'
                          : 'action.hover',
                      color:
                        status === 'completed'
                          ? 'success.contrastText'
                          : status === 'active'
                          ? 'primary.contrastText'
                          : status === 'error'
                          ? 'error.contrastText'
                          : 'text.disabled',
                      transition: 'all 0.3s ease',
                    }}
                  >
                    {getStageIcon(stage, index)}
                  </Box>
                )}
              >
                <Typography
                  variant="body1"
                  fontWeight={status === 'active' ? 600 : 400}
                  color={
                    status === 'error'
                      ? 'error'
                      : status === 'completed'
                      ? 'success.main'
                      : status === 'active'
                      ? 'primary'
                      : 'text.secondary'
                  }
                >
                  {stage.label}
                </Typography>
              </StepLabel>
              <StepContent>
                <Typography variant="body2" color="text.secondary">
                  {stage.description}
                </Typography>
                {status === 'active' && (
                  <Box sx={{ mt: 1 }}>
                    <LinearProgress
                      sx={{
                        height: 4,
                        borderRadius: 2,
                        width: '80%',
                      }}
                    />
                  </Box>
                )}
                {status === 'error' && error && (
                  <Typography variant="caption" color="error" sx={{ mt: 1, display: 'block' }}>
                    Error: {error}
                  </Typography>
                )}
              </StepContent>
            </Step>
          );
        })}
      </Stepper>

      {/* Status Message */}
      <Box
        sx={{
          mt: 3,
          p: 2,
          bgcolor: (theme) =>
            error
              ? theme.palette.error.light + '20'
              : currentStage === 'complete'
              ? theme.palette.success.light + '20'
              : theme.palette.primary.light + '20',
          borderRadius: 2,
          border: (theme) =>
            `1px solid ${
              error
                ? theme.palette.error.main
                : currentStage === 'complete'
                ? theme.palette.success.main
                : theme.palette.primary.main
            }`,
        }}
      >
        <Typography
          variant="body2"
          color={
            error ? 'error.main' : currentStage === 'complete' ? 'success.main' : 'primary.main'
          }
          fontWeight={600}
        >
          {error
            ? 'Generation failed. Please try again.'
            : currentStage === 'complete'
            ? 'Your podcast is ready!'
            : 'Generating your podcast...'}
        </Typography>
        {!error && currentStage !== 'complete' && (
          <Typography variant="caption" color="text.secondary" display="block" sx={{ mt: 0.5 }}>
            Please don't close this page while generation is in progress.
          </Typography>
        )}
      </Box>
    </Paper>
  );
};

export default GenerationProgress;

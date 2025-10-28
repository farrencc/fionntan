// src/components/Paper/PaperMetadata.js
import React, { useState } from 'react';
import {
  Box,
  Typography,
  Paper,
  Divider,
  Chip,
  IconButton,
  Link,
  Tooltip,
  Collapse,
  Button,
} from '@mui/material';
import {
  OpenInNew,
  ContentCopy,
  FormatQuote,
  ExpandMore,
  ExpandLess,
  Article,
  People,
  CalendarToday,
  Category,
} from '@mui/icons-material';
import { toast } from 'react-toastify';

const PaperMetadata = ({ paper }) => {
  const [showFullAbstract, setShowFullAbstract] = useState(false);
  const [showCitation, setShowCitation] = useState(false);

  if (!paper) return null;

  const {
    title,
    authors = [],
    abstract,
    arxivId,
    arxivUrl,
    pdfUrl,
    publishedDate,
    categories = [],
    journal,
    doi,
    citations,
  } = paper;

  const handleCopyToClipboard = (text, label) => {
    navigator.clipboard.writeText(text);
    toast.success(`${label} copied to clipboard!`);
  };

  const formatAuthors = (authorsList) => {
    if (!authorsList || authorsList.length === 0) return 'Unknown Authors';
    if (authorsList.length <= 3) {
      return authorsList.join(', ');
    }
    return `${authorsList.slice(0, 3).join(', ')}, et al. (${authorsList.length} authors)`;
  };

  const formatDate = (date) => {
    if (!date) return 'Date unknown';
    return new Date(date).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  };

  const generateBibTeX = () => {
    return `@article{${arxivId?.replace(/\./g, '_')},
  title={${title}},
  author={${authors.join(' and ')}},
  journal={arXiv preprint arXiv:${arxivId}},
  year={${new Date(publishedDate).getFullYear()}}
}`;
  };

  const generateAPACitation = () => {
    const authorStr = authors.length > 0 ? formatAuthors(authors) : 'Unknown Authors';
    const year = publishedDate ? new Date(publishedDate).getFullYear() : 'n.d.';
    return `${authorStr} (${year}). ${title}. arXiv preprint arXiv:${arxivId}.`;
  };

  return (
    <Paper
      elevation={2}
      sx={{
        p: 3,
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        gap: 2,
      }}
    >
      {/* Header Section */}
      <Box>
        <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 1, mb: 2 }}>
          <Article color="primary" sx={{ mt: 0.5 }} />
          <Typography variant="h5" component="h2" fontWeight={600} sx={{ flex: 1 }}>
            Paper Details
          </Typography>
        </Box>
        <Divider />
      </Box>

      {/* Title */}
      <Box>
        <Typography variant="overline" color="text.secondary" display="block">
          Title
        </Typography>
        <Typography variant="h6" fontWeight={600} sx={{ lineHeight: 1.4 }}>
          {title || 'Untitled Paper'}
        </Typography>
      </Box>

      {/* Authors */}
      {authors && authors.length > 0 && (
        <Box>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mb: 1 }}>
            <People fontSize="small" color="action" />
            <Typography variant="overline" color="text.secondary">
              Authors
            </Typography>
          </Box>
          <Typography variant="body2" sx={{ fontStyle: 'italic' }}>
            {formatAuthors(authors)}
          </Typography>
          {authors.length > 3 && (
            <Typography variant="caption" color="text.secondary" display="block" sx={{ mt: 0.5 }}>
              +{authors.length - 3} more authors
            </Typography>
          )}
        </Box>
      )}

      {/* Publication Info */}
      <Box>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mb: 1 }}>
          <CalendarToday fontSize="small" color="action" />
          <Typography variant="overline" color="text.secondary">
            Published
          </Typography>
        </Box>
        <Typography variant="body2">{formatDate(publishedDate)}</Typography>
        {journal && (
          <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
            {journal}
          </Typography>
        )}
      </Box>

      {/* Categories */}
      {categories && categories.length > 0 && (
        <Box>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mb: 1 }}>
            <Category fontSize="small" color="action" />
            <Typography variant="overline" color="text.secondary">
              Categories
            </Typography>
          </Box>
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
            {categories.map((category, index) => (
              <Chip key={index} label={category} size="small" variant="outlined" />
            ))}
          </Box>
        </Box>
      )}

      {/* Abstract */}
      {abstract && (
        <Box>
          <Typography variant="overline" color="text.secondary" display="block" gutterBottom>
            Abstract
          </Typography>
          <Collapse in={showFullAbstract} collapsedSize={100}>
            <Typography
              variant="body2"
              sx={{
                lineHeight: 1.7,
                textAlign: 'justify',
              }}
            >
              {abstract}
            </Typography>
          </Collapse>
          {abstract.length > 300 && (
            <Button
              size="small"
              endIcon={showFullAbstract ? <ExpandLess /> : <ExpandMore />}
              onClick={() => setShowFullAbstract(!showFullAbstract)}
              sx={{ mt: 1 }}
            >
              {showFullAbstract ? 'Show Less' : 'Show More'}
            </Button>
          )}
        </Box>
      )}

      <Divider />

      {/* Links */}
      <Box>
        <Typography variant="overline" color="text.secondary" display="block" gutterBottom>
          Links
        </Typography>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
          {arxivUrl && (
            <Link
              href={arxivUrl}
              target="_blank"
              rel="noopener noreferrer"
              sx={{
                display: 'flex',
                alignItems: 'center',
                gap: 1,
                textDecoration: 'none',
                '&:hover': { textDecoration: 'underline' },
              }}
            >
              <OpenInNew fontSize="small" />
              <Typography variant="body2">View on arXiv</Typography>
            </Link>
          )}
          {pdfUrl && (
            <Link
              href={pdfUrl}
              target="_blank"
              rel="noopener noreferrer"
              sx={{
                display: 'flex',
                alignItems: 'center',
                gap: 1,
                textDecoration: 'none',
                '&:hover': { textDecoration: 'underline' },
              }}
            >
              <Article fontSize="small" />
              <Typography variant="body2">Download PDF</Typography>
            </Link>
          )}
          {doi && (
            <Link
              href={`https://doi.org/${doi}`}
              target="_blank"
              rel="noopener noreferrer"
              sx={{
                display: 'flex',
                alignItems: 'center',
                gap: 1,
                textDecoration: 'none',
                '&:hover': { textDecoration: 'underline' },
              }}
            >
              <OpenInNew fontSize="small" />
              <Typography variant="body2">DOI: {doi}</Typography>
            </Link>
          )}
        </Box>
      </Box>

      {/* Citation */}
      <Box>
        <Box
          sx={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            mb: 1,
          }}
        >
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
            <FormatQuote fontSize="small" color="action" />
            <Typography variant="overline" color="text.secondary">
              Citation
            </Typography>
          </Box>
          <Button
            size="small"
            onClick={() => setShowCitation(!showCitation)}
            endIcon={showCitation ? <ExpandLess /> : <ExpandMore />}
          >
            {showCitation ? 'Hide' : 'Show'}
          </Button>
        </Box>

        <Collapse in={showCitation}>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
            {/* APA Citation */}
            <Box>
              <Typography variant="caption" fontWeight={600} display="block" gutterBottom>
                APA Format
              </Typography>
              <Paper
                variant="outlined"
                sx={{
                  p: 1.5,
                  bgcolor: (theme) =>
                    theme.palette.mode === 'dark' ? 'rgba(255,255,255,0.02)' : 'rgba(0,0,0,0.02)',
                  position: 'relative',
                }}
              >
                <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.75rem' }}>
                  {generateAPACitation()}
                </Typography>
                <Tooltip title="Copy citation">
                  <IconButton
                    size="small"
                    onClick={() => handleCopyToClipboard(generateAPACitation(), 'APA citation')}
                    sx={{
                      position: 'absolute',
                      top: 4,
                      right: 4,
                    }}
                  >
                    <ContentCopy fontSize="small" />
                  </IconButton>
                </Tooltip>
              </Paper>
            </Box>

            {/* BibTeX */}
            <Box>
              <Typography variant="caption" fontWeight={600} display="block" gutterBottom>
                BibTeX
              </Typography>
              <Paper
                variant="outlined"
                sx={{
                  p: 1.5,
                  bgcolor: (theme) =>
                    theme.palette.mode === 'dark' ? 'rgba(255,255,255,0.02)' : 'rgba(0,0,0,0.02)',
                  position: 'relative',
                }}
              >
                <Typography
                  variant="body2"
                  component="pre"
                  sx={{
                    fontFamily: 'monospace',
                    fontSize: '0.7rem',
                    whiteSpace: 'pre-wrap',
                    wordBreak: 'break-word',
                    m: 0,
                  }}
                >
                  {generateBibTeX()}
                </Typography>
                <Tooltip title="Copy BibTeX">
                  <IconButton
                    size="small"
                    onClick={() => handleCopyToClipboard(generateBibTeX(), 'BibTeX')}
                    sx={{
                      position: 'absolute',
                      top: 4,
                      right: 4,
                    }}
                  >
                    <ContentCopy fontSize="small" />
                  </IconButton>
                </Tooltip>
              </Paper>
            </Box>
          </Box>
        </Collapse>
      </Box>

      {/* arXiv ID */}
      {arxivId && (
        <Box sx={{ mt: 'auto', pt: 2 }}>
          <Chip
            label={`arXiv: ${arxivId}`}
            size="small"
            variant="outlined"
            icon={<Article />}
            sx={{ fontFamily: 'monospace' }}
          />
        </Box>
      )}
    </Paper>
  );
};

export default PaperMetadata;

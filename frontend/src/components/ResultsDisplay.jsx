// frontend/src/components/ResultsDisplay.jsx
import React from 'react';
import { Typography, Paper, Box, Divider } from '@mui/material';

function ResultsDisplay({ results }) {
  if (!results) {
    return (
      <Paper elevation={0} sx={{ p: 2, backgroundColor: '#f5f5f5', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <Typography variant="body2" sx={{ color: '#666' }}>
          // No sandbox results yet
        </Typography>
      </Paper>
    );
  }

  // Ensure results is an object before destructuring.
  // If results might be a simple string (e.g. from an earlier agent version or a simple success message), handle it.
  if (typeof results !== 'object' || results === null) {
    return (
        <Paper elevation={0} sx={{ p: 2, backgroundColor: '#f5f5f5', height: '100%' }}>
            <Typography component="pre" sx={{ whiteSpace: 'pre-wrap', wordBreak: 'break-all', fontSize: '0.9rem' }}>
                {String(results)}
            </Typography>
        </Paper>
    );
  }

  const { stdout, stderr, error, exit_code, execution_time, ...otherResults } = results;

  return (
    <Paper elevation={0} sx={{ p: 2, fontFamily: 'monospace', fontSize: '0.9rem', height: '100%', overflowY: 'auto', boxSizing: 'border-box' }}>
      {error && (
        <Box mb={2}>
          <Typography variant="subtitle2" sx={{ color: 'error.main', fontWeight: 'bold' }}>
            Sandbox Error:
          </Typography>
          <Typography component="pre" sx={{ whiteSpace: 'pre-wrap', wordBreak: 'break-all', color: 'error.main', pl:1, fontSize: '0.85rem' }}>
            {error}
          </Typography>
          <Divider sx={{ my: 1 }} />
        </Box>
      )}

      {typeof exit_code === 'number' && (
        <Box mb={1}>
          <Typography variant="subtitle2" display="inline" sx={{ fontWeight: 'bold' }}>Exit Code: </Typography>
          <Typography display="inline" sx={{ color: exit_code === 0 ? 'success.main' : 'error.main' }}>
            {exit_code} {exit_code === 0 ? '(Success)' : '(Failed)'}
          </Typography>
        </Box>
      )}
      
      {typeof execution_time === 'number' && (
        <Box mb={2}>
          <Typography variant="subtitle2" display="inline" sx={{ fontWeight: 'bold' }}>Execution Time: </Typography>
          <Typography display="inline">
            {execution_time.toFixed(3)}s
          </Typography>
        </Box>
      )}
      
      {(stdout !== undefined && stdout !== null) && ( // Check for null as well as undefined
        <Box mb={2}>
          <Typography variant="subtitle2" sx={{ fontWeight: 'bold' }}>Stdout:</Typography>
          <Paper variant="outlined" sx={{ p: 1, mt: 0.5, whiteSpace: 'pre-wrap', wordBreak: 'break-all', maxHeight: '150px', overflowY: 'auto', backgroundColor: '#e8f5e9', fontSize: '0.85rem' }}>
            {stdout.trim() === '' ? <Typography variant="caption" sx={{color: 'text.secondary'}}> (empty)</Typography> : stdout}
          </Paper>
        </Box>
      )}

      {(stderr !== undefined && stderr !== null) && ( // Check for null as well as undefined
        <Box mb={2}>
          <Typography variant="subtitle2" sx={{ fontWeight: 'bold', color: stderr.trim() ? 'error.main' : 'inherit' }}>Stderr:</Typography>
          <Paper variant="outlined" sx={{ p: 1, mt: 0.5, whiteSpace: 'pre-wrap', wordBreak: 'break-all', maxHeight: '150px', overflowY: 'auto', backgroundColor: stderr.trim() ? '#ffebee' : '#f5f5f5', fontSize: '0.85rem' }}>
            {stderr.trim() === '' ? <Typography variant="caption" sx={{color: 'text.secondary'}}>(empty)</Typography> : stderr}
          </Paper>
        </Box>
      )}

      {Object.keys(otherResults).length > 0 && (
        <Box>
          <Typography variant="subtitle2" sx={{ fontWeight: 'bold' }}>Other Results:</Typography>
          <Paper variant="outlined" sx={{ p: 1, mt: 0.5, whiteSpace: 'pre-wrap', wordBreak: 'break-all', fontSize: '0.85rem' }}>
            {JSON.stringify(otherResults, null, 2)}
          </Paper>
        </Box>
      )}
    </Paper>
  );
}

export default ResultsDisplay;

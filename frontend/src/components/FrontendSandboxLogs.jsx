// frontend/src/components/FrontendSandboxLogs.jsx
import React from 'react';
import { List, ListItem, ListItemIcon, ListItemText, Typography, Paper, Chip, Box } from '@mui/material';
import InfoIcon from '@mui/icons-material/Info';
import WarningIcon from '@mui/icons-material/Warning';
import ErrorIcon from '@mui/icons-material/Error';
import NotesIcon from '@mui/icons-material/Notes'; // For generic 'log'

const getIconAndColor = (level) => {
  switch (level?.toLowerCase()) {
    case 'error': return { icon: <ErrorIcon color="error" />, color: 'error.main' };
    case 'warn': return { icon: <WarningIcon sx={{ color: 'warning.main' }} />, color: 'warning.main' };
    case 'info': return { icon: <InfoIcon color="info" />, color: 'info.main' };
    case 'log':
    default: return { icon: <NotesIcon color="action" />, color: 'text.secondary' };
  }
};

const formatLogData = (data) => {
  if (!Array.isArray(data)) {
    // Handle cases where data might already be a pre-formatted string or a simple type
    if (typeof data === 'object' && data !== null && data.__isError) {
        return `Error: ${data.name || 'Unknown Error'}: ${data.message}\n${data.stack || '(no stack trace)'}`;
    }
    return String(data);
  }
  return data.map(arg => {
    if (typeof arg === 'object' && arg !== null) {
      if (arg.__isError) return `Error: ${arg.name || 'Unknown Error'}: ${arg.message}\n${arg.stack || '(no stack trace)'}`;
      try { return JSON.stringify(arg); } catch (e) { return '[Unserializable Object]'; }
    }
    return String(arg);
  }).join(' ');
};

function FrontendSandboxLogs({ logs }) {
  if (!logs || logs.length === 0) {
    return (
      <Typography variant="body2" sx={{ p: 2, color: 'text.secondary', textAlign:'center' }}>
        No logs from frontend sandbox yet.
      </Typography>
    );
  }

  return (
    <List dense sx={{ maxHeight: '100%', overflowY: 'auto', p:0, bgcolor: 'background.paper', borderRadius: 1 }}>
      {logs.map((log, index) => {
        const { icon, color } = getIconAndColor(log.level);
        let primaryText = '';
        let secondaryContent = null;
        const timestamp = log.timestamp ? new Date(log.timestamp).toLocaleTimeString() : '';

        if (log.type === 'sandbox-log') {
          primaryText = `[${log.level?.toUpperCase() || 'LOG'}]`;
          secondaryContent = formatLogData(log.data);
        } else if (log.type === 'sandbox-error') {
          primaryText = `[ERROR] ${log.message || 'Unknown error'}`;
          if (log.errorObject?.stack) {
            secondaryContent = <Typography component="pre" variant="caption" sx={{ whiteSpace: 'pre-wrap', wordBreak: 'break-all', mt: 0.5, color: 'text.secondary' }}>{log.errorObject.stack}</Typography>;
          } else if (log.message && (log.filename || log.lineno)) {
             secondaryContent = `At ${log.filename || 'unknown file'} (line ${log.lineno || '?'}, col ${log.colno || '?'})`;
          } else if (log.errorObject?.message) { // Fallback if stack isn't there but message is in errorObject
             secondaryContent = log.errorObject.message;
          }
        } else { // Fallback for unknown log types or direct strings if any
          primaryText = `[${log.level?.toUpperCase() || 'UNKNOWN'}] ${log.type || 'Message'}`;
          secondaryContent = typeof log === 'object' ? JSON.stringify(log, null, 2) : String(log);
        }

        return (
          <ListItem 
            key={index} 
            divider 
            sx={{ 
                alignItems: 'flex-start', 
                py: 0.75, px:1, 
                '&:hover': {backgroundColor: 'action.hover'},
                borderBottom: '1px solid rgba(0, 0, 0, 0.05)' 
            }}
          >
            <ListItemIcon sx={{ minWidth: '30px', mt: '3px', mr: 0.5 }}>{icon}</ListItemIcon>
            <ListItemText
              primary={
                <Box sx={{display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
                    <Typography variant="caption" sx={{ fontWeight: 'bold', color: color, display: 'block' }}>
                        {primaryText}
                    </Typography>
                    {timestamp && <Typography variant="caption" sx={{color: 'text.disabled', fontSize: '0.65rem'}}>{timestamp}</Typography>}
                </Box>
              }
              secondary={
                <Typography component="div" variant="caption" sx={{ whiteSpace: 'pre-wrap', wordBreak: 'break-all', color: 'text.primary', mt: 0.25, pl: '2px' }}>
                  {secondaryContent}
                </Typography>
              }
              sx={{my:0}}
            />
          </ListItem>
        );
      })}
    </List>
  );
}
export default FrontendSandboxLogs;

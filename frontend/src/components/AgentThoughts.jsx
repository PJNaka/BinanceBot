import React from 'react';
import { List, ListItem, ListItemText, Paper, Typography } from '@mui/material';

function AgentThoughts({ stream }) {
  if (!stream || stream.length === 0) {
    return <Typography variant="body2">No agent thoughts or stream yet...</Typography>;
  }

  return (
    <List dense sx={{maxHeight: '380px', overflowY: 'auto'}}>
      {stream.map((item, index) => (
        <ListItem key={index} sx={{ 
            borderBottom: '1px solid #eee', 
            alignItems: 'flex-start',
            backgroundColor: index % 2 ? '#f9f9f9' : 'transparent' // Alternating row colors
        }}>
          <ListItemText
            primary={
              <Typography variant="caption" sx={{ color: 'gray', display: 'block', fontWeight: 'bold' }}>
                Msg {index + 1} | Type: {item.type || 'N/A'} 
                {item.phase ? ` | Phase: ${item.phase}`: ""}
                {item.iteration ? ` | Iter: ${item.iteration}`: ""}
                {item.sub_phase ? ` | Sub: ${item.sub_phase}`: ""}
              </Typography>
            }
            secondary={
              <Typography component="pre" variant="body2" sx={{ whiteSpace: 'pre-wrap', wordBreak: 'break-all', fontSize: '0.8rem', marginTop: '4px' }}>
                {typeof item === 'object' ? JSON.stringify(item, null, 2) : item}
              </Typography>
            }
            sx={{margin:0, padding: '4px 0'}}
          />
        </ListItem>
      ))}
    </List>
  );
}
export default AgentThoughts;

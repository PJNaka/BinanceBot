import React from 'react';
import { Typography, Paper, List, ListItem, ListItemText } from '@mui/material';

function ScienceDataDisplay({ data }) {
  if (!data || data.length === 0) {
    return <Typography variant="body2">Loading science data or no data available...</Typography>;
  }
  return (
    <Paper elevation={0} sx={{maxHeight: '280px', overflowY: 'auto', p:1, backgroundColor: '#e9e9ff'}}>
      <List dense>
        {data.map((item, index) => (
          <ListItem key={item.symbol || index} sx={{borderBottom: '1px solid #ddd'}}>
            <ListItemText 
              primaryTypographyProps={{variant: 'subtitle2'}}
              secondaryTypographyProps={{variant: 'body2', fontSize: '0.8rem'}}
              primary={`${item.name} (${item.symbol})`} 
              secondary={`Atomic #: ${item.atomic_number}, Mass: ${item.mass.toFixed(3)}`} />
          </ListItem>
        ))}
      </List>
    </Paper>
  );
}
export default ScienceDataDisplay;

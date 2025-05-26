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
              <Box sx={{ mt: 0.5, whiteSpace: 'pre-wrap', wordBreak: 'break-all', fontSize: '0.8rem' }}>
                {item.type === 'agent_action' && item.action === 'web_search' ? (
                  <Typography variant="body2" sx={{ fontStyle: 'italic', color: 'info.main' }}>
                    Searching for: "{item.query}"...
                  </Typography>
                ) : item.type === 'search_results' ? (
                  <Box>
                    <Typography variant="body2" sx={{ fontWeight: 'bold', color: 'primary.main' }}>
                      Search Results Received ({item.results?.length || 0} results):
                    </Typography>
                    {item.results && item.results.length > 0 ? (
                      <List dense sx={{pl: 2, fontSize: '0.75rem'}}>
                        {item.results.slice(0, 3).map((res, idx) => ( // Show first 3 results as example
                          <ListItem key={idx} sx={{display: 'block', p:0, mb:0.5}}>
                            <Typography variant="caption" component="div" sx={{fontWeight: 'medium'}}>
                               {res.title || 'No Title'}
                            </Typography>
                            <Typography variant="caption" component="div" sx={{color: 'text.secondary', fontSize: '0.7rem'}}>
                               <a href={res.url} target="_blank" rel="noopener noreferrer">{res.url}</a>
                            </Typography>
                            {res.content && 
                                <Typography variant="caption" component="div" sx={{fontSize: '0.7rem', color: 'text.disabled', maxHeight: '40px', overflow: 'hidden', textOverflow: 'ellipsis'}}>
                                    {res.content.substring(0,100)}...
                                </Typography>
                            }
                          </ListItem>
                        ))}
                        {item.results.length > 3 && <Typography variant="caption">...and {item.results.length - 3} more.</Typography>}
                      </List>
                    ) : (
                      <Typography variant="body2" sx={{ fontStyle: 'italic', ml: 2 }}>
                        No results found or search returned an error.
                      </Typography>
                    )}
                  </Box>
                ) : item.type === 'agent_action' && item.action === 'fetch_url' ? (
                  <Typography variant="body2" sx={{ fontStyle: 'italic', color: 'info.dark' }}>
                    Fetching URL: {item.url}...
                  </Typography>
                ) : item.type === 'url_fetch_result' ? (
                  <Box>
                    <Typography variant="body2" sx={{ fontWeight: 'bold', color: item.error ? 'error.main' : 'success.dark' }}>
                      URL Fetch Result for: <a href={item.url} target="_blank" rel="noopener noreferrer">{item.url}</a>
                    </Typography>
                    {item.error ? (
                      <Typography variant="caption" component="div" sx={{ color: 'error.main', mt: 0.5 }}>
                        Error: {item.error}
                      </Typography>
                    ) : (
                      item.content_snippet && 
                        <Typography variant="caption" component="div" sx={{ mt: 0.5, color: 'text.secondary', maxHeight: '60px', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                            Snippet: {item.content_snippet}...
                        </Typography>
                    )}
                  </Box>
                ) : (
                  // Default rendering for other message types
                  <Typography component="pre" variant="body2">
                    {typeof item === 'object' ? JSON.stringify(item, null, 2) : item}
                  </Typography>
                )}
              </Box>
            }
            sx={{margin:0, padding: '4px 0'}}
          />
        </ListItem>
      ))}
    </List>
  );
}
export default AgentThoughts;

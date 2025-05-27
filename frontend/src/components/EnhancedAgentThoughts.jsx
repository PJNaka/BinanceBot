import React, { useState, useEffect } from 'react';
import { 
  Box, 
  Paper, 
  Typography, 
  Divider, 
  Chip, 
  LinearProgress, 
  Collapse,
  IconButton,
  Tooltip
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';
import CodeIcon from '@mui/icons-material/Code';
import TerminalIcon from '@mui/icons-material/Terminal';
import LanguageIcon from '@mui/icons-material/Language';
import FolderIcon from '@mui/icons-material/Folder';
import InfoIcon from '@mui/icons-material/Info';

// Componente para exibir o fluxo de pensamentos e ações do agente
function EnhancedAgentThoughts({ stream }) {
  const [expandedItems, setExpandedItems] = useState({});
  const [autoScroll, setAutoScroll] = useState(true);
  const streamContainerRef = React.useRef(null);

  // Função para alternar a expansão de um item específico
  const toggleExpand = (index) => {
    setExpandedItems(prev => ({
      ...prev,
      [index]: !prev[index]
    }));
  };

  // Auto-scroll para o último item quando novos itens são adicionados
  useEffect(() => {
    if (autoScroll && streamContainerRef.current && stream.length > 0) {
      const container = streamContainerRef.current;
      container.scrollTop = container.scrollHeight;
    }
  }, [stream, autoScroll]);

  // Função para renderizar ícone com base no tipo de mensagem
  const renderIcon = (type, action) => {
    switch (type) {
      case 'code_generated':
        return <CodeIcon fontSize="small" color="primary" />;
      case 'agent_action':
        if (action === 'web_search' || action === 'fetch_url') {
          return <LanguageIcon fontSize="small" color="info" />;
        }
        return <TerminalIcon fontSize="small" color="secondary" />;
      case 'error':
        return <InfoIcon fontSize="small" color="error" />;
      case 'phase_update':
        return <FolderIcon fontSize="small" color="success" />;
      default:
        return <TerminalIcon fontSize="small" color="action" />;
    }
  };

  // Função para formatar o timestamp
  const formatTimestamp = (message) => {
    if (!message.timestamp) return '';
    
    try {
      const date = new Date(message.timestamp);
      return date.toLocaleTimeString();
    } catch (e) {
      return '';
    }
  };

  // Função para determinar a cor do chip com base no tipo de mensagem
  const getChipColor = (type) => {
    switch (type) {
      case 'error':
        return 'error';
      case 'success':
        return 'success';
      case 'phase_update':
        return 'primary';
      case 'code_generated':
        return 'secondary';
      case 'search_results':
      case 'url_fetch_result':
        return 'info';
      default:
        return 'default';
    }
  };

  return (
    <Box 
      ref={streamContainerRef}
      sx={{ 
        height: '100%', 
        overflowY: 'auto',
        display: 'flex',
        flexDirection: 'column',
        gap: 1.5,
        p: 1,
        '&::-webkit-scrollbar': {
          width: '8px',
        },
        '&::-webkit-scrollbar-track': {
          background: '#f1f1f1',
          borderRadius: '10px',
        },
        '&::-webkit-scrollbar-thumb': {
          background: '#c1c1c1',
          borderRadius: '10px',
        },
        '&::-webkit-scrollbar-thumb:hover': {
          background: '#a8a8a8',
        },
      }}
    >
      {stream.length === 0 ? (
        <Box sx={{ 
          display: 'flex', 
          flexDirection: 'column', 
          alignItems: 'center', 
          justifyContent: 'center',
          height: '100%',
          opacity: 0.7
        }}>
          <Typography variant="body2" color="text.secondary" align="center">
            Aguardando comandos...
          </Typography>
          <Typography variant="body2" color="text.secondary" align="center">
            Digite um comando para iniciar o processamento.
          </Typography>
        </Box>
      ) : (
        stream.map((message, index) => (
          <Paper 
            key={index} 
            elevation={1}
            sx={{ 
              p: 1.5,
              borderRadius: 2,
              borderLeft: `4px solid ${message.type === 'error' ? '#EF4444' : 
                message.type === 'success' ? '#10B981' : 
                message.type === 'phase_update' ? '#2563EB' : 
                message.type === 'code_generated' ? '#8B5CF6' : '#64748B'}`,
              transition: 'all 0.2s ease',
              animation: 'fadeIn 0.5s ease',
              '&:hover': {
                boxShadow: '0px 4px 8px rgba(0, 0, 0, 0.1)',
              }
            }}
          >
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                {renderIcon(message.type, message.action)}
                <Chip 
                  label={message.type || 'info'} 
                  size="small" 
                  color={getChipColor(message.type)}
                  variant="outlined"
                />
                {message.phase && (
                  <Chip 
                    label={message.phase} 
                    size="small" 
                    variant="outlined"
                    sx={{ fontSize: '0.7rem' }}
                  />
                )}
              </Box>
              
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                {formatTimestamp(message) && (
                  <Typography variant="caption" color="text.secondary">
                    {formatTimestamp(message)}
                  </Typography>
                )}
                
                {(message.message?.length > 100 || message.content_snippet?.length > 100 || message.results?.length > 0) && (
                  <Tooltip title={expandedItems[index] ? "Recolher" : "Expandir"}>
                    <IconButton 
                      size="small" 
                      onClick={() => toggleExpand(index)}
                      sx={{ p: 0.5 }}
                    >
                      {expandedItems[index] ? <ExpandLessIcon fontSize="small" /> : <ExpandMoreIcon fontSize="small" />}
                    </IconButton>
                  </Tooltip>
                )}
              </Box>
            </Box>
            
            {message.message && (
              <Collapse in={message.message.length <= 100 || expandedItems[index]} collapsedSize={message.message.length > 100 ? "40px" : "auto"}>
                <Typography 
                  variant="body2" 
                  sx={{ 
                    whiteSpace: 'pre-wrap',
                    wordBreak: 'break-word',
                    mb: 1
                  }}
                >
                  {message.message}
                </Typography>
              </Collapse>
            )}
            
            {message.content_snippet && (
              <Collapse in={expandedItems[index]} collapsedSize="0px">
                <Box sx={{ mt: 1, p: 1, bgcolor: 'background.default', borderRadius: 1 }}>
                  <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.5 }}>
                    Conteúdo da página:
                  </Typography>
                  <Typography 
                    variant="body2" 
                    sx={{ 
                      whiteSpace: 'pre-wrap',
                      wordBreak: 'break-word',
                      fontSize: '0.8rem',
                      maxHeight: '200px',
                      overflowY: 'auto'
                    }}
                  >
                    {message.content_snippet}
                  </Typography>
                </Box>
              </Collapse>
            )}
            
            {message.results && message.results.length > 0 && (
              <Collapse in={expandedItems[index]} collapsedSize="0px">
                <Box sx={{ mt: 1 }}>
                  <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.5 }}>
                    Resultados da pesquisa:
                  </Typography>
                  <Box sx={{ pl: 1, borderLeft: '2px solid #e0e0e0' }}>
                    {message.results.map((result, idx) => (
                      <Box key={idx} sx={{ mb: 1 }}>
                        <Typography variant="body2" sx={{ fontWeight: 500 }}>
                          {result.title || 'Sem título'}
                        </Typography>
                        <Typography variant="caption" color="primary" sx={{ display: 'block', wordBreak: 'break-all' }}>
                          {result.url || '#'}
                        </Typography>
                        <Typography variant="body2" color="text.secondary" sx={{ fontSize: '0.8rem' }}>
                          {result.snippet || 'Sem descrição'}
                        </Typography>
                        <Divider sx={{ my: 1 }} />
                      </Box>
                    ))}
                  </Box>
                </Box>
              </Collapse>
            )}
            
            {message.type === 'phase_update' && message.progress !== undefined && (
              <Box sx={{ mt: 1 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                  <Typography variant="caption" color="text.secondary">
                    Progresso
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    {Math.round(message.progress * 100)}%
                  </Typography>
                </Box>
                <LinearProgress 
                  variant="determinate" 
                  value={message.progress * 100} 
                  sx={{ 
                    height: 6, 
                    borderRadius: 3,
                    bgcolor: 'rgba(37, 99, 235, 0.1)',
                    '& .MuiLinearProgress-bar': {
                      borderRadius: 3,
                      background: 'linear-gradient(90deg, #2563EB, #3B82F6)',
                    }
                  }}
                />
              </Box>
            )}
          </Paper>
        ))
      )}
    </Box>
  );
}

export default EnhancedAgentThoughts;

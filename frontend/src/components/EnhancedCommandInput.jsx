import React, { useState } from 'react';
import { 
  TextField, 
  Button, 
  Box, 
  Paper, 
  Typography, 
  IconButton, 
  Tooltip,
  CircularProgress
} from '@mui/material';
import SendIcon from '@mui/icons-material/Send';
import MicIcon from '@mui/icons-material/Mic';
import HistoryIcon from '@mui/icons-material/History';
import HelpOutlineIcon from '@mui/icons-material/HelpOutline';

function EnhancedCommandInput({ command, setCommand, onSubmit, isLoading }) {
  const [showHints, setShowHints] = useState(false);
  
  const handleInputChange = (event) => {
    setCommand(event.target.value);
  };

  const handleSubmit = (event) => {
    event.preventDefault();
    onSubmit();
  };

  const handleKeyDown = (event) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      onSubmit();
    }
  };

  const toggleHints = () => {
    setShowHints(!showHints);
  };

  // Exemplos de comandos para ajudar o usuário
  const exampleCommands = [
    'Analisar dados da ação TSLA e criar um dashboard',
    'Criar uma página web para exibir cotações de criptomoedas',
    'Automatizar a coleta de dados do mercado financeiro',
    'Gerar relatório de desempenho das ações da Binance'
  ];

  return (
    <Box sx={{ mb: 4 }}>
      <Paper 
        elevation={3} 
        sx={{ 
          p: 3, 
          borderRadius: 2,
          background: 'linear-gradient(to right, #FFFFFF, #F9FAFB)',
          transition: 'all 0.3s ease',
          '&:hover': {
            boxShadow: '0px 8px 16px rgba(0, 0, 0, 0.08)',
          }
        }}
      >
        <Typography 
          variant="h5" 
          component="h2" 
          gutterBottom 
          sx={{ 
            fontWeight: 600,
            color: 'text.primary',
            mb: 2,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between'
          }}
        >
          <span>O que você gostaria de fazer hoje?</span>
          <Tooltip title="Dicas de uso">
            <IconButton onClick={toggleHints} color="primary" size="small">
              <HelpOutlineIcon />
            </IconButton>
          </Tooltip>
        </Typography>
        
        {showHints && (
          <Box 
            sx={{ 
              mb: 2, 
              p: 2, 
              bgcolor: 'rgba(37, 99, 235, 0.05)', 
              borderRadius: 1,
              border: '1px solid rgba(37, 99, 235, 0.1)',
              animation: 'fadeIn 0.5s ease'
            }}
          >
            <Typography variant="body2" gutterBottom>
              Exemplos de comandos que você pode usar:
            </Typography>
            <Box component="ul" sx={{ pl: 2, m: 0 }}>
              {exampleCommands.map((example, index) => (
                <Typography 
                  component="li" 
                  variant="body2" 
                  key={index}
                  sx={{ 
                    cursor: 'pointer', 
                    '&:hover': { color: 'primary.main' },
                    mb: 0.5
                  }}
                  onClick={() => setCommand(example)}
                >
                  {example}
                </Typography>
              ))}
            </Box>
          </Box>
        )}
        
        <Box 
          component="form" 
          onSubmit={handleSubmit} 
          sx={{ 
            display: 'flex', 
            gap: 1, 
            alignItems: 'flex-start',
            position: 'relative'
          }}
        >
          <TextField
            label="Digite seu comando ou tarefa"
            variant="outlined"
            fullWidth
            value={command}
            onChange={handleInputChange}
            onKeyDown={handleKeyDown}
            disabled={isLoading}
            multiline
            minRows={1}
            maxRows={4}
            placeholder="Ex: Analisar dados da ação TSLA e criar um dashboard"
            sx={{
              '& .MuiOutlinedInput-root': {
                borderRadius: 2,
                transition: 'all 0.3s ease',
                pr: 10, // Espaço para os botões à direita
              }
            }}
          />
          
          <Box sx={{ 
            position: 'absolute', 
            right: 8, 
            top: '50%', 
            transform: 'translateY(-50%)',
            display: 'flex',
            gap: 0.5
          }}>
            <Tooltip title="Histórico de comandos">
              <IconButton 
                color="primary" 
                size="small"
                disabled={isLoading}
              >
                <HistoryIcon fontSize="small" />
              </IconButton>
            </Tooltip>
            
            <Tooltip title="Entrada por voz">
              <IconButton 
                color="primary" 
                size="small"
                disabled={isLoading}
              >
                <MicIcon fontSize="small" />
              </IconButton>
            </Tooltip>
            
            <Tooltip title="Enviar comando">
              <IconButton
                color="primary"
                onClick={handleSubmit}
                disabled={isLoading || !command.trim()}
                sx={{
                  bgcolor: 'primary.main',
                  color: 'white',
                  '&:hover': {
                    bgcolor: 'primary.dark',
                  },
                  '&.Mui-disabled': {
                    bgcolor: 'action.disabledBackground',
                  }
                }}
              >
                {isLoading ? (
                  <CircularProgress size={20} color="inherit" />
                ) : (
                  <SendIcon fontSize="small" />
                )}
              </IconButton>
            </Tooltip>
          </Box>
        </Box>
        
        {isLoading && (
          <Box sx={{ display: 'flex', alignItems: 'center', mt: 2 }}>
            <CircularProgress size={16} sx={{ mr: 1 }} />
            <Typography variant="body2" color="text.secondary">
              Processando seu comando...
            </Typography>
          </Box>
        )}
      </Paper>
    </Box>
  );
}

export default EnhancedCommandInput;

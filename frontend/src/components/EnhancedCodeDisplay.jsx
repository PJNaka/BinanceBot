import React, { useState } from 'react';
import { 
  Box, 
  Paper, 
  Typography, 
  IconButton, 
  Tooltip, 
  Menu, 
  MenuItem,
  Snackbar,
  Alert
} from '@mui/material';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import MoreVertIcon from '@mui/icons-material/MoreVert';
import DownloadIcon from '@mui/icons-material/Download';
import CodeIcon from '@mui/icons-material/Code';
import { Light as SyntaxHighlighter } from 'react-syntax-highlighter';
import { atomOneDark } from 'react-syntax-highlighter/dist/esm/styles/hljs';
import python from 'react-syntax-highlighter/dist/esm/languages/hljs/python';
import javascript from 'react-syntax-highlighter/dist/esm/languages/hljs/javascript';
import json from 'react-syntax-highlighter/dist/esm/languages/hljs/json';
import bash from 'react-syntax-highlighter/dist/esm/languages/hljs/bash';

// Registrar linguagens para o syntax highlighter
SyntaxHighlighter.registerLanguage('python', python);
SyntaxHighlighter.registerLanguage('javascript', javascript);
SyntaxHighlighter.registerLanguage('json', json);
SyntaxHighlighter.registerLanguage('bash', bash);

function EnhancedCodeDisplay({ code }) {
  const [language, setLanguage] = useState('python');
  const [anchorEl, setAnchorEl] = useState(null);
  const [snackbarOpen, setSnackbarOpen] = useState(false);
  const [snackbarMessage, setSnackbarMessage] = useState('');
  const [snackbarSeverity, setSnackbarSeverity] = useState('success');
  
  const open = Boolean(anchorEl);
  
  // Detectar linguagem automaticamente com base no conteúdo
  React.useEffect(() => {
    if (!code) return;
    
    if (code.includes('import React') || code.includes('function(') || code.includes('const ') || code.includes('let ')) {
      setLanguage('javascript');
    } else if (code.includes('import ') && code.includes('def ')) {
      setLanguage('python');
    } else if (code.startsWith('{') || code.startsWith('[')) {
      setLanguage('json');
    } else if (code.includes('#!/bin/bash') || code.includes('apt-get') || code.includes('sudo ')) {
      setLanguage('bash');
    }
  }, [code]);
  
  const handleMenuClick = (event) => {
    setAnchorEl(event.currentTarget);
  };
  
  const handleMenuClose = () => {
    setAnchorEl(null);
  };
  
  const handleLanguageChange = (lang) => {
    setLanguage(lang);
    handleMenuClose();
  };
  
  const handleCopyCode = () => {
    if (!code) return;
    
    navigator.clipboard.writeText(code)
      .then(() => {
        setSnackbarMessage('Código copiado para a área de transferência');
        setSnackbarSeverity('success');
        setSnackbarOpen(true);
      })
      .catch((error) => {
        setSnackbarMessage('Erro ao copiar código');
        setSnackbarSeverity('error');
        setSnackbarOpen(true);
        console.error('Erro ao copiar código:', error);
      });
  };
  
  const handleDownloadCode = () => {
    if (!code) return;
    
    const fileExtension = language === 'python' ? '.py' : 
                         language === 'javascript' ? '.js' : 
                         language === 'json' ? '.json' : '.sh';
    
    const fileName = `code_${new Date().toISOString().replace(/[:.]/g, '-')}${fileExtension}`;
    const blob = new Blob([code], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    
    const a = document.createElement('a');
    a.href = url;
    a.download = fileName;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    setSnackbarMessage(`Código baixado como ${fileName}`);
    setSnackbarSeverity('success');
    setSnackbarOpen(true);
  };
  
  const handleSnackbarClose = (event, reason) => {
    if (reason === 'clickaway') return;
    setSnackbarOpen(false);
  };

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {!code ? (
        <Box sx={{ 
          display: 'flex', 
          flexDirection: 'column', 
          alignItems: 'center', 
          justifyContent: 'center',
          height: '100%',
          opacity: 0.7
        }}>
          <CodeIcon sx={{ fontSize: 40, color: 'text.secondary', mb: 1 }} />
          <Typography variant="body2" color="text.secondary" align="center">
            Nenhum código gerado ainda.
          </Typography>
          <Typography variant="body2" color="text.secondary" align="center">
            O código gerado aparecerá aqui.
          </Typography>
        </Box>
      ) : (
        <>
          <Box sx={{ 
            display: 'flex', 
            justifyContent: 'space-between', 
            alignItems: 'center',
            mb: 1
          }}>
            <Typography variant="body2" color="text.secondary">
              {language === 'python' ? 'Python' : 
               language === 'javascript' ? 'JavaScript' : 
               language === 'json' ? 'JSON' : 'Bash'}
            </Typography>
            
            <Box>
              <Tooltip title="Copiar código">
                <IconButton size="small" onClick={handleCopyCode}>
                  <ContentCopyIcon fontSize="small" />
                </IconButton>
              </Tooltip>
              
              <Tooltip title="Baixar código">
                <IconButton size="small" onClick={handleDownloadCode}>
                  <DownloadIcon fontSize="small" />
                </IconButton>
              </Tooltip>
              
              <Tooltip title="Opções">
                <IconButton
                  size="small"
                  onClick={handleMenuClick}
                  aria-controls={open ? 'language-menu' : undefined}
                  aria-haspopup="true"
                  aria-expanded={open ? 'true' : undefined}
                >
                  <MoreVertIcon fontSize="small" />
                </IconButton>
              </Tooltip>
              
              <Menu
                id="language-menu"
                anchorEl={anchorEl}
                open={open}
                onClose={handleMenuClose}
                MenuListProps={{
                  'aria-labelledby': 'language-button',
                }}
              >
                <MenuItem onClick={() => handleLanguageChange('python')}>Python</MenuItem>
                <MenuItem onClick={() => handleLanguageChange('javascript')}>JavaScript</MenuItem>
                <MenuItem onClick={() => handleLanguageChange('json')}>JSON</MenuItem>
                <MenuItem onClick={() => handleLanguageChange('bash')}>Bash</MenuItem>
              </Menu>
            </Box>
          </Box>
          
          <Paper 
            elevation={0} 
            sx={{ 
              flexGrow: 1, 
              overflow: 'auto',
              borderRadius: 2,
              '&::-webkit-scrollbar': {
                width: '8px',
              },
              '&::-webkit-scrollbar-track': {
                background: '#2d2d2d',
                borderRadius: '0 10px 10px 0',
              },
              '&::-webkit-scrollbar-thumb': {
                background: '#555',
                borderRadius: '10px',
              },
              '&::-webkit-scrollbar-thumb:hover': {
                background: '#777',
              },
            }}
          >
            <SyntaxHighlighter
              language={language}
              style={atomOneDark}
              customStyle={{
                margin: 0,
                padding: '16px',
                borderRadius: '8px',
                fontSize: '0.9rem',
                height: '100%',
              }}
              showLineNumbers={true}
              wrapLines={true}
            >
              {code}
            </SyntaxHighlighter>
          </Paper>
        </>
      )}
      
      <Snackbar 
        open={snackbarOpen} 
        autoHideDuration={3000} 
        onClose={handleSnackbarClose}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert 
          onClose={handleSnackbarClose} 
          severity={snackbarSeverity} 
          variant="filled"
          sx={{ width: '100%' }}
        >
          {snackbarMessage}
        </Alert>
      </Snackbar>
    </Box>
  );
}

export default EnhancedCodeDisplay;

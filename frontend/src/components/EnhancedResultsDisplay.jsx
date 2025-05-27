import React, { useState } from 'react';
import { 
  Box, 
  Paper, 
  Typography, 
  Tabs, 
  Tab, 
  IconButton, 
  Tooltip,
  Button,
  CircularProgress,
  Divider
} from '@mui/material';
import DownloadIcon from '@mui/icons-material/Download';
import ShareIcon from '@mui/icons-material/Share';
import FullscreenIcon from '@mui/icons-material/Fullscreen';
import FullscreenExitIcon from '@mui/icons-material/FullscreenExit';
import RefreshIcon from '@mui/icons-material/Refresh';

function EnhancedResultsDisplay({ results }) {
  const [activeTab, setActiveTab] = useState(0);
  const [isFullscreen, setIsFullscreen] = useState(false);
  
  const handleTabChange = (event, newValue) => {
    setActiveTab(newValue);
  };
  
  const handleFullscreenToggle = () => {
    setIsFullscreen(!isFullscreen);
  };
  
  const handleDownload = () => {
    // Implementação para download dos resultados
    console.log('Download results');
  };
  
  const handleShare = () => {
    // Implementação para compartilhamento dos resultados
    console.log('Share results');
  };
  
  const handleRefresh = () => {
    // Implementação para atualização dos resultados
    console.log('Refresh results');
  };
  
  // Renderiza o conteúdo com base no tipo de resultado
  const renderContent = () => {
    if (!results) {
      return (
        <Box sx={{ 
          display: 'flex', 
          flexDirection: 'column', 
          alignItems: 'center', 
          justifyContent: 'center',
          height: '100%',
          opacity: 0.7
        }}>
          <Typography variant="body2" color="text.secondary" align="center">
            Nenhum resultado disponível.
          </Typography>
          <Typography variant="body2" color="text.secondary" align="center">
            Os resultados da execução aparecerão aqui.
          </Typography>
        </Box>
      );
    }
    
    if (results.status === 'running') {
      return (
        <Box sx={{ 
          display: 'flex', 
          flexDirection: 'column', 
          alignItems: 'center', 
          justifyContent: 'center',
          height: '100%'
        }}>
          <CircularProgress size={40} sx={{ mb: 2 }} />
          <Typography variant="body1" align="center">
            Processando...
          </Typography>
          <Typography variant="body2" color="text.secondary" align="center" sx={{ mt: 1 }}>
            {results.message || 'Executando tarefas no sandbox'}
          </Typography>
        </Box>
      );
    }
    
    if (results.status === 'error') {
      return (
        <Box sx={{ 
          p: 2, 
          bgcolor: 'rgba(239, 68, 68, 0.05)', 
          borderRadius: 2,
          border: '1px solid rgba(239, 68, 68, 0.2)'
        }}>
          <Typography variant="body1" color="error" sx={{ fontWeight: 500, mb: 1 }}>
            Erro na execução
          </Typography>
          <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
            {results.error || 'Ocorreu um erro durante a execução da tarefa.'}
          </Typography>
          {results.suggestion && (
            <Box sx={{ mt: 2, p: 1, bgcolor: 'background.paper', borderRadius: 1 }}>
              <Typography variant="body2" sx={{ fontWeight: 500 }}>
                Sugestão:
              </Typography>
              <Typography variant="body2">
                {results.suggestion}
              </Typography>
            </Box>
          )}
        </Box>
      );
    }
    
    // Resultados bem-sucedidos
    switch (activeTab) {
      case 0: // Visualização principal
        return (
          <Box sx={{ height: '100%', overflow: 'auto' }}>
            <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
              {typeof results.result === 'string' 
                ? results.result 
                : JSON.stringify(results.result, null, 2)}
            </Typography>
          </Box>
        );
      case 1: // Dados
        return (
          <Box sx={{ height: '100%', overflow: 'auto' }}>
            <pre style={{ margin: 0, fontSize: '0.9rem' }}>
              {JSON.stringify(results.data || {}, null, 2)}
            </pre>
          </Box>
        );
      case 2: // Logs
        return (
          <Box sx={{ 
            height: '100%', 
            overflow: 'auto', 
            bgcolor: '#f8f9fa', 
            p: 1, 
            borderRadius: 1,
            fontFamily: 'monospace',
            fontSize: '0.85rem'
          }}>
            {results.logs?.map((log, index) => (
              <div key={index} style={{ marginBottom: '4px' }}>
                {log}
              </div>
            )) || 'Nenhum log disponível.'}
          </Box>
        );
      default:
        return null;
    }
  };

  return (
    <Box 
      sx={{ 
        height: '100%', 
        display: 'flex', 
        flexDirection: 'column',
        ...(isFullscreen && {
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          zIndex: 1300,
          bgcolor: 'background.paper',
          p: 3
        })
      }}
    >
      {results && results.status !== 'running' && (
        <>
          <Box sx={{ 
            display: 'flex', 
            justifyContent: 'space-between', 
            alignItems: 'center',
            mb: 1
          }}>
            <Tabs 
              value={activeTab} 
              onChange={handleTabChange}
              variant="scrollable"
              scrollButtons="auto"
              sx={{
                minHeight: '36px',
                '& .MuiTab-root': {
                  minHeight: '36px',
                  py: 0.5
                }
              }}
            >
              <Tab label="Resultados" />
              <Tab label="Dados" disabled={!results?.data} />
              <Tab label="Logs" disabled={!results?.logs?.length} />
            </Tabs>
            
            <Box>
              <Tooltip title="Atualizar">
                <IconButton size="small" onClick={handleRefresh}>
                  <RefreshIcon fontSize="small" />
                </IconButton>
              </Tooltip>
              
              <Tooltip title="Baixar">
                <IconButton size="small" onClick={handleDownload}>
                  <DownloadIcon fontSize="small" />
                </IconButton>
              </Tooltip>
              
              <Tooltip title="Compartilhar">
                <IconButton size="small" onClick={handleShare}>
                  <ShareIcon fontSize="small" />
                </IconButton>
              </Tooltip>
              
              <Tooltip title={isFullscreen ? "Sair da tela cheia" : "Tela cheia"}>
                <IconButton size="small" onClick={handleFullscreenToggle}>
                  {isFullscreen ? <FullscreenExitIcon fontSize="small" /> : <FullscreenIcon fontSize="small" />}
                </IconButton>
              </Tooltip>
            </Box>
          </Box>
          
          <Divider sx={{ mb: 2 }} />
        </>
      )}
      
      <Box sx={{ flexGrow: 1, overflow: 'auto' }}>
        {renderContent()}
      </Box>
      
      {isFullscreen && (
        <Box sx={{ mt: 2, display: 'flex', justifyContent: 'flex-end' }}>
          <Button 
            variant="outlined" 
            size="small" 
            onClick={handleFullscreenToggle}
            startIcon={<FullscreenExitIcon />}
          >
            Sair da tela cheia
          </Button>
        </Box>
      )}
    </Box>
  );
}

export default EnhancedResultsDisplay;

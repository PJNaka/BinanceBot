import React, { useState, useEffect, useRef } from 'react';
import { Container, Grid, Paper, Typography, Box, Button, CircularProgress, Drawer, AppBar, Toolbar, IconButton, useMediaQuery, useTheme, Fab } from '@mui/material';
import MenuIcon from '@mui/icons-material/Menu';
import CloseIcon from '@mui/icons-material/Close';
import DarkModeIcon from '@mui/icons-material/DarkMode';
import LightModeIcon from '@mui/icons-material/LightMode';
import KeyboardArrowUpIcon from '@mui/icons-material/KeyboardArrowUp';

// Importando componentes aprimorados
import EnhancedCommandInput from './components/EnhancedCommandInput';
import EnhancedAgentThoughts from './components/EnhancedAgentThoughts';
import EnhancedCodeDisplay from './components/EnhancedCodeDisplay';
import EnhancedResultsDisplay from './components/EnhancedResultsDisplay';

// Importando componentes originais
import ScienceDataDisplay from './components/ScienceDataDisplay'; 
import FrontendSandbox from './components/FrontendSandbox'; 
import FrontendSandboxLogs from './components/FrontendSandboxLogs';
import LoginForm from './components/LoginForm';
import RegisterForm from './components/RegisterForm';

// Importando serviços
import { 
    sendGenerateCommand, 
    fetchScienceData, 
    connectWebSocket,
    logoutUser,
    fetchCurrentUser
} from './services/api';

// Função para gerar um ID de cliente único
const generateClientId = () => `client-${Date.now()}-${Math.random().toString(36).substring(2, 7)}`;

function App() {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const isTablet = useMediaQuery(theme.breakpoints.between('sm', 'md'));
  
  // Estados originais
  const [command, setCommand] = useState('');
  const [agentStream, setAgentStream] = useState([]);
  const [generatedCode, setGeneratedCode] = useState('');
  const [sandboxResults, setSandboxResults] = useState(null);
  const [scienceDataList, setScienceDataList] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [clientId, setClientId] = useState('');
  const [frontendHtml, setFrontendHtml] = useState('');
  const [frontendCss, setFrontendCss] = useState('');
  const [frontendJs, setFrontendJs] = useState('');
  const [frontendSandboxLogEntries, setFrontendSandboxLogEntries] = useState([]);
  const [currentUser, setCurrentUser] = useState(null);
  const [isLoadingAuth, setIsLoadingAuth] = useState(true);
  const [showLogin, setShowLogin] = useState(true);
  
  // Novos estados para UI aprimorada
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [darkMode, setDarkMode] = useState(false);
  const [showScrollTop, setShowScrollTop] = useState(false);
  
  const ws = useRef(null);
  const mainContainerRef = useRef(null);

  // Detectar rolagem para mostrar botão de voltar ao topo
  useEffect(() => {
    const handleScroll = () => {
      if (mainContainerRef.current) {
        setShowScrollTop(mainContainerRef.current.scrollTop > 300);
      }
    };
    
    const currentContainer = mainContainerRef.current;
    if (currentContainer) {
      currentContainer.addEventListener('scroll', handleScroll);
    }
    
    return () => {
      if (currentContainer) {
        currentContainer.removeEventListener('scroll', handleScroll);
      }
    };
  }, []);

  // Efeito para inicialização
  useEffect(() => {
    const id = generateClientId();
    setClientId(id);

    // Buscar dados científicos iniciais
    const loadScienceData = async () => {
      try {
        const data = await fetchScienceData();
        setScienceDataList(data);
      } catch (err) {
        setError('Falha ao carregar dados científicos.');
        console.error(err);
      }
    };
    loadScienceData();

    // Verificar autenticação
    const checkAuth = async () => {
      setIsLoadingAuth(true);
      try {
        const user = await fetchCurrentUser(); 
        setCurrentUser(user); 
      } catch (error) {
        setCurrentUser(null); 
      } finally {
        setIsLoadingAuth(false);
      }
    };
    checkAuth();
    
  }, []);

  // Callback para mensagens do FrontendSandbox
  const handleSandboxMessage = (message) => {
    console.log('Mensagem do Frontend Sandbox:', message);
    const timestampedMessage = { 
      ...message, 
      timestamp: new Date().toISOString()
    };
    setFrontendSandboxLogEntries(prevLogs => [...prevLogs, timestampedMessage]);
  };

  // Lógica de conexão WebSocket
  useEffect(() => {
    if (!clientId || !currentUser) {
      if (ws.current && (ws.current.readyState === WebSocket.OPEN || ws.current.readyState === WebSocket.CONNECTING)) {
         console.log("Fechando WebSocket devido a logout ou falta de clientID/currentUser.");
         ws.current.close();
         ws.current = null;
      }
      return;
    }

    if (ws.current && ws.current.readyState === WebSocket.OPEN) {
        console.log("WebSocket já está aberto e conectado para o Usuário:", currentUser.username, "ID do Cliente:", clientId);
        return;
    }
    
    console.log("Tentando conectar WebSocket (Usuário Autenticado):", currentUser.username, "ID do Cliente:", clientId);
    ws.current = connectWebSocket(clientId, (message) => {
      console.log("Mensagem WebSocket recebida por App.jsx:", message);
      setAgentStream(prevStream => [...prevStream, message]);

      // Tratamento de diferentes tipos de mensagens
      if (message.type === 'phase_update') {
        // Atualização de fase
      } else if (message.type === 'code_generated') {
        setGeneratedCode(message.code);
      } else if (message.type === 'test_result') {
        setSandboxResults(message.results);
      } else if (message.type === 'error') {
        setError(message.message);
      } else if (message.type === 'success') {
        if (message.final_output) {
            console.log("Processo do agente bem-sucedido, saída final:", message.final_output);
        }
      } else if (message.type === 'frontend_code_bundle') {
        console.log("Recebido frontend_code_bundle:", message);
        setFrontendHtml(message.html || '');
        setFrontendCss(message.css || '');
        setFrontendJs(message.js || '');
        setFrontendSandboxLogEntries([]);
      } else if (message.type === 'frontend_html_content') {
        console.log("Recebido frontend_html_content:", message);
        setFrontendHtml(message.content || '');
        setFrontendSandboxLogEntries([]);
      } else if (message.type === 'frontend_css_content') {
        console.log("Recebido frontend_css_content:", message);
        setFrontendCss(message.content || '');
      } else if (message.type === 'frontend_js_content') {
        console.log("Recebido frontend_js_content:", message);
        setFrontendJs(message.content || '');
        setFrontendSandboxLogEntries([]);
      }
    });

    return () => {
      if (ws.current && (ws.current.readyState === WebSocket.OPEN || ws.current.readyState === WebSocket.CONNECTING)) {
        console.log("Fechando conexão WebSocket (limpeza de efeito) para ID do Cliente:", clientId, "Usuário:", currentUser?.username);
        ws.current.close();
        ws.current = null;
      }
    };
  }, [clientId, currentUser]);

  // Funções de autenticação
  const handleLoginSuccess = async () => {
    setIsLoadingAuth(true);
    try {
      const user = await fetchCurrentUser();
      setCurrentUser(user);
      setShowLogin(true);
    } catch (error) {
      setCurrentUser(null);
      setError("Falha ao buscar dados do usuário após login.");
    } finally {
      setIsLoadingAuth(false);
    }
  };

  const handleLogout = () => {
    if (ws.current && (ws.current.readyState === WebSocket.OPEN || ws.current.readyState === WebSocket.CONNECTING)) {
      ws.current.close();
      ws.current = null;
      console.log("Conexão WebSocket fechada devido a logout.");
    }
    logoutUser(); 
    setCurrentUser(null);
    setAgentStream([]); 
    setGeneratedCode('');
    setSandboxResults(null);
    setFrontendHtml(''); 
    setFrontendCss('');
    setFrontendJs('');
    setFrontendSandboxLogEntries([]);
    setError('');
  };

  const handleSwitchAuthMode = () => {
    setShowLogin(!showLogin);
    setError('');
  };

  const handleRegistrationSuccess = () => {
    setShowLogin(true);
  };

  // Função para enviar comando
  const handleSubmitCommand = async () => {
    if (!command.trim()) {
      setError('O comando não pode estar vazio.');
      return;
    }
    setIsLoading(true);
    setError('');
    setAgentStream([]);
    setGeneratedCode('');
    setSandboxResults(null);

    try {
      const finalResponse = await sendGenerateCommand(command, clientId);
      console.log('Resposta HTTP final de /generate:', finalResponse);
      
      if(finalResponse.generated_code && !generatedCode) {
          setGeneratedCode(finalResponse.generated_code);
      }
      if(finalResponse.final_output && !sandboxResults) {
          setSandboxResults({ result: finalResponse.final_output, status: "completed_http" });
      }

    } catch (err) {
      console.error('Erro ao enviar comando:', err);
      const errorMsg = err.response?.data?.detail || err.message || 'Falha ao processar comando.';
      setError(errorMsg);
      setAgentStream(prevStream => [...prevStream, {type: "error", phase: "HTTP_REQUEST", message: `Falha no envio do comando: ${errorMsg}`}]);
    } finally {
      setIsLoading(false);
    }
  };

  // Função para alternar o drawer
  const toggleDrawer = () => {
    setDrawerOpen(!drawerOpen);
  };

  // Função para alternar o modo escuro
  const toggleDarkMode = () => {
    setDarkMode(!darkMode);
    // Implementação real exigiria mudança no tema do MUI
  };

  // Função para rolar para o topo
  const scrollToTop = () => {
    if (mainContainerRef.current) {
      mainContainerRef.current.scrollTo({
        top: 0,
        behavior: 'smooth'
      });
    }
  };

  // Renderização condicional para autenticação
  if (isLoadingAuth) {
    return (
      <Container maxWidth="sm" sx={{ mt: 8, textAlign: 'center' }}>
        <CircularProgress size={60} />
        <Typography variant="h6" sx={{ mt: 2 }}>
          Carregando...
        </Typography>
      </Container>
    );
  }

  if (!currentUser) {
    return (
      <Container maxWidth="sm" sx={{ mt: 4, mb: 4 }}>
        <Paper elevation={3} sx={{ p: 4, borderRadius: 2 }}>
          <Typography variant="h4" component="h1" gutterBottom textAlign="center" sx={{ mb: 3 }}>
            {showLogin ? 'Login' : 'Cadastro'}
          </Typography>
          
          {error && (
            <Typography color="error" sx={{ mt: 2, mb: 2, whiteSpace: 'pre-wrap' }}>
              Erro: {error}
            </Typography>
          )}
          
          {showLogin ? (
            <LoginForm onLoginSuccess={handleLoginSuccess} />
          ) : (
            <RegisterForm onRegistrationSuccess={handleRegistrationSuccess} />
          )}
          
          <Box sx={{ mt: 3, textAlign: 'center' }}>
            <Button 
              onClick={handleSwitchAuthMode}
              sx={{ textTransform: 'none' }}
            >
              {showLogin ? 'Não tem uma conta? Cadastre-se' : 'Já tem uma conta? Faça login'}
            </Button>
          </Box>
        </Paper>
      </Container>
    );
  }

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      {/* AppBar */}
      <AppBar position="static" color="default" elevation={1}>
        <Toolbar>
          <IconButton
            edge="start"
            color="inherit"
            aria-label="menu"
            onClick={toggleDrawer}
            sx={{ mr: 2 }}
          >
            <MenuIcon />
          </IconButton>
          
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            BinanceBot - Interface Autônoma
          </Typography>
          
          <IconButton color="inherit" onClick={toggleDarkMode}>
            {darkMode ? <LightModeIcon /> : <DarkModeIcon />}
          </IconButton>
          
          <Button color="inherit" onClick={handleLogout}>
            Sair
          </Button>
        </Toolbar>
      </AppBar>
      
      {/* Drawer para navegação em dispositivos móveis */}
      <Drawer
        anchor="left"
        open={drawerOpen}
        onClose={toggleDrawer}
      >
        <Box
          sx={{ width: 250 }}
          role="presentation"
          onClick={toggleDrawer}
        >
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', p: 2 }}>
            <Typography variant="h6">Menu</Typography>
            <IconButton onClick={toggleDrawer}>
              <CloseIcon />
            </IconButton>
          </Box>
          
          <Box sx={{ p: 2 }}>
            <Typography variant="body1" sx={{ mb: 2 }}>
              Usuário: {currentUser.username}
            </Typography>
            
            <Button 
              variant="contained" 
              color="primary" 
              fullWidth 
              sx={{ mb: 1 }}
              onClick={toggleDrawer}
            >
              Dashboard
            </Button>
            
            <Button 
              variant="outlined" 
              color="primary" 
              fullWidth 
              sx={{ mb: 1 }}
              onClick={handleLogout}
            >
              Sair
            </Button>
          </Box>
        </Box>
      </Drawer>
      
      {/* Conteúdo principal */}
      <Box 
        ref={mainContainerRef}
        component="main" 
        sx={{ 
          flexGrow: 1, 
          p: { xs: 2, sm: 3, md: 4 },
          overflow: 'auto',
          maxHeight: 'calc(100vh - 64px)'
        }}
      >
        <Container maxWidth="lg">
          {/* Input de comando aprimorado */}
          <EnhancedCommandInput
            command={command}
            setCommand={setCommand}
            onSubmit={handleSubmitCommand}
            isLoading={isLoading}
          />
          
          {error && (
            <Paper 
              elevation={0} 
              sx={{ 
                p: 2, 
                mb: 3, 
                bgcolor: 'rgba(239, 68, 68, 0.05)', 
                borderRadius: 2,
                border: '1px solid rgba(239, 68, 68, 0.2)'
              }}
            >
              <Typography color="error" sx={{ whiteSpace: 'pre-wrap' }}>
                Erro: {error}
              </Typography>
            </Paper>
          )}
          
          <Grid container spacing={3}>
            {/* Pensamentos do agente */}
            <Grid item xs={12} md={6}>
              <Paper 
                elevation={2} 
                sx={{ 
                  p: 2, 
                  height: '400px', 
                  borderRadius: 2,
                  display: 'flex',
                  flexDirection: 'column'
                }}
              >
                <Typography variant="h6" gutterBottom>Fluxo de Pensamentos do Agente</Typography>
                <Box sx={{ flexGrow: 1, overflow: 'hidden' }}>
                  <EnhancedAgentThoughts stream={agentStream} />
                </Box>
              </Paper>
            </Grid>
            
            {/* Código gerado */}
            <Grid item xs={12} md={6}>
              <Paper 
                elevation={2} 
                sx={{ 
                  p: 2, 
                  height: '400px', 
                  borderRadius: 2,
                  display: 'flex',
                  flexDirection: 'column'
                }}
              >
                <Typography variant="h6" gutterBottom>Código Gerado</Typography>
                <Box sx={{ flexGrow: 1, overflow: 'hidden' }}>
                  <EnhancedCodeDisplay code={generatedCode} />
                </Box>
              </Paper>
            </Grid>
            
            {/* Resultados do sandbox */}
            <Grid item xs={12} md={6}>
              <Paper 
                elevation={2} 
                sx={{ 
                  p: 2, 
                  height: '300px', 
                  borderRadius: 2,
                  display: 'flex',
                  flexDirection: 'column'
                }}
              >
                <Typography variant="h6" gutterBottom>Resultados do Sandbox</Typography>
                <Box sx={{ flexGrow: 1, overflow: 'hidden' }}>
                  <EnhancedResultsDisplay results={sandboxResults} />
                </Box>
              </Paper>
            </Grid>
            
            {/* Dados científicos */}
            <Grid item xs={12} md={6}>
              <Paper 
                elevation={2} 
                sx={{ 
                  p: 2, 
                  height: '300px', 
                  borderRadius: 2,
                  display: 'flex',
                  flexDirection: 'column'
                }}
              >
                <Typography variant="h6" gutterBottom>Dados Científicos</Typography>
                <Box sx={{ flexGrow: 1, overflow: 'hidden' }}>
                  <ScienceDataDisplay data={scienceDataList} />
                </Box>
              </Paper>
            </Grid>
            
            {/* Frontend Sandbox */}
            <Grid item xs={12} md={6}>
              <Paper 
                elevation={2} 
                sx={{ 
                  p: 2, 
                  height: '400px', 
                  borderRadius: 2,
                  display: 'flex',
                  flexDirection: 'column'
                }}
              >
                <Typography variant="h6" gutterBottom>Frontend Sandbox</Typography>
                <Box 
                  sx={{ 
                    flexGrow: 1, 
                    border: '1px solid #ccc', 
                    borderRadius: 1, 
                    overflow: 'hidden', 
                    bgcolor: 'white' 
                  }}
                >
                  <FrontendSandbox
                    htmlContent={frontendHtml}
                    cssContent={frontendCss}
                    javascriptContent={frontendJs}
                    onSandboxMessage={handleSandboxMessage}
                    parentOrigin={window.location.origin}
                  />
                </Box>
              </Paper>
            </Grid>
            
            {/* Frontend Sandbox Logs */}
            <Grid item xs={12} md={6}>
              <Paper 
                elevation={2} 
                sx={{ 
                  p: 2, 
                  height: '400px', 
                  borderRadius: 2,
                  display: 'flex',
                  flexDirection: 'column'
                }}
              >
                <Typography variant="h6" gutterBottom>Logs do Frontend Sandbox</Typography>
                <Box 
                  sx={{ 
                    flexGrow: 1, 
                    border: '1px solid #ccc', 
                    borderRadius: 1, 
                    overflow: 'hidden', 
                    bgcolor: 'background.paper' 
                  }}
                >
                  <FrontendSandboxLogs logs={frontendSandboxLogEntries} />
                </Box>
              </Paper>
            </Grid>
          </Grid>
        </Container>
      </Box>
      
      {/* Botão de voltar ao topo */}
      {showScrollTop && (
        <Fab 
          color="primary" 
          size="small" 
          aria-label="scroll back to top"
          onClick={scrollToTop}
          sx={{ 
            position: 'fixed', 
            bottom: 16, 
            right: 16,
            zIndex: 1000
          }}
        >
          <KeyboardArrowUpIcon />
        </Fab>
      )}
    </Box>
  );
}

export default App;

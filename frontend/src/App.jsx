import React, { useState, useEffect, useRef } from 'react';
import { Container, Grid, Paper, Typography, Box, Button, CircularProgress } from '@mui/material'; // Added Button, CircularProgress
import CommandInput from './components/CommandInput';
import AgentThoughts from './components/AgentThoughts';
import CodeDisplay from './components/CodeDisplay'; 
import ResultsDisplay from './components/ResultsDisplay'; 
import ScienceDataDisplay from './components/ScienceDataDisplay'; 
import FrontendSandbox from './components/FrontendSandbox'; 
import FrontendSandboxLogs from './components/FrontendSandboxLogs';
import LoginForm from './components/LoginForm'; // Import LoginForm
import RegisterForm from './components/RegisterForm'; // Import RegisterForm
import { 
    sendGenerateCommand, 
    fetchScienceData, 
    connectWebSocket,
    logoutUser,         // Import logoutUser
    fetchCurrentUser    // Import fetchCurrentUser
    // token as currentToken, // Not using direct token export, relying on fetchCurrentUser
} from './services/api';
import './App.css';

// Function to generate a simple unique ID
const generateClientId = () => `client-${Date.now()}-${Math.random().toString(36).substring(2, 7)}`;

function App() {
  const [command, setCommand] = useState('');
  const [agentStream, setAgentStream] = useState([]); // Stores all incoming WebSocket messages
  const [generatedCode, setGeneratedCode] = useState('');
  const [sandboxResults, setSandboxResults] = useState(null);
  const [scienceDataList, setScienceDataList] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [clientId, setClientId] = useState('');

  // State for FrontendSandbox
  const [frontendHtml, setFrontendHtml] = useState('');
  const [frontendCss, setFrontendCss] = useState('');
  const [frontendJs, setFrontendJs] = useState('');
  const [frontendSandboxLogEntries, setFrontendSandboxLogEntries] = useState([]);

  // Auth state
  const [currentUser, setCurrentUser] = useState(null);
  const [isLoadingAuth, setIsLoadingAuth] = useState(true); // For initial auth check
  const [showLogin, setShowLogin] = useState(true); // true for Login, false for Register

  const ws = useRef(null);

  useEffect(() => {
    const id = generateClientId();
    setClientId(id);

    // Fetch initial science data
    const loadScienceData = async () => {
      try {
        const data = await fetchScienceData();
        setScienceDataList(data);
      } catch (err) {
        setError('Failed to load science data.');
        console.error(err);
      }
    };
    loadScienceData();

    // Example initial content for testing FrontendSandbox (can be removed after backend sends real data)
    // console.log("Setting initial test content for FrontendSandbox");
    // setFrontendHtml('<h1>Hello from Frontend Sandbox!</h1><button onclick="console.log(\'Button clicked from iframe!\')">Click me in iframe</button><div id="testdiv"></div>');
    // setFrontendCss('body { background-color: #f0f8ff; color: darkblue; } h1 { font-style: italic; } button { padding: 5px; background-color: lightgreen; }');
    // setFrontendJs('console.log("JavaScript executed in frontend sandbox!"); console.warn("A warning from sandbox."); setTimeout(() => { try { document.getElementById("testdiv").innerText = "Async op complete!"; nonExistentFunc(); } catch(e) { console.error("Simulated error in sandbox:", e); } }, 1000); Promise.reject("Simulated unhandled promise rejection");');
    // setFrontendSandboxLogEntries([]); // Clear logs on new content set by this test

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
    
  }, []); // Run only once on mount


  // Callback for messages from FrontendSandbox iframe
  const handleSandboxMessage = (message) => {
    console.log('Message from Frontend Sandbox:', message);
    const timestampedMessage = { 
      ...message, 
      timestamp: new Date().toISOString() // Add timestamp here
    };
    setFrontendSandboxLogEntries(prevLogs => [...prevLogs, timestampedMessage]);
  };

  // WebSocket connection logic
  useEffect(() => {
    if (!clientId || !currentUser) { // DON'T CONNECT IF NOT LOGGED IN or no clientID
      if (ws.current && (ws.current.readyState === WebSocket.OPEN || ws.current.readyState === WebSocket.CONNECTING)) {
         console.log("Closing WebSocket due to user logout or missing clientID/currentUser.");
         ws.current.close();
         ws.current = null; // Ensure ref is cleared after closing
      }
      return; // Exit if no clientID or not logged in
    }

    // If ws.current already exists and is open, don't reconnect (unless clientId/currentUser changed, handled by deps)
    if (ws.current && ws.current.readyState === WebSocket.OPEN) {
        console.log("WebSocket already open and connected for User:", currentUser.username, "Client ID:", clientId);
        return;
    }
    
    console.log("Attempting to connect WebSocket (User Authenticated):", currentUser.username, "Client ID:", clientId);
    // connectWebSocket in api.js now uses the token from its module scope (set during login)
    ws.current = connectWebSocket(clientId, (message) => {
      console.log("WebSocket message received by App.jsx:", message);
      setAgentStream(prevStream => [...prevStream, message]);

      // Example of how to handle different message types from backend
      if (message.type === 'phase_update') {
        // Could update a specific "current phase" state or just log it in thoughts
      } else if (message.type === 'code_generated') { // Backend Python code
        setGeneratedCode(message.code);
      } else if (message.type === 'test_result') { // Backend Python code execution results
        setSandboxResults(message.results);
      } else if (message.type === 'error') { // Agent/Process level errors
        setError(message.message);
      } else if (message.type === 'success') { // Handle success message from agent
        if (message.final_output) {
            console.log("Agent process successful, final output:", message.final_output);
        }
      } else if (message.type === 'frontend_code_bundle') { // New message type for frontend code
        console.log("Received frontend_code_bundle:", message);
        setFrontendHtml(message.html || '');
        setFrontendCss(message.css || '');
        setFrontendJs(message.js || '');
        setFrontendSandboxLogEntries([]); // Clear previous logs for new content
      } else if (message.type === 'frontend_html_content') {
        console.log("Received frontend_html_content:", message);
        setFrontendHtml(message.content || '');
        setFrontendSandboxLogEntries([]);
      } else if (message.type === 'frontend_css_content') {
        console.log("Received frontend_css_content:", message);
        setFrontendCss(message.content || '');
      } else if (message.type === 'frontend_js_content') {
        console.log("Received frontend_js_content:", message);
        setFrontendJs(message.content || '');
        setFrontendSandboxLogEntries([]);
      } else if (message.type === 'agent_action' && message.action === 'web_search') {
        // Message structure: { type: 'agent_action', action: 'web_search', query: 'search query', phase: 'current_phase' }
        console.log("Received agent_action (web_search):", message);
        // The message itself is already added to agentStream by the generic handler.
        // No specific state update needed here beyond what AgentThoughts will render.
      } else if (message.type === 'search_results') {
        // Message structure: { type: 'search_results', results: [...], message: 'Web search completed.', phase: 'current_phase' }
        console.log("Received search_results:", message);
        // The message itself is already added to agentStream.
        // AgentThoughts will be responsible for displaying this.
      } else if (message.type === 'agent_action' && message.action === 'fetch_url') {
        // Message structure: { type: 'agent_action', action: 'fetch_url', url: 'url_to_fetch', phase: 'current_phase' }
        console.log("Received agent_action (fetch_url):", message);
        // Added to agentStream by the generic handler below.
      } else if (message.type === 'url_fetch_result') {
        // Message structure: { type: 'url_fetch_result', url: 'url', content_snippet: '...', error: '...', phase: 'current_phase' }
        console.log("Received url_fetch_result:", message);
        // Added to agentStream by the generic handler below.
      }
      // All messages are added to agentStream by the line:
      // setAgentStream(prevStream => [...prevStream, message]);
      // which should be located just before or after this block.
    });

    return () => {
      if (ws.current && (ws.current.readyState === WebSocket.OPEN || ws.current.readyState === WebSocket.CONNECTING)) {
        console.log("Closing WebSocket connection (cleanup effect) for Client ID:", clientId, "User:", currentUser?.username);
        ws.current.close();
        ws.current = null;
      }
    };
  }, [clientId, currentUser]); // Add currentUser as dependency


  const handleLoginSuccess = async () => {
    setIsLoadingAuth(true);
    try {
      const user = await fetchCurrentUser();
      setCurrentUser(user);
      setShowLogin(true); // Should already be true if login form was shown, ensures main app view
    } catch (error) {
      setCurrentUser(null);
      setError("Failed to fetch user data after login.");
    } finally {
      setIsLoadingAuth(false);
    }
  };

  const handleLogout = () => {
    if (ws.current && (ws.current.readyState === WebSocket.OPEN || ws.current.readyState === WebSocket.CONNECTING)) {
      ws.current.close();
      ws.current = null; // Clear the ref
      console.log("WebSocket connection closed due to logout.");
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
    setError(''); // Clear any general errors
    // ClientID can remain. New WS connection on next login will use it.
  };

  const handleSwitchAuthMode = () => {
    setShowLogin(!showLogin);
    setError(''); // Clear errors when switching forms
  };

  const handleRegistrationSuccess = () => {
    // alert("Registration successful! Please login."); // Using Typography for messages now
    setShowLogin(true); // Switch to login form
    // Error state is already cleared in RegisterForm on success
  };

  const handleSubmitCommand = async () => {
    if (!command.trim()) {
      setError('Command cannot be empty.');
      return;
    }
    setIsLoading(true);
    setError('');
    setAgentStream([]); // Clear previous stream
    setGeneratedCode('');
    setSandboxResults(null);
    // Clear frontend sandbox content on new command if desired, or let it persist
    // setFrontendHtml('');
    // setFrontendCss('');
    // setFrontendJs('');
    // setFrontendSandboxLogEntries([]);


    try {
      const finalResponse = await sendGenerateCommand(command, clientId);
      // The final HTTP response might confirm completion or provide final summary.
      // Most detailed updates are expected via WebSocket.
      console.log('Final HTTP response from /generate:', finalResponse);
      // Optionally, update state based on finalResponse if it contains data not sent via WS
      // e.g., if code generation happens synchronously before WS updates for it.
      if(finalResponse.generated_code && !generatedCode) {
          setGeneratedCode(finalResponse.generated_code);
      }
      if(finalResponse.final_output && !sandboxResults) { // If final output is part of HTTP response
          setSandboxResults({ result: finalResponse.final_output, status: "completed_http" });
      }


    } catch (err) {
      console.error('Error submitting command:', err);
      const errorMsg = err.response?.data?.detail || err.message || 'Failed to process command.';
      setError(errorMsg);
      // Also send this error to the agent stream for display
      setAgentStream(prevStream => [...prevStream, {type: "error", phase: "HTTP_REQUEST", message: `Command submission failed: ${errorMsg}`}]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Paper elevation={3} sx={{ p: 3, borderRadius: 2 }}>
        <Typography variant="h4" component="h1" gutterBottom textAlign="center">
          Autonomous Agent UI
        </Typography>
        
        <CommandInput
          command={command}
          setCommand={setCommand}
          onSubmit={handleSubmitCommand}
          isLoading={isLoading}
        />

        {error && (
          <Typography color="error" sx={{ mt: 2, whiteSpace: 'pre-wrap' }}>
            Error: {error}
          </Typography>
        )}

        <Grid container spacing={3} sx={{ mt: 2 }}>
          <Grid item xs={12} md={6}>
            <Paper elevation={2} sx={{ p: 2, height: '400px', overflowY: 'auto' }}>
              <Typography variant="h6">Agent Thoughts & Stream</Typography>
              <AgentThoughts stream={agentStream} />
            </Paper>
          </Grid>
          <Grid item xs={12} md={6}>
            <Paper elevation={2} sx={{ p: 2, height: '400px', overflowY: 'auto' }}>
              <Typography variant="h6">Generated Code</Typography>
              <CodeDisplay code={generatedCode} />
            </Paper>
          </Grid>
          <Grid item xs={12} md={6}>
            <Paper elevation={2} sx={{ p: 2, height: '300px', overflowY: 'auto' }}>
              <Typography variant="h6">Sandbox Results</Typography>
              <ResultsDisplay results={sandboxResults} />
            </Paper>
          </Grid>
          <Grid item xs={12} md={6}>
            <Paper elevation={2} sx={{ p: 2, height: '300px', overflowY: 'auto' }}>
              <Typography variant="h6">Science Data</Typography>
              <ScienceDataDisplay data={scienceDataList} />
            </Paper>
          </Grid>

          {/* Frontend Sandbox Display */}
          <Grid item xs={12} md={6}>
            <Paper elevation={2} sx={{ p: 2, height: '400px', display: 'flex', flexDirection: 'column' }}>
              <Typography variant="h6">Frontend Sandbox</Typography>
              <Box sx={{ flexGrow: 1, border: '1px solid #ccc', borderRadius: 1, overflow: 'hidden', mt: 1, backgroundColor: 'white' }}>
                <FrontendSandbox
                  htmlContent={frontendHtml}
                  cssContent={frontendCss}
                  javascriptContent={frontendJs}
                  onSandboxMessage={handleSandboxMessage}
                  parentOrigin={window.location.origin} // Crucial for postMessage security
                  // sandboxPolicy="allow-scripts allow-modals allow-popups" // Example if more permissions needed
                />
              </Box>
            </Paper>
          </Grid>

          {/* Frontend Sandbox Logs */}
          <Grid item xs={12} md={6}>
            <Paper elevation={2} sx={{ p: 2, height: '400px', display: 'flex', flexDirection: 'column' }}>
              <Typography variant="h6" gutterBottom>Frontend Sandbox Logs</Typography>
              <Box sx={{ flexGrow: 1, border: '1px solid #ccc', borderRadius: 1, overflow: 'hidden', backgroundColor: 'background.paper' }}>
                <FrontendSandboxLogs logs={frontendSandboxLogEntries} />
              </Box>
            </Paper>
          </Grid>

        </Grid>
      </Paper>
    </Container>
  );
}
export default App;

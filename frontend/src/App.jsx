import React, { useState, useEffect, useRef } from 'react';
import { Container, Grid, Paper, Typography, Box, List, ListItem, ListItemText } from '@mui/material'; // Added List, ListItem, ListItemText
import CommandInput from './components/CommandInput';
import AgentThoughts from './components/AgentThoughts';
import CodeDisplay from './components/CodeDisplay'; 
import ResultsDisplay from './components/ResultsDisplay'; 
import ScienceDataDisplay from './components/ScienceDataDisplay'; 
import FrontendSandbox from './components/FrontendSandbox'; 
import FrontendSandboxLogs from './components/FrontendSandboxLogs'; // Import FrontendSandboxLogs
import { sendGenerateCommand, fetchScienceData, connectWebSocket } from './services/api';
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

  useEffect(() => {
    if (!clientId) return; // Don't connect if no clientId yet

    console.log("Attempting to connect WebSocket with Client ID:", clientId);
    ws.current = connectWebSocket(clientId, (message) => {
      console.log("WebSocket message received:", message);
      setAgentStream(prevStream => [...prevStream, message]); // Add new message to stream

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
        // Note: CSS changes alone might not trigger iframeKey update if JS/HTML are main drivers.
        // Consider if iframeKey logic needs to be more nuanced or if CSS is always bundled.
      } else if (message.type === 'frontend_js_content') {
        console.log("Received frontend_js_content:", message);
        setFrontendJs(message.content || '');
        setFrontendSandboxLogEntries([]);
      }
    });

    return () => {
      if (ws.current) {
        console.log("Closing WebSocket connection for Client ID:", clientId);
        ws.current.close();
      }
    };
  }, [clientId]); // Reconnect if clientId changes (should not happen often)


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

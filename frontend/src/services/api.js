import axios from 'axios';

const apiClient = axios.create({
  baseURL: 'http://localhost:8000', // Adjust if your backend runs elsewhere
});

export const sendGenerateCommand = async (command, clientId) => {
  try {
    const response = await apiClient.post('/generate', { command, client_id: clientId });
    return response.data;
  } catch (error) {
    console.error('Error sending generate command:', error);
    throw error;
  }
};

export const fetchScienceData = async () => {
  try {
    const response = await apiClient.get('/science-data');
    return response.data;
  } catch (error) {
    console.error('Error fetching science data:', error);
    throw error;
  }
};

export const connectWebSocket = (clientId, onMessageCallback) => {
  const wsUrl = `ws://localhost:8000/ws/agent-updates/${clientId}`;
  const socket = new WebSocket(wsUrl);

  socket.onopen = () => {
    console.log(`WebSocket connected for client: ${clientId}`);
  };

  socket.onmessage = (event) => {
    try {
      const message = JSON.parse(event.data);
      onMessageCallback(message);
    } catch (error) {
      console.error('Error parsing WebSocket message:', error);
      // Handle non-JSON messages or log them
      // onMessageCallback({ type: 'raw', data: event.data });
    }
  };

  socket.onerror = (error) => {
    console.error('WebSocket error:', error);
  };

  socket.onclose = (event) => {
    console.log(`WebSocket disconnected for client: ${clientId}. Code: ${event.code}, Reason: ${event.reason}`);
  };

  return socket; // Return the socket instance for potential external management (e.g., closing)
};

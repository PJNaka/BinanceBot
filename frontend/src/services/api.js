import axios from 'axios';

const apiClient = axios.create({
  baseURL: 'http://localhost:8000', // Backend URL
});

// --- Token Management ---
let token = localStorage.getItem('authToken'); // Load token from localStorage

export const setAuthToken = (newToken) => {
  token = newToken; // Update in-memory token
  if (newToken) {
    localStorage.setItem('authToken', newToken);
    apiClient.defaults.headers.common['Authorization'] = `Bearer ${newToken}`;
  } else {
    localStorage.removeItem('authToken');
    delete apiClient.defaults.headers.common['Authorization'];
  }
};

// Initialize Authorization header if token exists on page load
if (token) {
  apiClient.defaults.headers.common['Authorization'] = `Bearer ${token}`;
}

// --- Auth API Calls ---
export const registerUser = async (userData) => { // {username, email, password}
  try {
    const response = await apiClient.post('/auth/register', userData);
    return response.data;
  } catch (error) {
    console.error('Error during registration:', error.response?.data || error.message);
    // Rethrow a more structured error or the specific detail from backend
    const errDetail = error.response?.data?.detail || 'Registration failed due to an unexpected error.';
    throw new Error(errDetail); 
  }
};

export const loginUser = async (credentials) => { // {username, password}
  try {
    const formData = new FormData();
    formData.append('username', credentials.username);
    formData.append('password', credentials.password);

    const response = await apiClient.post('/auth/token', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    
    if (response.data.access_token) {
      setAuthToken(response.data.access_token); // Store token
    }
    return response.data; // {access_token, token_type}
  } catch (error) {
    console.error('Error during login:', error.response?.data || error.message);
    setAuthToken(null); // Clear token on login failure
    const errDetail = error.response?.data?.detail || 'Login failed due to an unexpected error.';
    throw new Error(errDetail);
  }
};

export const logoutUser = () => {
     setAuthToken(null); // Clear token and remove from localStorage
     // Optionally, could also call a backend /auth/logout endpoint if it exists
     // and performs server-side session invalidation. For now, client-side only.
     // console.log("User logged out, token cleared.");
};

export const fetchCurrentUser = async () => {
  if (!token) { // Use the in-memory token variable that's kept in sync
    // console.log("fetchCurrentUser: No token available.");
    return null;
  }
  try {
    const response = await apiClient.get('/auth/users/me');
    return response.data; // User object
  } catch (error) {
    console.error('Error fetching current user:', error.response?.data || error.message);
    if (error.response?.status === 401) { // Unauthorized or token expired
        setAuthToken(null); // Token is invalid/expired, clear it
    }
    // Do not throw generic new Error, let specific error pass or rethrow backend error
    // This allows components to check error.response.status for specific handling if needed
    throw error.response?.data || new Error('Failed to fetch user details.');
  }
};

// --- Existing API Calls (ensure they use the configured apiClient) ---
// sendGenerateCommand and fetchScienceData are assumed to be correctly using apiClient already.
// If they were defined in this file, they would naturally use it.
// If they are imported from elsewhere and don't use this apiClient, that's a larger refactor.
// For this task, we assume they are fine or will be updated if part of this file.

export const sendGenerateCommand = async (command, clientId) => {
  // This function was previously defined in App.jsx or similar.
  // It should now use the global apiClient.
  if (!token) {
    throw new Error("Authentication token not found. Please login.");
  }
  try {
    // The backend's /generate endpoint now expects client_id in the body.
    // The actual user_id is derived from the JWT token on the backend.
    const response = await apiClient.post('/generate', { command, client_id: clientId });
    return response.data;
  } catch (error) {
    console.error('Error sending generate command:', error.response?.data || error.message);
    if (error.response?.status === 401) {
        setAuthToken(null); // Token might be invalid/expired
    }
    throw error.response?.data || new Error('Failed to send generate command.');
  }
};

export const fetchScienceData = async () => {
  // Assumed to use apiClient. If not, needs to be updated.
  try {
    const response = await apiClient.get('/science-data');
    return response.data;
  } catch (error) {
    console.error('Error fetching science data:', error.response?.data || error.message);
    // No specific auth error handling here unless /science-data becomes protected
    throw error.response?.data || new Error('Failed to fetch science data.');
  }
};

export const connectWebSocket = (clientId, onMessageCallback) => {
    // Use the in-memory token, which is kept up-to-date by setAuthToken
    if (!token) {
        console.warn("WebSocket connection: No auth token available. Connection might be rejected by backend.");
        // Optionally, prevent connection entirely or let backend handle rejection
        // For this implementation, we'll attempt connection and let backend reject.
        // However, it's better to not attempt if token is mandatory.
        // For now, we proceed but the backend is expected to close if token is invalid/missing.
    }
    
    // Append token as a query parameter for WebSocket authentication
    const wsUrl = `ws://localhost:8000/ws/agent-updates/${clientId}?token=${encodeURIComponent(token || '')}`;
    
    const socket = new WebSocket(wsUrl);

    socket.onopen = () => {
        console.log(`WebSocket connected for client: ${clientId} with token (presence: ${!!token})`);
    };

    socket.onmessage = (event) => {
        try {
            const message = JSON.parse(event.data);
            onMessageCallback(message);
        } catch (error) {
            console.error('Error parsing WebSocket message:', error);
            // onMessageCallback({ type: 'raw', data: event.data }); // If raw data handling is needed
        }
    };

    socket.onerror = (error) => {
        console.error('WebSocket error:', error);
        // Potentially call onMessageCallback with an error object if needed by UI
        // onMessageCallback({type: 'ws_error', error: 'WebSocket connection error'});
    };

    socket.onclose = (event) => {
        console.log(`WebSocket disconnected for client: ${clientId}. Code: ${event.code}, Reason: ${event.reason}, Clean: ${event.wasClean}`);
        // Potentially call onMessageCallback with a close event if needed by UI
        // onMessageCallback({type: 'ws_close', code: event.code, reason: event.reason});
    };

    return socket; // Return the socket instance
};

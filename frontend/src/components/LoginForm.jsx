// frontend/src/components/LoginForm.jsx
import React, { useState } from 'react';
import { TextField, Button, Box, Typography, Paper } from '@mui/material';
import { loginUser } from '../services/api'; // Adjust path as necessary

function LoginForm({ onLoginSuccess, onSwitchToRegister }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError('');
    try {
      const data = await loginUser({ username, password }); // loginUser from api.js
      if (onLoginSuccess && data.access_token) { // Ensure onLoginSuccess is called only if token received
        onLoginSuccess(data.access_token); 
      } else if (!data.access_token) {
        setError('Login successful, but no access token received.'); // Should not happen with correct backend
      }
    } catch (err) {
      // err.detail is common from FastAPI validation, err.message for others
      setError(err.detail || err.message || 'Login failed. Please check credentials.');
    }
  };

  return (
    <Paper elevation={3} sx={{ p: 4, mt: 4, maxWidth: 400, mx: 'auto' }}>
      <Box component="form" onSubmit={handleSubmit} noValidate>
        <Typography variant="h5" component="h1" gutterBottom textAlign="center">
          Login
        </Typography>
        <TextField
          margin="normal" required fullWidth id="login-username" // Unique ID
          label="Username" name="username" autoComplete="username"
          value={username} onChange={(e) => setUsername(e.target.value)}
        />
        <TextField
          margin="normal" required fullWidth name="password"
          label="Password" type="password" id="login-password" // Unique ID
          autoComplete="current-password"
          value={password} onChange={(e) => setPassword(e.target.value)}
        />
        {error && (
          <Typography color="error" variant="body2" sx={{ mt: 1 }}>
            {error}
          </Typography>
        )}
        <Button type="submit" fullWidth variant="contained" sx={{ mt: 3, mb: 2 }}>
          Sign In
        </Button>
        <Button fullWidth onClick={onSwitchToRegister}>
          Don't have an account? Register
        </Button>
      </Box>
    </Paper>
  );
}
export default LoginForm;

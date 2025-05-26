// frontend/src/components/RegisterForm.jsx
import React, { useState } from 'react';
import { TextField, Button, Box, Typography, Paper } from '@mui/material';
import { registerUser } from '../services/api'; // Adjust path as necessary

function RegisterForm({ onRegisterSuccess, onSwitchToLogin }) {
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError('');
    setSuccessMessage('');
    if (password.length < 6) { // Basic validation example
        setError("Password must be at least 6 characters long.");
        return;
    }
    try {
      await registerUser({ username, email, password }); // registerUser from api.js
      setSuccessMessage('Registration successful! Please login.');
      // Optionally, call onRegisterSuccess or redirect/switch to login
      if(onRegisterSuccess) {
        // Delay switching to login to allow user to see success message
        setTimeout(() => {
            onRegisterSuccess(); 
            if(onSwitchToLogin) onSwitchToLogin(); // Optionally switch view after success
        }, 2000); // 2 seconds delay
      }
    } catch (err) {
      // err.detail is common from FastAPI validation, err.message for others
      setError(err.detail || err.message || 'Registration failed. Please try again.');
    }
  };

  return (
    <Paper elevation={3} sx={{ p: 4, mt: 4, maxWidth: 400, mx: 'auto' }}>
      <Box component="form" onSubmit={handleSubmit} noValidate>
        <Typography variant="h5" component="h1" gutterBottom textAlign="center">
          Register
        </Typography>
        <TextField 
            margin="normal" required fullWidth id="register-username" // Unique ID
            label="Username" name="username" autoComplete="username"
            value={username} onChange={(e) => setUsername(e.target.value)} 
        />
        <TextField 
            margin="normal" required fullWidth id="register-email" // Unique ID
            label="Email Address" name="email" type="email" autoComplete="email"
            value={email} onChange={(e) => setEmail(e.target.value)} 
        />
        <TextField 
            margin="normal" required fullWidth name="password" 
            label="Password" type="password" id="register-password" // Unique ID
            autoComplete="new-password"
            value={password} onChange={(e) => setPassword(e.target.value)} 
        />
        
        {error && <Typography color="error" variant="body2" sx={{ mt: 1 }}>{error}</Typography>}
        {successMessage && <Typography color="primary.main" variant="body2" sx={{ mt: 1 }}>{successMessage}</Typography>} 
        {/* Changed color to primary.main for success */}
        
        <Button type="submit" fullWidth variant="contained" sx={{ mt: 3, mb: 2 }}>
          Register
        </Button>
        <Button fullWidth onClick={onSwitchToLogin}>
          Already have an account? Login
        </Button>
      </Box>
    </Paper>
  );
}
export default RegisterForm;

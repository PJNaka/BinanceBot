import React from 'react';
import { TextField, Button, Box } from '@mui/material';

function CommandInput({ command, setCommand, onSubmit, isLoading }) {
  const handleInputChange = (event) => {
    setCommand(event.target.value);
  };

  const handleSubmit = (event) => {
    event.preventDefault(); // Prevent default form submission if it were a form
    onSubmit();
  };

  return (
    <Box component="form" onSubmit={handleSubmit} sx={{ display: 'flex', gap: 1, alignItems: 'center', mt: 2 }}>
      <TextField
        label="Enter your command"
        variant="outlined"
        fullWidth
        value={command}
        onChange={handleInputChange}
        disabled={isLoading}
      />
      <Button
        variant="contained"
        color="primary"
        onClick={handleSubmit} // Using onClick as Box is not a native form for onSubmit trigger by Enter key naturally
        disabled={isLoading}
        sx={{whiteSpace: 'nowrap'}}
      >
        {isLoading ? 'Processing...' : 'Submit Command'}
      </Button>
    </Box>
  );
}
export default CommandInput;

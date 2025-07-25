import React, { useState, useEffect } from 'react';
import { Container, Grid, Paper, Typography, Box, AppBar, Toolbar, CircularProgress, List, ListItem, ListItemText, Button } from '@mui/material';

function App() {
  const [locations, setLocations] = useState([]);
  const [userLocation, setUserLocation] = useState(null);
  const [installPrompt, setInstallPrompt] = useState(null);

  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const handler = (e) => {
      e.preventDefault();
      setInstallPrompt(e);
    };
    window.addEventListener('beforeinstallprompt', handler);

    return () => {
      window.removeEventListener('beforeinstallprompt', handler);
    };
  }, []);

  useEffect(() => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition((position) => {
        setUserLocation({
          lat: position.coords.latitude,
          lon: position.coords.longitude,
        });
      });
    }
  }, []);

  const [error, setError] = useState(null);

  useEffect(() => {
    if (userLocation) {
      fetch(`https://api.iavibra.com/proximity?lat=${userLocation.lat}&lon=${userLocation.lon}`)
        .then((response) => {
          if (!response.ok) {
            throw new Error('Network response was not ok');
          }
          return response.json();
        })
        .then((data) => {
          setLocations(data);
          setLoading(false);
        })
        .catch((error) => {
          setError(error);
          setLoading(false);
        });
    }
  }, [userLocation]);

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      <AppBar position="static" color="default" elevation={1}>
        <Toolbar>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            PWA de Proximidade
          </Typography>
          {installPrompt && (
            <Button
              color="primary"
              variant="contained"
              onClick={() => installPrompt.prompt()}
            >
              Instalar
            </Button>
          )}
        </Toolbar>
      </AppBar>
      
      <Box 
        component="main" 
        sx={{ 
          flexGrow: 1, 
          p: { xs: 2, sm: 3, md: 4 },
          overflow: 'auto',
        }}
      >
        <Container maxWidth="lg">
          <Grid container spacing={3}>
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
                <Typography variant="h6" gutterBottom>Mapa</Typography>
                <Box sx={{ flexGrow: 1, backgroundColor: '#eee' }} />
              </Paper>
            </Grid>
            
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
                <Typography variant="h6" gutterBottom>Locais Próximos</Typography>
                <Box sx={{ flexGrow: 1, overflow: 'auto' }}>
                  {loading && <CircularProgress />}
                  {error && <Typography color="error">Erro: {error.message}</Typography>}
                  {!loading && !error && (
                    <List>
                      {locations.map((location) => (
                        <ListItem key={location.id}>
                          <ListItemText primary={location.name} />
                        </ListItem>
                      ))}
                    </List>
                  )}
                </Box>
              </Paper>
            </Grid>
          </Grid>
        </Container>
      </Box>
    </Box>
  );
}

export default App;

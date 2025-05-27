import { createTheme } from '@mui/material/styles';

// Criando um tema personalizado conforme os requisitos
const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#2563EB', // Cor de acento para botões conforme especificado
      light: '#3b82f6',
      dark: '#1d4ed8',
      contrastText: '#FFFFFF',
    },
    secondary: {
      main: '#10B981', // Verde para elementos secundários
      light: '#34D399',
      dark: '#059669',
      contrastText: '#FFFFFF',
    },
    background: {
      default: '#F3F4F6', // Cor de fundo conforme especificado
      paper: '#FFFFFF',   // Cor para áreas de conteúdo
    },
    text: {
      primary: '#111827',
      secondary: '#4B5563',
    },
    error: {
      main: '#EF4444',
    },
    warning: {
      main: '#F59E0B',
    },
    info: {
      main: '#3B82F6',
    },
    success: {
      main: '#10B981',
    },
  },
  typography: {
    fontFamily: '"Inter", "Poppins", "Roboto", "Helvetica", "Arial", sans-serif',
    fontSize: 16, // Tamanho base de fonte conforme especificado
    h1: {
      fontSize: '2.5rem',
      fontWeight: 600,
    },
    h2: {
      fontSize: '2rem',
      fontWeight: 600,
    },
    h3: {
      fontSize: '1.75rem',
      fontWeight: 600,
    },
    h4: {
      fontSize: '1.5rem', // 24px conforme especificado para cabeçalhos
      fontWeight: 600,
    },
    h5: {
      fontSize: '1.25rem',
      fontWeight: 600,
    },
    h6: {
      fontSize: '1rem',
      fontWeight: 600,
    },
    body1: {
      fontSize: '1rem', // 16px conforme especificado para corpo
    },
    body2: {
      fontSize: '0.875rem',
    },
    button: {
      textTransform: 'none', // Evita texto em maiúsculas nos botões
      fontWeight: 500,
    },
  },
  shape: {
    borderRadius: 8, // Bordas arredondadas para elementos
  },
  shadows: [
    'none',
    '0px 2px 4px rgba(0, 0, 0, 0.05)',
    '0px 4px 6px rgba(0, 0, 0, 0.05)',
    '0px 6px 8px rgba(0, 0, 0, 0.05)',
    '0px 8px 12px rgba(0, 0, 0, 0.05)',
    '0px 12px 16px rgba(0, 0, 0, 0.05)',
    // ... outros níveis de sombra
  ],
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          padding: '8px 16px',
          boxShadow: '0px 2px 4px rgba(0, 0, 0, 0.05)',
          transition: 'all 0.3s ease', // Animação suave para hover
          '&:hover': {
            transform: 'translateY(-2px)',
            boxShadow: '0px 4px 8px rgba(0, 0, 0, 0.1)',
          },
        },
        contained: {
          background: 'linear-gradient(45deg, #2563EB 30%, #3B82F6 90%)', // Gradiente sutil
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          boxShadow: '0px 4px 12px rgba(0, 0, 0, 0.05)',
          transition: 'box-shadow 0.3s ease',
          '&:hover': {
            boxShadow: '0px 6px 16px rgba(0, 0, 0, 0.08)',
          },
        },
        elevation2: {
          background: 'linear-gradient(to bottom, #FFFFFF, #F9FAFB)',
        },
      },
    },
    MuiTextField: {
      styleOverrides: {
        root: {
          '& .MuiOutlinedInput-root': {
            borderRadius: 8,
            transition: 'all 0.3s ease',
            '&:hover': {
              boxShadow: '0px 2px 4px rgba(0, 0, 0, 0.05)',
            },
            '&.Mui-focused': {
              boxShadow: '0px 4px 8px rgba(0, 0, 0, 0.08)',
            },
          },
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 12,
          overflow: 'hidden',
        },
      },
    },
    MuiTooltip: {
      styleOverrides: {
        tooltip: {
          backgroundColor: 'rgba(17, 24, 39, 0.9)',
          borderRadius: 6,
          fontSize: '0.75rem',
          padding: '8px 12px',
        },
      },
    },
  },
});

export default theme;

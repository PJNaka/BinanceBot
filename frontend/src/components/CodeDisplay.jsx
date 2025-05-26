// frontend/src/components/CodeDisplay.jsx
import React from 'react';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism'; // A popular style
// Or: import { materialLight } from 'react-syntax-highlighter/dist/esm/styles/prism';
// Or: import { okaidia } from 'react-syntax-highlighter/dist/esm/styles/prism';

import { Paper, Typography } from '@mui/material';

function CodeDisplay({ code, language = 'python' }) { // Default language to python
  if (!code || code.trim() === '') {
    return (
      <Paper elevation={0} sx={{ p: 2, backgroundColor: '#f5f5f5', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <Typography variant="body2" sx={{ color: '#666' }}>
          {language === 'log' ? "// No logs/output to display" : "// No code generated yet"}
        </Typography>
      </Paper>
    );
  }

  // If language is 'log', display as plain text without syntax highlighting but preserve formatting
  if (language === 'log') {
    return (
      <Paper elevation={0} sx={{ p: 1, backgroundColor: '#1e1e1e', color: '#d4d4d4', height: '100%', overflowY: 'auto', borderRadius: '4px' }}>
        <Typography component="pre" sx={{ whiteSpace: 'pre-wrap', wordBreak: 'break-all', fontSize: '0.9rem', fontFamily: 'monospace', margin: 0 }}>
          {code}
        </Typography>
      </Paper>
    );
  }
  
  return (
    // The parent Paper in App.jsx provides the overall container and padding.
    // This div ensures SyntaxHighlighter takes full height of its allocated space.
    <div style={{ fontSize: '0.85rem', height: '100%', minHeight: '100px' /* Ensure it has some min height */ }}> 
      <SyntaxHighlighter
        language={language}
        style={vscDarkPlus} // Use your chosen style
        showLineNumbers
        wrapLines={true}
        wrapLongLines={true} // Helps with very long lines without breaking layout
        customStyle={{ 
            margin: 0, 
            height: '100%', // Fill parent height
            overflowY: 'auto', 
            borderRadius: '4px', // Match Paper's rounding if desired
            border: 'none', // Remove default border if SyntaxHighlighter adds one
            boxSizing: 'border-box', // Ensure padding/border are included in height
        }}
        codeTagProps={{ style: { fontFamily: '"Fira Code", "Courier New", monospace' } }} // Optional: use a coding font
      >
        {String(code).trim()}
      </SyntaxHighlighter>
    </div>
  );
}

export default CodeDisplay;

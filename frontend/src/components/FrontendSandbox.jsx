import React, { useEffect, useRef, useMemo, useState } from 'react';
import { Paper, Typography } from '@mui/material'; // For styling the container and error messages

function FrontendSandbox({
  htmlContent = '',
  cssContent = '',
  javascriptContent = '',
  onSandboxMessage,
  parentOrigin, // Expected to be window.location.origin from App.jsx
  /**
   * The sandbox attribute policy for the iframe. Controls restrictions on iframe content.
   * - 'allow-scripts': Essential to allow JavaScript execution.
   * - 'allow-modals': Allows `alert()`, `confirm()`, `prompt()`. Added for example compatibility.
   * Other common flags (generally AVOID unless absolutely necessary due to security risks):
   *   - 'allow-same-origin': Would break sandbox security by allowing access to parent DOM/cookies if srcDoc was not used or if 'null' origin was bypassed. With srcDoc, origin is 'null', but still good to be explicit.
   *   - 'allow-popups': Prevents `window.open()` unless specified.
   *   - 'allow-forms': Prevents form submissions.
   *   - 'allow-top-navigation': Prevents iframe from changing parent URL.
   *   - 'allow-pointer-lock', 'allow-presentation', 'allow-orientation-lock', etc.
   * Refer to MDN docs for full list: https://developer.mozilla.org/en-US/docs/Web/HTML/Element/iframe#sandbox
   */
  sandboxPolicy = 'allow-scripts allow-modals', 
}) {
  const iframeRef = useRef(null);
  const [iframeKey, setIframeKey] = useState(0); // To force re-render

  // Update iframe key when content changes to ensure iframe re-renders with new srcDoc
  useEffect(() => {
    // console.log("FrontendSandbox: Content changed, updating iframe key.");
    setIframeKey(prevKey => prevKey + 1);
  }, [htmlContent, cssContent, javascriptContent]);

  // Setup message event listener for communication from iframe to parent
  useEffect(() => {
    const handleMessage = (event) => {
      // Security check: Ensure message is from our iframe.
      // For srcDoc iframes without 'allow-same-origin', event.origin will be "null".
      // So, checking event.source is the primary way to verify the message sender.
      if (iframeRef.current && event.source === iframeRef.current.contentWindow) {
        if (typeof onSandboxMessage === 'function') {
          // console.log("FrontendSandbox: Message received from iframe:", event.data);
          onSandboxMessage(event.data);
        } else {
          // console.warn("FrontendSandbox: onSandboxMessage prop is not a function.");
        }
      } else {
        // Optional: Log messages not from the expected source for debugging,
        // but be careful not to process them if they aren't trusted.
        // console.log("FrontendSandbox: Message received from unexpected source:", event.origin, event.source);
      }
    };

    window.addEventListener('message', handleMessage);
    return () => {
      window.removeEventListener('message', handleMessage);
    };
  }, [onSandboxMessage]); // Rerun if onSandboxMessage changes

  const srcDocValue = useMemo(() => {
    if (!parentOrigin) {
      console.error("FrontendSandbox: Critical - parentOrigin prop is missing. Sandbox communication script will fail.");
      // Return a minimal HTML document indicating the error, as the communication script cannot be set up.
      return `<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Error</title></head><body>Error: Parent origin not specified. Sandbox cannot initialize communication.</body></html>`;
    }

    const safeParentOrigin = String(parentOrigin); // Ensure it's a string

    return `
      <!DOCTYPE html>
      <html>
      <head>
          <meta charset="UTF-8">
          <style>
            body { margin: 0; padding: 8px; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif, "Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol"; color: #333; }
            /* Include user's CSS */
            ${cssContent}
          </style>
          <script>
              // Sandbox Communication & Error/Log Capture Script
              (function() {
                  const TARGET_ORIGIN = '${safeParentOrigin}';
                  let messageQueue = []; 
                  let canPost = window.parent && TARGET_ORIGIN && TARGET_ORIGIN !== 'null' && TARGET_ORIGIN !== 'undefined';

                  function postMsg(message) {
                      if (canPost) {
                          while(messageQueue.length > 0) {
                              const queuedMsg = messageQueue.shift();
                              window.parent.postMessage(queuedMsg, TARGET_ORIGIN);
                          }
                          window.parent.postMessage(message, TARGET_ORIGIN);
                      } else {
                          messageQueue.push(message);
                      }
                  }
                  
                  const originalConsole = {};
                  ['log', 'error', 'warn', 'info', 'debug', 'assert'].forEach(level => {
                      originalConsole[level] = console[level] || function() {}; 
                      console[level] = (...args) => {
                          originalConsole[level].apply(console, args); 
                          try {
                            const serializableArgs = args.map(arg => {
                                if (arg instanceof Error) return { __isError: true, message: arg.message, stack: arg.stack, name: arg.name, toString: arg.toString() };
                                if (typeof arg === 'function') return arg.toString();
                                if (typeof arg === 'symbol') return arg.toString();
                                try {
                                  JSON.stringify(arg); 
                                  return arg;
                                } catch (e) {
                                  return String(arg);
                                }
                            });
                            postMsg({ type: 'sandbox-log', level: level, data: serializableArgs });
                          } catch (e) {
                            originalConsole.error('Sandbox: Error serializing log for postMessage:', e);
                            postMsg({ type: 'sandbox-log', level: 'error', data: ['Sandbox: Error serializing log message.'] });
                          }
                      };
                  });

                  window.addEventListener('error', function(event) {
                      postMsg({
                          type: 'sandbox-error',
                          message: event.message,
                          filename: event.filename,
                          lineno: event.lineno,
                          colno: event.colno,
                          errorObject: event.error ? { __isError: true, message: event.error.message, stack: event.error.stack, name: event.error.name, toString: event.error.toString() } : null
                      });
                      return false; 
                  });

                  window.addEventListener('unhandledrejection', function(event) {
                    const reason = event.reason;
                    originalConsole.error('Sandbox: Unhandled Promise Rejection:', reason); 
                    postMsg({
                        type: 'sandbox-error', 
                        message: 'Unhandled Promise Rejection: ' + (reason instanceof Error ? reason.message : String(reason)),
                        errorObject: reason instanceof Error ? { __isError: true, message: reason.message, stack: reason.stack, name: reason.name, toString: reason.toString() } : { message: String(reason) }
                    });
                  });
              })();
          </script>
      </head>
      <body>
          ${htmlContent}
          ${javascriptContent ? `<script>${javascriptContent.replace(/<\/script>/g, '<\\/script>')}</script>` : ''}
      </body>
      </html>
    `;
  }, [htmlContent, cssContent, javascriptContent, parentOrigin]);

  if (!parentOrigin) {
    return (
        <Paper sx={{p:2, color: 'error.main', textAlign: 'center', height: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', border: '1px solid #ddd', borderRadius: '4px'}}>
            <Typography variant="h6">Frontend Sandbox Error</Typography>
            <Typography>Configuration error: Parent origin not provided. Cannot initialize sandbox.</Typography>
        </Paper>
    );
  }

  return (
    <iframe
      key={iframeKey} // Force re-render on key change
      ref={iframeRef}
      srcDoc={srcDocValue} // Content of the iframe
      sandbox={sandboxPolicy} // Security policy
      frameBorder="0"
      width="100%"
      height="100%"
      title="Frontend Sandbox Execution Environment"
      style={{ border: '1px solid #ddd', borderRadius: '4px', backgroundColor: '#fff' }} // Basic styling
    />
  );
}

export default FrontendSandbox;

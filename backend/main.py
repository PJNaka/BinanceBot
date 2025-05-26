from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio
from typing import List, Dict, Any, Callable, Awaitable

# Adjust imports based on your project structure
# Assuming main.py is in 'backend/' and agent.py, data.py are also in 'backend/'
try:
    from .agent import AutonomousAgent, AgentOutput, LLMClient, ReactPhase # Relative imports
    from .data import load_elements
    # from .sandbox import SandboxExecutionResult # Not directly used in main.py models anymore
except ImportError: # Fallback for scenarios where main.py might be run directly as a script
    from agent import AutonomousAgent, AgentOutput, LLMClient, ReactPhase
    from data import load_elements
    # from sandbox import SandboxExecutionResult


# Pydantic Models for robust API contracts

class PhaseInfo(BaseModel):
    phase: str # Corresponds to ReactPhase.value
    thoughts: List[str]
    summary: str
    data: Dict[str, Any] | None = None

class AgentOutputModel(BaseModel):
    phases_info: List[PhaseInfo] = []
    generated_code: str | None = None # For backend Python code
    test_results: Dict[str, Any] | None = None 
    final_output: Any | None = None
    errors: List[str] = []
    frontend_html: str | None = None
    frontend_css: str | None = None
    frontend_js: str | None = None

class GenerateCommandRequest(BaseModel):
    command: str
    client_id: str # Added client_id for WebSocket communication


# Connection Manager for WebSockets
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        print(f"Client #{client_id} connected via WebSocket.")

    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            # Optional: Add logic to await close if websocket is still in a valid state
            # try:
            #     if self.active_connections[client_id].client_state == WebSocketState.CONNECTED:
            #         # await self.active_connections[client_id].close() # This can also raise
            #         pass
            # except Exception:
            #     pass # Ignore errors on close, client might be gone
            del self.active_connections[client_id]
            print(f"Client #{client_id} disconnected.")

    async def send_personal_message(self, message: dict, client_id: str):
        if client_id in self.active_connections:
            websocket = self.active_connections[client_id]
            try:
                await websocket.send_json(message)
            except WebSocketDisconnect:
                print(f"Client #{client_id} disconnected (WebSocketDisconnect during send). Removing.")
                self.disconnect(client_id)
            except RuntimeError as e: # Handles "Cannot call send after connection is closed."
                print(f"RuntimeError sending to client #{client_id}: {e}. Removing connection.")
                self.disconnect(client_id)
            except Exception as e: # Catch any other unexpected error during send
                print(f"Unexpected error sending JSON to client #{client_id}: {type(e).__name__} - {e}. Removing.")
                self.disconnect(client_id)

manager = ConnectionManager()

app = FastAPI(
    title="Autonomous Programming Agent API",
    description="API for interacting with an AI agent that uses REACT + CoT to generate and test code.",
    version="0.1.0"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Agent and LLMClient (placeholder)
llm_client = LLMClient() 
autonomous_agent = AutonomousAgent(llm_client=llm_client)


# WebSocket Endpoint
@app.websocket("/ws/agent-updates/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await manager.connect(websocket, client_id)
    try:
        while True:
            # This loop keeps the connection alive and can optionally process incoming messages.
            # If the frontend is only receiving, it might not send data often.
            # A keep-alive mechanism (e.g., client sends ping, server sends pong) can be implemented if needed.
            data = await websocket.receive_text() 
            # For debugging or if client sends specific messages:
            print(f"Received message from client #{client_id} via WebSocket: {data}")
            # Example: Echo back or process specific client commands
            # await manager.send_personal_message({"received": data}, client_id)
    except WebSocketDisconnect:
        # This exception is expected when the client closes the connection.
        # manager.disconnect logs this.
        manager.disconnect(client_id)
    except Exception as e:
        # Catch any other unexpected errors during the WebSocket lifecycle.
        print(f"Unexpected error in WebSocket connection for client #{client_id}: {type(e).__name__} - {e}")
        manager.disconnect(client_id) # Ensure cleanup


# API Endpoints

@app.post("/generate", response_model=AgentOutputModel)
async def generate_code_endpoint(request: GenerateCommandRequest):
    
    async def agent_update_callback(update_data: Dict):
        # Check if client is still connected before sending
        if request.client_id in manager.active_connections:
            await manager.send_personal_message(update_data, request.client_id)
        else:
            # This can happen if client disconnects while agent is still processing.
            print(f"Client #{request.client_id} disconnected during agent processing. Update not sent: {update_data.get('type')}")

    try:
        # Pass the command and the callback to the agent
        agent_class_output: AgentOutput = await autonomous_agent.process_command(
            request.command,
            update_callback=agent_update_callback
        )
        
        # Convert the final AgentOutput (class instance) to the Pydantic AgentOutputModel
        response_data = AgentOutputModel(
            phases_info=[PhaseInfo(**pi) for pi in agent_class_output.phases_info],
            generated_code=agent_class_output.generated_code, # Backend code
            test_results=agent_class_output.test_results,
            final_output=agent_class_output.final_output,
            errors=agent_class_output.errors,
            frontend_html=agent_class_output.frontend_html,
            frontend_css=agent_class_output.frontend_css,
            frontend_js=agent_class_output.frontend_js
        )
        return response_data
        
    except Exception as e:
        # Log the exception for server-side debugging
        print(f"Critical error during agent processing for client #{request.client_id}: {type(e).__name__} - {e}")
        # Send a final error message over WebSocket if the client is still connected
        error_message_for_client = {
            "type": "error", 
            "phase": "PROCESS_ERROR", # General process error
            "message": f"An unexpected server error occurred: {str(e)}"
        }
        if request.client_id in manager.active_connections:
            # Use asyncio.create_task if you don't want to wait for this to complete,
            # but for a final error, it's probably okay to await.
            await manager.send_personal_message(error_message_for_client, request.client_id)
        
        # Raise HTTPException to inform the HTTP client about the error
        raise HTTPException(status_code=500, detail=f"An error occurred during agent processing: {str(e)}")


@app.get("/science-data")
async def get_science_data_endpoint():
    try:
        elements = load_elements() 
        return elements
    except Exception as e:
        print(f"Error loading science data: {e}")
        raise HTTPException(status_code=500, detail=f"An error occurred while loading science data: {str(e)}")

@app.get("/health")
async def health_check():
    return {"status": "ok"}

# To run this app (from the project root, assuming 'backend' is a folder):
# uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
#
# Note on WebSocketState: If more detailed state checking is needed in ConnectionManager.disconnect,
# you might need to import WebSocketState from starlette.websockets.
# from starlette.websockets import WebSocketState (or fastapi.websockets.WebSocketState if available)
# However, for simple deletion from active_connections, it's not strictly necessary.
# FastAPI's WebSocketDisconnect exception is the primary way to detect disconnections.

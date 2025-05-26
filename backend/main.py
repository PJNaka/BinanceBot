from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Depends, Query, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio
from typing import List, Dict, Any, Callable, Awaitable, Tuple, Optional # Added Depends, Query, status, Tuple, Optional
from sqlalchemy.orm import Session # For DB session in WebSocket

# Adjust imports based on your project structure
try:
    from .agent import AutonomousAgent, AgentOutput, LLMClient, ReactPhase
    from .data import load_elements
    from .api import auth_routes # Contains get_current_active_user
    from .api.auth_routes import get_current_active_user # Explicit import for endpoint dependency
    from . import crud_user, models, auth_utils # For WebSocket auth
    from .db_setup import get_db # For WebSocket auth
    from .redis_client import init_redis_pool, close_redis_pool
except ImportError: # Fallback for scenarios where main.py might be run directly as a script
    from agent import AutonomousAgent, AgentOutput, LLMClient, ReactPhase
    from data import load_elements
    from api import auth_routes
    from api.auth_routes import get_current_active_user
    import crud_user, models, auth_utils # Fallback for WebSocket auth
    from db_setup import get_db # Fallback for WebSocket auth
    from redis_client import init_redis_pool, close_redis_pool


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
        self.active_connections: Dict[str, Tuple[WebSocket, Any]] = {} # client_id: (WebSocket, user_id)

    async def connect(self, websocket: WebSocket, client_id: str, user_id: Any): # Added user_id
        await websocket.accept()
        self.active_connections[client_id] = (websocket, user_id)
        print(f"Client {client_id} (User {user_id}) connected via WebSocket.")

    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            websocket_tuple = self.active_connections.pop(client_id, None) # Use pop to get and remove
            if websocket_tuple:
                user_id = websocket_tuple[1]
                print(f"Client {client_id} (User {user_id}) disconnected from WebSocket.")
            else: # Should not happen if key was in active_connections
                print(f"Client {client_id} disconnected (user ID not found in tuple).")


    async def send_personal_message(self, message: dict, client_id: str):
        if client_id in self.active_connections:
            websocket, user_id = self.active_connections[client_id] # Unpack user_id for potential logging
            try:
                await websocket.send_json(message)
            except WebSocketDisconnect:
                print(f"Client {client_id} (User {user_id}) disconnected (WebSocketDisconnect during send). Removing.")
                self.disconnect(client_id) # disconnect will handle removal from dict
            except RuntimeError as e: 
                print(f"RuntimeError sending to client {client_id} (User {user_id}): {e}. Removing connection.")
                self.disconnect(client_id)
            except Exception as e: 
                print(f"Unexpected error sending JSON to client {client_id} (User {user_id}): {type(e).__name__} - {e}. Removing.")
                self.disconnect(client_id)

manager = ConnectionManager()

app = FastAPI(
    title="Autonomous Programming Agent API",
    description="API for interacting with an AI agent that uses REACT + CoT to generate and test code.",
    version="0.1.0"
)

# Event handlers for Redis pool lifecycle
@app.on_event("startup")
async def startup_event():
    await init_redis_pool()

@app.on_event("shutdown")
async def shutdown_event():
    await close_redis_pool()

# Include the authentication router
app.include_router(auth_routes.router)

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
autonomous_agent = AutonomousAgent(llm_client=llm_client) # Agent itself does not need db session directly


# WebSocket Endpoint
@app.websocket("/ws/agent-updates/{client_id}")
async def websocket_endpoint(
    websocket: WebSocket, 
    client_id: str, 
    token: Optional[str] = Query(None), # Token from query parameter
    db: Session = Depends(get_db) # DB session for user validation
):
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Missing auth token")
        return

    payload = auth_utils.decode_access_token(token) # Uses SECRET_KEY and ALGORITHM from auth_utils
    if not payload or not payload.get("sub"):
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid or expired token")
        return
    
    username = payload["sub"]
    user = crud_user.get_user_by_username(db, username=username)

    if not user or not user.is_active:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="User not found or inactive")
        return

    # User is authenticated, extract user_id
    user_id = user.id
    await manager.connect(websocket, client_id, user_id) # Pass user_id to manager
    
    try:
        while True:
            # Keep connection alive, or handle incoming client messages if any.
            # For this app, WS is primarily for server-to-client updates.
            data = await websocket.receive_text() 
            # print(f"Client {client_id} (User {user_id}) sent: {data}") # For debugging client messages
            # Example: await manager.send_personal_message({"echo_from_user": user_id, "data": data}, client_id)
    except WebSocketDisconnect:
        manager.disconnect(client_id) # Handles removal from active_connections and logging
    except Exception as e:
        # Log any other exceptions that occur during the WebSocket connection
        print(f"WebSocket error for client {client_id} (User {user_id}): {type(e).__name__} - {e}")
        manager.disconnect(client_id) # Ensure cleanup


# API Endpoints

@app.post("/generate", response_model=AgentOutputModel)
async def generate_code_endpoint(
    request: GenerateCommandRequest, # Assumes GenerateCommandRequest has client_id
    # db: Session = Depends(get_db), # Not directly needed by agent, but available if other ops were here
    current_user: models.User = Depends(get_current_active_user) # Authentication
):
    
    async def agent_update_callback(update_data: Dict):
        # Check if client is still connected before sending
        # request.client_id is from the Pydantic model, which should be the same as connected ws client_id
        if request.client_id in manager.active_connections:
            await manager.send_personal_message(update_data, request.client_id)
        else:
            print(f"Client #{request.client_id} (User {current_user.id}) disconnected during agent processing. Update not sent: {update_data.get('type')}")

    try:
        agent_class_output: AgentOutput = await autonomous_agent.process_command(
            user_command=request.command,
            user_id=current_user.id, # Use authenticated user's ID
            session_id=request.client_id, # Use client_id from request as session_id
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

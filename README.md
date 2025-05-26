# Autonomous Programming Agent

This project implements an autonomous programming agent inspired by Manus AI and OpenManus. The agent uses the REACT (Reflect, Evaluate, Analyze, Correct, Test) technique integrated with Chain of Thought (CoT) to generate and execute Python or JavaScript code based on user commands. It features a FastAPI backend and a ReactJS frontend.

## Features

*   **REACT + CoT Agent:** Intelligent agent for autonomous code generation and problem-solving.
*   **Secure Sandbox:** Docker-based sandbox for safe code execution (Python currently supported).
*   **FastAPI Backend:** Robust Python backend providing RESTful APIs and WebSocket communication.
*   **ReactJS Frontend:** Interactive user interface for command input, real-time thought process display, code view, and results.
*   **Scientific Data Interaction:** Includes a sample list of chemical elements for data manipulation tasks.
*   **Real-time Updates:** WebSocket integration for live updates of the agent's thinking process.

## Project Structure

```
.
├── backend/        # Python FastAPI backend
│   ├── main.py         # FastAPI app, API endpoints, WebSocket
│   ├── agent.py        # Core REACT + CoT agent logic
│   ├── sandbox.py      # Secure code execution sandbox (Docker)
│   ├── data.py         # Scientific data management
│   ├── elements.json   # Sample scientific data (chemical elements)
│   ├── config.py       # API keys and configurations
│   ├── Dockerfile      # Docker configuration for the backend
│   └── requirements.txt # Python dependencies
├── frontend/       # ReactJS Vite frontend
│   ├── src/
│   │   ├── App.jsx       # Main React application component
│   │   ├── components/   # UI components
│   │   ├── services/     # API service (axios, WebSocket)
│   │   └── ...           # Other React files (main.jsx, index.css, etc.)
│   ├── package.json    # Frontend dependencies
│   └── vite.config.js  # Vite configuration
└── README.md       # This file
```

## Prerequisites

*   [Docker](https://www.docker.com/get-started)
*   [Node.js](https://nodejs.org/) (v18 or later recommended for Vite) and npm
*   [Python](https://www.python.org/downloads/) (v3.10 or later recommended)

## Setup and Running

### Backend (FastAPI + Docker)

1.  **Navigate to Project Root:**
    Open your terminal in the project's root directory.

2.  **Configure API Keys:**
    *   Copy your LLM API key(s) into `backend/config.py`.
    *   The agent currently uses a placeholder LLM. To connect to a real LLM (e.g., Groq, OpenAI):
        *   Install the necessary Python client library (e.g., `pip install groq openai`). Add it to `backend/requirements.txt`.
        *   Update the `LLMClient` class in `backend/agent.py` to use the chosen LLM SDK and the API key from `config.py`.

3.  **Python Virtual Environment (Recommended for local development/testing):**
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate
    pip install -r backend/requirements.txt
    ```

4.  **Build the Docker Image:**
    ```bash
    docker build -t autonomous-agent-backend -f backend/Dockerfile backend
    ```
    *Note: The `-f backend/Dockerfile backend` syntax assumes Docker CLI is version 20.10+ that supports specifying build context separately. If using older versions, you might need to `cd backend` and run `docker build -t autonomous-agent-backend .` or adjust paths.*
    *A simpler command from project root if Dockerfile is efficient with context:*
    ```bash
    docker build -t autonomous-agent-backend ./backend
    ```


5.  **Run the Docker Container:**
    ```bash
    docker run -d -p 8000:8000 --name agent-app autonomous-agent-backend
    ```
    *   `-d` runs in detached mode.
    *   To view logs: `docker logs agent-app`
    *   To stop: `docker stop agent-app`
    *   To remove: `docker rm agent-app`

6.  **Alternative: Running Backend Directly with Uvicorn (for development):**
    Ensure you have activated the virtual environment and installed requirements.
    From the project root directory:
    ```bash
    uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
    ```

### Frontend (ReactJS + Vite)

1.  **Navigate to Frontend Directory:**
    ```bash
    cd frontend
    ```

2.  **Install Dependencies:**
    ```bash
    npm install
    ```

3.  **Run Development Server:**
    ```bash
    npm run dev
    ```
    The frontend will typically be available at `http://localhost:5173`.

4.  **Build for Production (Optional):**
    ```bash
    npm run build
    ```
    Static files will be generated in the `frontend/dist` directory.

## API Endpoints

*   **`POST /generate`**:
    *   Receives a user command and processes it with the REACT + CoT agent.
    *   Request Body: `{ "command": "your command here", "client_id": "your_unique_client_id" }`
    *   Returns the agent's final output (reasoning, code, results). Intermediate updates are sent via WebSocket.
*   **`GET /science-data`**: Returns the list of chemical elements.
*   **`GET /health`**: Health check for the backend.
*   **`WS /ws/agent-updates/{client_id}`**: WebSocket endpoint for real-time updates from the agent.

## Example Usage

1.  Ensure the backend and frontend servers are running.
2.  Open the frontend in your browser (e.g., `http://localhost:5173`).
3.  Enter a command in the input field, for example:
    `"Create a Python function that takes a list of chemical elements and returns the element with the highest atomic mass."`
4.  Click "Submit Command".
5.  Observe the agent's thought process, generated code, and execution results in real-time.

## Technology Stack

*   **Backend:** Python, FastAPI, Uvicorn, Docker
*   **Frontend:** ReactJS, Vite, Material-UI, Axios
*   **Agent:** REACT + CoT methodology (LLM interaction is currently placeholder)
*   **Code Execution:** Python execution in a Dockerized sandbox.

## Disclaimer
This is a conceptual implementation. The LLM integration is currently a placeholder. Real LLM integration and further security hardening for the sandbox would be required for production use.

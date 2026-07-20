"""Quick start script - run the API server."""

import sys
sys.path.insert(0, '/opt/data/Agent-Flow')

from agent_flow.agents.api.main import app
import uvicorn

if __name__ == "__main__":
    print("🚀 Starting Agent-Flow API...")
    print("📍 Demo UI: http://localhost:8000/demo")
    print("📍 Scenarios: http://localhost:8000/scenarios")
    print("📍 API Docs: http://localhost:8000/docs")
    print()
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
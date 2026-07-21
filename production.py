#!/usr/bin/env python3
"""Agent-Flow — Production Entry Point.

Starts the API server with production settings:
- Loads .env if exists
- Optional API key authentication
- CORS config
- Health checks
"""

import os
import sys
from pathlib import Path

# Load .env
env_path = Path("/app/data/.env") if Path("/app/data/.env").exists() else Path(".env")
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ.setdefault(key.strip(), value.strip())

sys.path.insert(0, str(Path(__file__).parent))

from agent_flow.agents.api.main import app
import uvicorn

if __name__ == "__main__":
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    log_level = os.getenv("API_LOG_LEVEL", "info")
    
    print(f"""
╔══════════════════════════════════════╗
║        Agent-Flow  v0.2.0           ║
║                                      ║
║  🚀 API:  http://{host}:{port}           ║
║  📖 Docs: http://{host}:{port}/docs     ║
║  🧪 UI:   http://localhost:3000      ║
╚══════════════════════════════════════╝
""")
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level=log_level,
        workers=1,
        proxy_headers=True,
        forwarded_allow_ips="*"
    )
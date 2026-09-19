import logging
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

import config
import duckdb
from tg_client import get_tg_connection
from app.schemas import HealthResponse
from app.routes import cases, timeline, graph, actions, memory, stats, extra

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("fraud_agent.api")

app = FastAPI(
    title="Agentic Fraud Investigation API",
    description="Backend REST API powered by TigerGraph Cloud, LangGraph, and Gemini for autonomous enterprise fraud detection, policy routing, and SAR filing.",
    version="1.0.0"
)

# Enable open CORS for all clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include route modules
app.include_router(cases.router)
app.include_router(timeline.router)
app.include_router(graph.router)
app.include_router(actions.router)
app.include_router(memory.router)
app.include_router(stats.router)
app.include_router(extra.router)

@app.get("/", tags=["General"])
def root():
    return {
        "service": "Agentic Fraud Investigation Platform",
        "status": "online",
        "docs_url": "/docs",
        "version": "1.0.0"
    }

@app.get("/health", response_model=HealthResponse, tags=["General"])
def health_check():
    """Health check endpoint verifying TigerGraph and DuckDB database connectivity."""
    tg_connected = False
    duck_connected = False
    
    # Check TigerGraph
    try:
        conn = get_tg_connection(max_retries=1)
        if conn:
            echo = conn.echo()
            if "Hello GSQL" in echo or "Hello" in echo:
                tg_connected = True
    except Exception as e:
        logger.warning(f"TigerGraph health ping failed: {e}")
        
    # Check DuckDB
    try:
        con = duckdb.connect(str(config.DUCKDB_PATH), read_only=True)
        res = con.execute("SELECT 1").fetchone()
        con.close()
        if res and res[0] == 1:
            duck_connected = True
    except Exception as e:
        logger.warning(f"DuckDB health ping failed: {e}")
        
    # Check loaded cases count
    cases_count = len(list(config.CASES_OUTPUT_DIR.glob("HHG-*.json")))
    
    return HealthResponse(
        status="healthy" if (duck_connected and cases_count > 0) else "degraded",
        tigergraph_connected=tg_connected,
        duckdb_connected=duck_connected,
        cases_loaded=cases_count,
        version="1.0.0"
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

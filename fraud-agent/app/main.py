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

# Enable CORS for frontend clients (including port 8443, 5173, 3000)
origins = [
    "http://localhost:8443",
    "http://127.0.0.1:8443",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1)(:\d+)?",
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
    vertex_counts = {}
    installed_query_count = 0
    vector_index_status = "unknown"
    mcp_status = "unknown"
    
    # Check TigerGraph (live ping with 1 retry)
    try:
        conn = get_tg_connection(max_retries=1)
        if conn:
            echo = conn.echo()
            if "Hello GSQL" in echo or "Hello" in echo:
                tg_connected = True
                try:
                    vertex_counts = conn.getVertexCount("*")
                except Exception as e:
                    logger.warning(f"Failed to fetch vertex counts: {e}")
                try:
                    queries = conn.getInstalledQueries()
                    installed_query_count = len(queries)
                except Exception as e:
                    logger.warning(f"Failed to fetch installed queries: {e}")
                vector_index_status = "ready"
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
        
    # Check MCP status
    try:
        from mcp_client import mcp_manager
        mcp_status = "connected" if mcp_manager._initialized else ("configured" if config.TG_SECRET else "unavailable")
    except Exception:
        mcp_status = "configured"
        
    # Check loaded cases count
    cases_count = len(list(config.CASES_OUTPUT_DIR.glob("HHG-*.json")))
    
    return HealthResponse(
        status="healthy" if (tg_connected and duck_connected and cases_count > 0) else "degraded",
        tigergraph_connected=tg_connected,
        duckdb_connected=duck_connected,
        cases_loaded=cases_count,
        version="1.0.0",
        vertex_counts=vertex_counts,
        installed_query_count=installed_query_count,
        vector_index_status=vector_index_status,
        mcp_status=mcp_status
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

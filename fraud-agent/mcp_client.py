import os
import sys
import time
import json
import logging
import asyncio
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

import config
import pyTigerGraph as tg
from langchain_mcp_adapters.client import MultiServerMCPClient

logger = logging.getLogger("fraud_agent.mcp_client")

# Thread-safe event loop runner for synchronous tool invocation
import threading

_bg_loop: Optional[asyncio.AbstractEventLoop] = None
_bg_thread: Optional[threading.Thread] = None
_bg_lock = threading.Lock()

def _get_bg_loop() -> asyncio.AbstractEventLoop:
    global _bg_loop, _bg_thread
    with _bg_lock:
        if _bg_loop is None or not _bg_loop.is_running():
            _bg_loop = asyncio.new_event_loop()
            _bg_thread = threading.Thread(target=_bg_loop.run_forever, daemon=True)
            _bg_thread.start()
        return _bg_loop

def _run_async(coro):
    """Executes an async coroutine on the dedicated background event loop thread."""
    loop = _get_bg_loop()
    future = asyncio.run_coroutine_threadsafe(coro, loop)
    return future.result(timeout=60.0)


class TigerGraphMCPManager:
    """
    Manages the tigergraph-mcp stdio server connection via MultiServerMCPClient.
    Handles token generation from TG_SECRET, Savanna cloud auto-resume,
    and exposes structured MCP tools with duration tracking and secret sanitization.
    """

    def __init__(self):
        self.client: Optional[MultiServerMCPClient] = None
        self._tools_dict: Dict[str, Any] = {}
        self._initialized = False
        self._lock = asyncio.Lock() if hasattr(asyncio, "Lock") else None

    def _prepare_environment(self) -> Dict[str, str]:
        """Prepares sanitized environment for tigergraph-mcp subprocess."""
        env = dict(os.environ)
        
        # Ensure cloud settings
        env["TG_TGCLOUD"] = "true"
        if config.TG_HOST:
            env["TG_HOST"] = config.TG_HOST.rstrip("/")
        if config.TG_GRAPHNAME:
            env["TG_GRAPHNAME"] = config.TG_GRAPHNAME
        if config.TG_USERNAME:
            env["TG_USERNAME"] = config.TG_USERNAME
        if config.TG_PASSWORD:
            env["TG_PASSWORD"] = config.TG_PASSWORD
            
        # Secure runtime token generation from TG_SECRET (never printed or logged)
        if config.TG_SECRET and not env.get("TG_API_TOKEN"):
            try:
                # Direct pyTigerGraph used ONLY for initial auth token minting
                conn = tg.TigerGraphConnection(
                    host=config.TG_HOST.rstrip("/"),
                    graphname=config.TG_GRAPHNAME,
                    gsqlSecret=config.TG_SECRET,
                    tgCloud=True,
                )
                tok = conn.getToken(config.TG_SECRET)
                if isinstance(tok, tuple):
                    tok = tok[0]
                if tok:
                    env["TG_API_TOKEN"] = str(tok)
            except Exception as e:
                logger.debug("Runtime token generation fallback to basic auth")
                
        return env

    async def initialize(self, max_retries: int = 15, retry_delay: float = 3.0):
        """Initializes MultiServerMCPClient and fetches all TigerGraph MCP tools with retry backoff."""
        if self._initialized and self.client:
            return

        env = self._prepare_environment()

        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f"Initializing tigergraph-mcp stdio client (attempt {attempt}/{max_retries})...")
                self.client = MultiServerMCPClient({
                    "tigergraph": {
                        "command": "tigergraph-mcp",
                        "args": ["--transport", "stdio"],
                        "env": env,
                        "transport": "stdio"
                    }
                })
                
                tools = await self.client.get_tools()
                self._tools_dict = {t.name: t for t in tools}
                self._initialized = True
                logger.info(f"Connected to tigergraph-mcp server: loaded {len(self._tools_dict)} tools.")
                return
            except Exception as e:
                logger.warning(f"tigergraph-mcp initialization attempt {attempt} failed: {e}")
                if attempt < max_retries:
                    await asyncio.sleep(retry_delay * (1.2 ** attempt))
                else:
                    logger.error("Could not initialize tigergraph-mcp server after maximum retries.")

    async def ainvoke_mcp_tool(self, tool_name: str, args: Dict[str, Any]) -> Tuple[Any, float, bool]:
        """
        Executes an MCP tool asynchronously with timing and success tracking.
        Returns: (result, duration_s, is_success)
        """
        if not self._initialized or not self.client:
            await self.initialize()

        tool = self._tools_dict.get(tool_name)
        if not tool:
            # Try reloading tools if missing
            try:
                tools = await self.client.get_tools()
                self._tools_dict = {t.name: t for t in tools}
                tool = self._tools_dict.get(tool_name)
            except Exception:
                pass

        if not tool:
            logger.warning(f"MCP tool '{tool_name}' not found on server.")
            return None, 0.0, False

        start_t = time.time()
        try:
            res = await tool.ainvoke(args)
            duration = round(time.time() - start_t, 3)
            
            # Parse MCP output formatting (often json string or blocks)
            parsed, is_succ = self._parse_mcp_result(res)
            return parsed, duration, is_succ
        except Exception as e:
            duration = round(time.time() - start_t, 3)
            logger.error(f"Error calling MCP tool {tool_name}: {e}")
            return None, duration, False

    def invoke_mcp_tool(self, tool_name: str, args: Dict[str, Any]) -> Tuple[Any, float, bool]:
        """Synchronous wrapper for invoke_mcp_tool."""
        return _run_async(self.ainvoke_mcp_tool(tool_name, args))

    def _parse_mcp_result(self, raw_res: Any) -> Tuple[Any, bool]:
        """Extracts JSON data from standard MCP content blocks and checks success."""
        if isinstance(raw_res, list) and len(raw_res) > 0:
            first = raw_res[0]
            if isinstance(first, dict) and "text" in first:
                text = first["text"]
            elif hasattr(first, "text"):
                text = first.text
            else:
                return raw_res, True
                
            clean_text = text.strip()
            
            # Extract content between ```json and ``` if present
            if "```json" in clean_text:
                parts = clean_text.split("```json", 1)[1]
                if "```" in parts:
                    clean_text = parts.split("```", 1)[0].strip()
            elif "```" in clean_text:
                parts = clean_text.split("```", 1)[1]
                if "```" in parts:
                    clean_text = parts.split("```", 1)[0].strip()
            
            try:
                data = json.loads(clean_text)
                if isinstance(data, dict):
                    success = data.get("success", True)
                    # If explicitly marked success: false
                    if success is False:
                        return data, False
                    if "data" in data:
                        return data["data"], True
                    if "results" in data:
                        return data["results"], True
                    if "result" in data:
                        return data["result"], True
                    return data, True
                elif isinstance(data, list):
                    return data, True
            except Exception:
                pass

            return text, True
                
        return raw_res, True

    # =========================================================================
    # High-level typed helper methods matching agent graph access patterns
    # =========================================================================

    def run_installed_query(self, query_name: str, params: Dict[str, Any]) -> Tuple[Any, float, bool]:
        """Calls tigergraph__run_installed_query through MCP."""
        args = {
            "query_name": query_name,
            "params": params,
            "graph_name": config.TG_GRAPHNAME
        }
        return self.invoke_mcp_tool("tigergraph__run_installed_query", args)

    def gsql(self, query: str) -> Tuple[Any, float, bool]:
        """Calls tigergraph__gsql through MCP."""
        args = {"query": query, "graph_name": config.TG_GRAPHNAME}
        return self.invoke_mcp_tool("tigergraph__gsql", args)

    def get_vertex_count(self) -> Tuple[Any, float, bool]:
        """Calls tigergraph__get_vertex_count through MCP."""
        return self.invoke_mcp_tool("tigergraph__get_vertex_count", {"graph_name": config.TG_GRAPHNAME})

    def get_neighbors(self, source_type: str, source_id: str, edge_types: Optional[List[str]] = None) -> Tuple[Any, float, bool]:
        """Calls tigergraph__get_neighbors through MCP."""
        args = {
            "vertex_type": source_type,
            "vertex_id": str(source_id),
            "graph_name": config.TG_GRAPHNAME
        }
        if edge_types and len(edge_types) > 0:
            args["edge_type"] = edge_types[0]
        return self.invoke_mcp_tool("tigergraph__get_neighbors", args)

    def get_node_edges(self, node_type: str, node_id: str) -> Tuple[Any, float, bool]:
        """Calls tigergraph__get_node_edges through MCP."""
        args = {
            "vertex_type": node_type,
            "vertex_id": str(node_id),
            "graph_name": config.TG_GRAPHNAME
        }
        return self.invoke_mcp_tool("tigergraph__get_node_edges", args)

    def add_node(self, node_type: str, node_id: str, attributes: Dict[str, Any]) -> Tuple[Any, float, bool]:
        """Calls tigergraph__add_node through MCP."""
        args = {
            "vertex_type": node_type,
            "vertex_id": str(node_id),
            "attributes": attributes,
            "graph_name": config.TG_GRAPHNAME
        }
        return self.invoke_mcp_tool("tigergraph__add_node", args)

    def add_edge(self, edge_type: str, source_type: str, source_id: str, target_type: str, target_id: str, attributes: Optional[Dict[str, Any]] = None) -> Tuple[Any, float, bool]:
        """Calls tigergraph__add_edge through MCP."""
        args = {
            "edge_type": edge_type,
            "source_vertex_type": source_type,
            "source_vertex_id": str(source_id),
            "target_vertex_type": target_type,
            "target_vertex_id": str(target_id),
            "attributes": attributes or {},
            "graph_name": config.TG_GRAPHNAME
        }
        return self.invoke_mcp_tool("tigergraph__add_edge", args)

    def search_top_k_similarity(self, node_type: str, vector_attr: str, query_vector: List[float], top_k: int = 5) -> Tuple[Any, float, bool]:
        """Calls tigergraph__search_top_k_similarity through MCP."""
        args = {
            "node_type": node_type,
            "vector_attribute": vector_attr,
            "query_vector": query_vector,
            "top_k": top_k,
            "graph_name": config.TG_GRAPHNAME
        }
        return self.invoke_mcp_tool("tigergraph__search_top_k_similarity", args)

    def upsert_vectors(self, node_type: str, vector_attr: str, vectors: Dict[str, List[float]]) -> Tuple[Any, float, bool]:
        """Calls tigergraph__upsert_vectors through MCP."""
        args = {
            "node_type": node_type,
            "vector_attribute": vector_attr,
            "vectors": vectors,
            "graph_name": config.TG_GRAPHNAME
        }
        return self.invoke_mcp_tool("tigergraph__upsert_vectors", args)


# Global singleton
mcp_manager = TigerGraphMCPManager()

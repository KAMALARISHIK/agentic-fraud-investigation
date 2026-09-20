import time
import logging
from typing import Optional, Any, Dict
import pyTigerGraph as tg
import config

logger = logging.getLogger("fraud_agent.tg_client")

def get_tg_connection(
    max_retries: int = 30,
    initial_delay: float = 5.0,
    backoff_factor: float = 1.2,
    max_delay: float = 30.0,
) -> Optional[tg.TigerGraphConnection]:
    """
    Connects to TigerGraph with retries and exponential backoff.
    Handles Savanna auto-resume by retrying up to ~5 minutes.
    """
    if not config.TG_HOST:
        logger.warning("TG_HOST is not set.")
        return None

    host = config.TG_HOST.rstrip("/")
    if not host.startswith("http://") and not host.startswith("https://"):
        host = f"https://{host}"
    
    is_tgcloud = bool(config.TG_TGCLOUD or ("tgcloud.io" in host))
    graph_name = config.TG_GRAPHNAME

    delay = initial_delay
    total_elapsed = 0.0

    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f"Connecting to TigerGraph at {host} (attempt {attempt}/{max_retries})...")
            
            # Step 1: Initialize connection
            api_token = config.TG_API_TOKEN if config.TG_API_TOKEN else None
            conn = tg.TigerGraphConnection(
                host=host,
                graphname=graph_name,
                gsqlSecret=config.TG_SECRET if config.TG_SECRET else "",
                username=config.TG_USERNAME if config.TG_USERNAME else None,
                password=config.TG_PASSWORD if config.TG_PASSWORD else None,
                apiToken=api_token,
                tgCloud=is_tgcloud,
            )

            # Step 2: Handle authentication if apiToken not directly provided
            if not api_token:
                if config.TG_SECRET:
                    try:
                        token = conn.getToken(config.TG_SECRET)
                        if isinstance(token, tuple):
                            token = token[0]
                        conn.apiToken = token
                    except Exception as token_err:
                        logger.warning(f"Failed to get token via TG_SECRET: {token_err}.")
                elif config.TG_USERNAME and config.TG_PASSWORD:
                    try:
                        token = conn.getToken()
                        if isinstance(token, tuple):
                            token = token[0]
                        conn.apiToken = token
                    except Exception:
                        pass

            # Step 3: Test connection with a lightweight ping/check
            # conn.echo() or ping
            try:
                echo_res = conn.echo()
                logger.info(f"TigerGraph connection successful. Echo: {echo_res}")
                return conn
            except Exception as echo_err:
                # If graph does not exist yet, schema creation might be pending, but host is reachable
                logger.info(f"Host reachable, response: {echo_err}")
                return conn

        except Exception as e:
            logger.warning(f"Connection attempt {attempt} failed: {e}")
            if attempt == max_retries:
                logger.error(f"Exhausted {max_retries} connection attempts to TigerGraph.")
                return None
            
            time.sleep(delay)
            total_elapsed += delay
            delay = min(delay * backoff_factor, max_delay)

    return None

class TigerGraphManager:
    """Wrapper around pyTigerGraph connection for convenient fraud queries."""

    def __init__(self, conn: Optional[tg.TigerGraphConnection] = None):
        self._conn = conn

    @property
    def conn(self) -> Optional[tg.TigerGraphConnection]:
        if self._conn is None:
            self._conn = get_tg_connection()
        return self._conn

    def is_connected(self) -> bool:
        try:
            c = self.conn
            if c is None:
                return False
            # Check host response
            res = c.echo()
            return True
        except Exception:
            return False

    def run_installed_query(self, query_name: str, params: Optional[Dict[str, Any]] = None) -> Any:
        if self.conn is None:
            raise ConnectionError("TigerGraph is not connected.")
        return self.conn.runInstalledQuery(query_name, params=params or {})

    def run_gsql(self, gsql_script: str) -> str:
        if self.conn is None:
            raise ConnectionError("TigerGraph is not connected.")
        return self.conn.gsql(gsql_script)

    def upsert_vertex(self, vertex_type: str, vertex_id: str, attributes: Dict[str, Any]) -> Any:
        if self.conn is None:
            raise ConnectionError("TigerGraph is not connected.")
        return self.conn.upsertVertex(vertex_type, vertex_id, attributes)

    def upsert_edge(
        self,
        source_vertex_type: str,
        source_vertex_id: str,
        edge_type: str,
        target_vertex_type: str,
        target_vertex_id: str,
        attributes: Optional[Dict[str, Any]] = None,
    ) -> Any:
        if self.conn is None:
            raise ConnectionError("TigerGraph is not connected.")
        return self.conn.upsertEdge(
            source_vertex_type,
            source_vertex_id,
            edge_type,
            target_vertex_type,
            target_vertex_id,
            attributes=attributes or {},
        )

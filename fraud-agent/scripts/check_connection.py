import sys
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import config
from tg_client import get_tg_connection
from llm import get_genai_client, generate_text

def check_tigergraph(max_retries: int = 15, initial_delay: float = 3.0) -> bool:
    try:
        if not config.TG_HOST:
            print("TG_HOST is not set in environment.")
            return False
        conn = get_tg_connection(max_retries=max_retries, initial_delay=initial_delay, backoff_factor=1.3, max_delay=15.0)
        if conn is None:
            return False
        # Test echo
        conn.echo()
        return True
    except Exception as e:
        print(f"TigerGraph check error: {e}")
        return False

def check_gemini() -> bool:
    try:
        if not config.GEMINI_API_KEY:
            return False
        client = get_genai_client()
        if client is None:
            return False
        res = generate_text("Ping", model=config.GEMINI_MODEL)
        return bool(res and not res.startswith("ERROR") and res != "LLM_NOT_CONFIGURED")
    except Exception:
        return False

def main():
    tg_ok = check_tigergraph()
    gemini_ok = check_gemini()

    print(f"TigerGraph: {'OK' if tg_ok else 'FAIL'}")
    print(f"Gemini:     {'OK' if gemini_ok else 'FAIL'}")

    if tg_ok and gemini_ok:
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()

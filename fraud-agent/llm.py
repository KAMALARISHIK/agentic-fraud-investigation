import logging
from typing import List, Optional, Dict, Any
from google import genai
from google.genai import types
import config

logger = logging.getLogger("fraud_agent.llm")

_client: Optional[genai.Client] = None

def get_genai_client() -> Optional[genai.Client]:
    global _client
    if _client is None and config.GEMINI_API_KEY:
        try:
            _client = genai.Client(api_key=config.GEMINI_API_KEY)
        except Exception as e:
            logger.error(f"Failed to initialize Google GenAI Client: {e}")
            _client = None
    return _client

def generate_text(
    prompt: str,
    system_instruction: Optional[str] = None,
    model: Optional[str] = None,
    temperature: float = 0.1,
) -> str:
    """Generate text response using Gemini SDK."""
    client = get_genai_client()
    if not client:
        logger.warning("GEMINI_API_KEY not configured or client initialization failed.")
        return "LLM_NOT_CONFIGURED"

    model_name = model or config.GEMINI_MODEL
    config_params = types.GenerateContentConfig(
        temperature=temperature,
        system_instruction=system_instruction,
    )

    import concurrent.futures

    def _call():
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=config_params,
        )
        return response.text or ""

    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(_call)
            return future.result(timeout=15.0)
    except concurrent.futures.TimeoutError:
        logger.warning(f"Gemini generate_content timed out after 15s for prompt length {len(prompt)}.")
        return "ERROR: Gemini API call timed out"
    except Exception as e:
        logger.error(f"Gemini generate_content error: {e}")
        return f"ERROR: {e}"

def generate_embedding(
    text: str,
    model: Optional[str] = None,
) -> List[float]:
    """Generate vector embedding for a single text."""
    res = generate_embeddings_batch([text], model=model)
    return res[0] if res else [0.0] * 768

def generate_embeddings_batch(
    texts: List[str],
    model: Optional[str] = None,
) -> List[List[float]]:
    """Generate vector embeddings for a batch of texts."""
    client = get_genai_client()
    if not client or not texts:
        return [[0.0] * 768 for _ in texts]

    model_name = model or config.GEMINI_EMBED_MODEL
    import concurrent.futures

    def _call():
        response = client.models.embed_content(
            model=model_name,
            contents=texts,
        )
        results = []
        if hasattr(response, 'embeddings') and response.embeddings:
            for emb in response.embeddings:
                results.append(emb.values if hasattr(emb, 'values') else [0.0] * 768)
            return results
        elif hasattr(response, 'embedding') and response.embedding:
            return [response.embedding.values]
        return [[0.0] * 768 for _ in texts]

    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(_call)
            return future.result(timeout=5.0)
    except Exception as e:
        logger.warning(f"Gemini batch embed_content error/timeout: {e}")
        return [[0.0] * 768 for _ in texts]

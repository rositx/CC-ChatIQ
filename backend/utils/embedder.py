import asyncio
import logging
from typing import List
from backend.config import EMBEDDING_PROVIDER, EMBEDDING_DIMENSIONS

logger = logging.getLogger("embedder")

# Global fastembed model reference to avoid reloading model repeatedly
_model_instance = None

def _get_fastembed_model():
    """Lazily load and cache the fastembed model instance to optimize memory usage."""
    global _model_instance
    if _model_instance is None:
        from fastembed import TextEmbedding
        _model_instance = TextEmbedding()
    return _model_instance

async def generate_embedding(text: str) -> List[float]:
    """Generates a high-dimensional vector for a given normalized string with backoff."""
    from backend import config
    
    # Normalize query inputs: remove double spacing, leading/trailing whitespace
    normalized_text = " ".join(text.strip().split())
    
    # 3-strike exponential backoff wrapper
    for attempt in range(3):
        try:
            if config.EMBEDDING_PROVIDER == "local":
                model = _get_fastembed_model()
                embeddings = list(model.embed([normalized_text]))
                return list(embeddings[0].tolist())
            else:
                # Return standard deterministic mock vector matching dimensions
                return [0.0] * config.EMBEDDING_DIMENSIONS
        except Exception as e:
            if attempt == 2:
                logger.error("Embedding generation failed after 3 attempts.")
                raise e
            # Wait 1s, 2s on subsequent failures
            wait_time = 2 ** attempt
            logger.warning(f"Embedding attempt {attempt + 1} failed: {str(e)}. Retrying in {wait_time}s...")
            await asyncio.sleep(wait_time)

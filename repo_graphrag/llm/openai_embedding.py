from ..config.settings import (
    embedding_model_openai_api_key,
    embedding_model_openai_base_url,
    embedding_model_name,
    rate_limit_error_wait_time,
    embedding_dim,
    embedding_support_custom_dim
)
from ..utils.rate_limiter import get_rate_limiter
from typing import List
from openai import AsyncOpenAI
import asyncio
import logging
import numpy as np


logger = logging.getLogger(__name__)

# Initialize OpenAI client for embeddings
_openai_embedding_client = None
if embedding_model_openai_api_key or embedding_model_openai_base_url:
    client_kwargs = {"timeout": 300.0}
    if embedding_model_openai_api_key:
        client_kwargs["api_key"] = embedding_model_openai_api_key

    if embedding_model_openai_base_url:
        client_kwargs["base_url"] = embedding_model_openai_base_url.rstrip("/")
    _openai_embedding_client = AsyncOpenAI(**client_kwargs)

async def openai_embed(texts: List[str]) -> np.ndarray:
    """
    Generate embeddings using OpenAI API.

    Args:
        texts: List of text strings to embed

    Returns:
        np.ndarray: Array of embeddings

    Raises:
        ValueError: If OpenAI client is not configured
        RuntimeError: If embedding generation fails
    """
    if not _openai_embedding_client:
        raise ValueError(
            "OpenAI embedding client is not configured. "
            "Please set either EMBEDDING_MODEL_OPENAI_API_KEY or EMBEDDING_MODEL_OPENAI_BASE_URL."
        )

    # Prepare batches if needed (OpenAI has token limits)
    all_embeddings = []

    try:
        # Apply rate limiting for API calls
        async with get_rate_limiter():
            # Create embedding request parameters
            embed_params = {
                "model": embedding_model_name,
                "input": texts,
                "encoding_format": "float"
            }
            
            # Only include dimensions if the model supports custom dimensions
            if embedding_support_custom_dim:
                embed_params["dimensions"] = embedding_dim
            
            response = await _openai_embedding_client.embeddings.create(**embed_params)

        all_embeddings = [data.embedding for data in response.data]

    except Exception as e:
        logger.error(f"OpenAI embedding API error: {e}")

        # If batch fails, try individual texts
        if len(texts) > 1:
            for text in texts:
                try:
                    async with get_rate_limiter():
                        # Create embedding request parameters for fallback
                        embed_params = {
                            "model": embedding_model_name,
                            "input": [text],
                            "encoding_format": "float"
                        }
                        
                        # Only include dimensions if the model supports custom dimensions
                        if embedding_support_custom_dim:
                            embed_params["dimensions"] = embedding_dim
                        
                        response = await _openai_embedding_client.embeddings.create(**embed_params)
                    all_embeddings.append(response.data[0].embedding)
                except Exception as inner_e:
                    logger.error(f"Failed to embed individual text: {inner_e}")
                    raise RuntimeError(f"Failed to embed text: {text[:50]}... Error: {inner_e}")
        else:
            raise RuntimeError(f"Failed to embed text: {texts[0][:50]}... Error: {e}")

    return np.array(all_embeddings)


async def test_openai_embedding():
    """
    Test OpenAI embedding API with timing and response analysis.
    """
    import time

    test_texts = [
        "This is a test sentence for OpenAI embedding.",
        "Another example text to test the embedding API.",
        "Python programming language is widely used for AI and data science.",
        "Machine learning models require large amounts of training data.",
        "Natural language processing helps computers understand human language."
    ]

    print("=" * 60)
    print("Testing OpenAI Embedding API")
    print("=" * 60)

    # Check if client is configured
    if not _openai_embedding_client:
        print("[ERROR] OpenAI embedding client is not configured.")
        print("Please set either EMBEDDING_MODEL_OPENAI_API_KEY or EMBEDDING_MODEL_OPENAI_BASE_URL in .env file.")
        return

    print(f"[OK] OpenAI client configured")
    print(f"[INFO] Model: {embedding_model_name}")
    print(f"[INFO] Embedding dimension: {embedding_dim}")
    print(f"[INFO] Test texts: {len(test_texts)}")
    print()

    try:
        # Test single text embedding
        print("1. Testing single text embedding...")
        start_time = time.time()
        single_embedding = await openai_embed([test_texts[0]])
        elapsed_time = time.time() - start_time

        print(f"   [OK] Success!")
        print(f"   [TIME] Time: {elapsed_time:.3f} seconds")
        print(f"   [SHAPE] Shape: {single_embedding.shape}")
        print(f"   [VALUES] First 5 values: {single_embedding[0][:5]}")
        print()

        # Test batch embedding
        print("2. Testing batch embedding...")
        start_time = time.time()
        batch_embeddings = await openai_embed(test_texts)
        elapsed_time = time.time() - start_time

        print(f"   [OK] Success!")
        print(f"   [TIME] Time: {elapsed_time:.3f} seconds")
        print(f"   [SHAPE] Shape: {batch_embeddings.shape}")
        print(f"   [STATS] Average embedding length: {np.mean(np.linalg.norm(batch_embeddings, axis=1)):.4f}")
        print()

        # Test similarity calculation
        print("3. Testing similarity calculation...")
        from sklearn.metrics.pairwise import cosine_similarity

        # Calculate similarity between first two embeddings
        similarity = cosine_similarity(
            batch_embeddings[0:1],
            batch_embeddings[1:2]
        )[0][0]

        print(f"   [SIMILARITY] Cosine similarity between text 1 and 2: {similarity:.4f}")

        # Calculate similarity matrix
        similarity_matrix = cosine_similarity(batch_embeddings)
        print(f"   [MATRIX] Similarity matrix shape: {similarity_matrix.shape}")
        print(f"   [AVG] Average similarity: {np.mean(similarity_matrix):.4f}")
        print()

        print("=" * 60)
        print("[SUCCESS] All tests completed successfully!")
        print("=" * 60)

    except Exception as e:
        print(f"[ERROR] Error during testing: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    import asyncio

    print("Starting OpenAI embedding test...")
    print()

    # Run the async test
    asyncio.run(test_openai_embedding())
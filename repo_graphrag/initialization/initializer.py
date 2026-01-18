import gc
import os
import asyncio
from ..config.settings import (
    parallel_num,
    graph_create_max_token_size,
    embedding_model_provider,
    embedding_model_name,
    embedding_tokenizer_model_name,
    embedding_dim,
    embedding_max_token_size,
    llm_model_max_async,
    embedding_func_max_async,
    document_definition_list,
    huggingface_hub_token,
    hf_hub_offline,
    hf_hub_cache
)
from lightrag import LightRAG
from transformers import AutoModel, AutoTokenizer
from lightrag.utils import EmbeddingFunc
from lightrag.llm.hf import hf_embed
from lightrag.kg.shared_storage import initialize_pipeline_status
from ..llm.llm_client import complete_graph_create
from ..llm.openai_embedding import openai_embed


_emb_model = None
_tokenizer = None
_embed_init_lock = None

async def _load_embedding_components():
    """
    Initialize and cache the embedding model and tokenizer (thread-safe once-only init).
    Supports both HuggingFace and OpenAI embedding providers.

    Returns:
        Callable: Embedding function appropriate for the configured provider
    """
    global _emb_model, _tokenizer, _embed_init_lock, _embedding_func

    # Check if we already have an embedding function
    if hasattr(_load_embedding_components, '_cached_embedding_func'):
        return _load_embedding_components._cached_embedding_func

    # Share the same lock across calls
    lock = _embed_init_lock
    if lock is None:
        new_lock = asyncio.Lock()
        if _embed_init_lock is None:
            _embed_init_lock = new_lock
            lock = new_lock
        else:
            lock = _embed_init_lock

    async with lock:
        # Double-check after acquiring lock
        if hasattr(_load_embedding_components, '_cached_embedding_func'):
            return _load_embedding_components._cached_embedding_func

        # Load embedding model based on provider
        if embedding_model_provider == "huggingface":
            # Load HuggingFace embedding model & tokenizer
            if huggingface_hub_token:
                _emb_model = await asyncio.to_thread(AutoModel.from_pretrained, embedding_model_name, token=huggingface_hub_token)
                _tokenizer = await asyncio.to_thread(AutoTokenizer.from_pretrained, embedding_tokenizer_model_name, token=huggingface_hub_token)
            else:
                _emb_model = await asyncio.to_thread(AutoModel.from_pretrained, embedding_model_name)
                _tokenizer = await asyncio.to_thread(AutoTokenizer.from_pretrained, embedding_tokenizer_model_name)

            # Create HuggingFace embedding function
            def hf_embedding_func(texts):
                return hf_embed(
                    texts,
                    tokenizer=_tokenizer,
                    embed_model=_emb_model,
                )

            _load_embedding_components._cached_embedding_func = hf_embedding_func

        elif embedding_model_provider == "openai":
            # For OpenAI provider, we don't need to load local models
            # Set them to None to indicate we're using OpenAI API
            _emb_model = None
            if not hf_hub_offline:
                _tokenizer = await asyncio.to_thread(AutoTokenizer.from_pretrained, embedding_tokenizer_model_name)
                _tokenizer.save_pretrained(hf_hub_cache + "/" + embedding_tokenizer_model_name)
            else:
                _tokenizer = await asyncio.to_thread(AutoTokenizer.from_pretrained, hf_hub_cache + "/" + embedding_tokenizer_model_name)


            # Import OpenAI embedding function

            # Use OpenAI embedding function directly
            _load_embedding_components._cached_embedding_func = openai_embed

        else:
            raise ValueError(f"Unsupported embedding model provider: {embedding_model_provider}. "
                           f"Supported providers: 'huggingface', 'openai'")

        return _load_embedding_components._cached_embedding_func


async def initialize_rag(storage_dir_path: str) -> LightRAG:
    """
    Initialize and return a configured LightRAG instance.
    
    Args:
        storage_dir_path: Path to the storage directory
    
    Returns:
        LightRAG: The initialized LightRAG instance
    """
    
    # Attempt to clean up global state
    gc.collect()
    
    # Derive storage name from path
    storage_name = os.path.basename(storage_dir_path.rstrip('/'))
    
    # Get embedding function from provider-specific initialization
    embedding_func_raw = await _load_embedding_components()

    # Wrap the embedding function in EmbeddingFunc
    embedding_func = EmbeddingFunc(
        embedding_dim=embedding_dim,
        max_token_size=embedding_max_token_size,
        func=embedding_func_raw
    )

    # Construct LightRAG with configured parameters
    rag = LightRAG(
        working_dir=storage_dir_path,  # storage path
        workspace=storage_name+"_work",  # workspace name
        max_parallel_insert=parallel_num,  # parallelism for chunking/graphing
        vector_storage="FaissVectorDBStorage",  # use Faiss for vectors
        llm_model_func=complete_graph_create,  # LLM for entity extraction/summaries
        summary_max_tokens=graph_create_max_token_size,  # max tokens for graph_create
        embedding_func=embedding_func,
        llm_model_max_async=llm_model_max_async,  # LLM concurrency limit
        embedding_func_max_async=embedding_func_max_async,  # embed concurrency limit
        addon_params={
            "language": "english",  # language for summaries
            "entity_types": document_definition_list,  # entity types to extract from docs
        }
    )

    # Initialize storages and pipeline status
    await rag.initialize_storages()
    await initialize_pipeline_status()

    return rag

def get_tokenizer() -> AutoTokenizer:
    """
    Get the tokenizer used by the embedding model.
    Only available for HuggingFace provider.

    Returns:
        AutoTokenizer: Tokenizer for the embedding model

    Raises:
        ValueError: If tokenizer is not available or not initialized
    """
    if _tokenizer is None:
        # Check if we're using OpenAI provider by checking if _emb_model is also None
        # (for OpenAI, both are set to None in _load_embedding_components)
        if _emb_model is None:
            raise ValueError("Tokenizer is not available for OpenAI embedding provider")
        else:
            raise ValueError("Tokenizer is not initialized (HuggingFace provider)")
    return _tokenizer

import os
import logging
import asyncio
from datetime import datetime, timezone
from typing import Dict, Any, Tuple
from ..config.settings import code_ext_dict, parallel_num
from tree_sitter import Parser
from lightrag import LightRAG
from lightrag.utils import compute_mdhash_id
from lightrag.base import DocStatus
from .code_chunker import create_code_chunks
from .code_grapher import create_code_graph
from ..utils.node_line_range import get_node_line_range, build_line_offset_list


logger = logging.getLogger(__name__)

async def process_file(code_path: str, file_content_bytes: bytes) -> Dict[str, Any]:
    """
    Process a single code file: chunking and graph extraction.

    Args:
        code_path: Path to the code file
        file_content_bytes: File content as bytes

    Returns:
        Dictionary containing file processing results
    """
    file_name = os.path.basename(code_path)

    # Extract extension from filename
    _, ext = os.path.splitext(file_name)

    # Prepare Tree-sitter parser
    language = code_ext_dict[ext.lstrip(".")]["language"]
    parser = Parser(language)

    # Parse bytes into syntax tree
    tree = parser.parse(file_content_bytes)

    # Get root node
    root_node = tree.root_node

    # Decode bytes to UTF-8 text
    file_content_text = file_content_bytes.decode('utf-8')

    # Build a line offset list
    line_offset_list = build_line_offset_list(file_content_bytes)

    chunks = []
    entities = []
    relationships = []

    # Extract nodes to be chunked
    chunk_node_list = await create_code_chunks(root_node, file_content_bytes)

    # Get definition node types to extract as entities
    definition_dict = code_ext_dict[ext.lstrip(".")]["definition"]

    # For each target node, perform chunking and graph extraction
    for node, node_text in chunk_node_list:

        # Get line range
        start_line, end_line = get_node_line_range(node, line_offset_list)

        # Set chunk ID
        source_id = f"file:{file_name}_line:{start_line}-{end_line}"

        # Append chunk with its ID
        chunks.append(
            {
                "content": node_text,
                "source_id": source_id,
                "file_path": code_path
            }
        )

        # Extract graph elements (entities, relationships)
        chunk_entities, chunk_relationships = await create_code_graph(
            node=node,
            definition_dict=definition_dict,
            file_content_bytes=file_content_bytes,
            parent_definition_name="",
            source_id=source_id,
            code_path=code_path,
            line_offset_list=line_offset_list
        )

        # Append extracted entities/relationships
        entities += chunk_entities
        relationships += chunk_relationships

    logger.info(f"Processed: {code_path}")

    # Return file/chunks/graph information
    return {
        "file_path": code_path,
        "file_content": file_content_text,
        "chunks": chunks,
        "entities": entities,
        "relationships": relationships
    }

async def store_file_result(rag: LightRAG, result: Dict[str, Any]) -> None:
    """
    Store a single file's processing results into storage.
    This function runs serially to avoid database resource conflicts.

    Args:
        rag: LightRAG instance
        result: File processing results from process_file
    """
    file_path = result["file_path"]
    file_content = result["file_content"]
    file_chunks = result["chunks"]
    file_entities = result["entities"]
    file_relationships = result["relationships"]

    if file_chunks or file_entities or file_relationships:
        try:
            # Create document ID from file content
            doc_id = compute_mdhash_id(file_content, prefix="doc-")

            logger.info(f"Saving {file_path} to storage: chunks={len(file_chunks)}, entities={len(file_entities)}, relationships={len(file_relationships)}")
            await rag.ainsert_custom_kg(
                custom_kg={
                    "chunks": file_chunks,
                    "entities": file_entities,
                    "relationships": file_relationships
                },
                full_doc_id=doc_id
            )

            # Update document status
            if file_chunks:
                # Build list of chunk IDs
                chunk_ids = [compute_mdhash_id(chunk["content"], prefix="chunk-") for chunk in file_chunks]

                # Upsert document status
                current_time = datetime.now(timezone.utc).isoformat()
                await rag.doc_status.upsert({
                    doc_id: {
                        "status": DocStatus.PROCESSED,
                        "chunks_count": len(file_chunks),
                        "content": file_content,
                        "content_summary": f"Code file: {os.path.basename(file_path)}",
                        "content_length": len(file_content),
                        "created_at": current_time,
                        "updated_at": current_time,
                        "file_path": file_path,
                        "chunks_list": chunk_ids,
                        "metadata": {
                            "file_type": "code",
                            "processed_by": "code_processor"
                        }
                    }
                })

                # Save to full document storage
                await rag.full_docs.upsert(
                    {
                        doc_id: {"content": file_content}
                    }
                )

                logger.info(f"Updated doc status for {file_path} (chunks_list: {len(chunk_ids)})")

            logger.info(f"Saved {file_path} to storage (ID: {doc_id})")
        except Exception as e:
            logger.error(f"code_processor error for {file_path}: {e}")
            raise

async def code_to_storage(rag: LightRAG, code_dict: Dict[str, bytes]) -> None:
    """
    Chunk code, build a graph, and store into backend storage.
    Uses dynamic batch queue processing with serial storage operations.

    Args:
        rag: LightRAG instance
        code_dict: Mapping of file path -> file content bytes
    """
    logger.info("=" * 50)
    logger.info("Graphing code files")
    logger.info(f"Starting code processing: {len(code_dict)} files")

    # Create queues for processing pipeline
    processing_queue = asyncio.Queue()
    storage_queue = asyncio.Queue()

    # Track processing progress
    total_files = len(code_dict)
    processed_count = 0
    stored_count = 0

    # Event to signal completion
    processing_done = asyncio.Event()
    storage_done = asyncio.Event()

    async def producer() -> None:
        """Producer coroutine: put all files into processing queue."""
        logger.info(f"Producer: Adding {total_files} files to processing queue")
        for code_path, file_content_bytes in code_dict.items():
            await processing_queue.put((code_path, file_content_bytes))
        logger.info("Producer: All files added to queue")
        # Signal that no more items will be added
        for _ in range(parallel_num):
            await processing_queue.put(None)  # Sentinel value to stop workers

    async def processing_worker(worker_id: int) -> None:
        """Worker coroutine: process files from queue and put results into storage queue."""
        nonlocal processed_count
        logger.info(f"Worker {worker_id}: Started")

        while True:
            try:
                # Get next file to process
                item = await processing_queue.get()

                # Check for sentinel value (end of processing)
                if item is None:
                    processing_queue.task_done()
                    break

                code_path, file_content_bytes = item

                try:
                    # Process the file
                    logger.info(f"Worker {worker_id}: Processing {code_path}")
                    result = await process_file(code_path, file_content_bytes)

                    # Put result into storage queue
                    await storage_queue.put(result)

                    # Update progress
                    processed_count += 1
                    logger.info(f"Worker {worker_id}: Processed {code_path} ({processed_count}/{total_files})")

                except Exception as e:
                    logger.error(f"Worker {worker_id}: Error processing {code_path}: {e}")
                    # Re-raise to stop processing on critical errors
                    raise
                finally:
                    processing_queue.task_done()

            except asyncio.CancelledError:
                logger.info(f"Worker {worker_id}: Cancelled")
                break
            except Exception as e:
                logger.error(f"Worker {worker_id}: Unexpected error: {e}")
                break

        logger.info(f"Worker {worker_id}: Finished")
        # Check if all workers are done
        if processed_count == total_files:
            processing_done.set()

    async def storage_worker() -> None:
        """Storage worker coroutine: process results from storage queue serially."""
        nonlocal stored_count
        logger.info("Storage worker: Started")

        while True:
            try:
                # Get next result to store
                result = await storage_queue.get()

                # Check for sentinel value (end of processing)
                if result is None:
                    storage_queue.task_done()
                    break

                try:
                    # Store the result
                    await store_file_result(rag, result)

                    # Update progress
                    stored_count += 1
                    logger.info(f"Storage worker: Stored {result['file_path']} ({stored_count}/{total_files})")

                except Exception as e:
                    logger.error(f"Storage worker: Error storing {result['file_path']}: {e}")
                    # Re-raise to stop processing on critical errors
                    raise
                finally:
                    storage_queue.task_done()

            except asyncio.CancelledError:
                logger.info("Storage worker: Cancelled")
                break
            except Exception as e:
                logger.error(f"Storage worker: Unexpected error: {e}")
                break

        logger.info("Storage worker: Finished")
        storage_done.set()

    # Start the processing pipeline
    logger.info(f"Starting processing pipeline with {parallel_num} workers")
    start_time = datetime.now(timezone.utc)

    # Create tasks
    producer_task = asyncio.create_task(producer())
    worker_tasks = [asyncio.create_task(processing_worker(i)) for i in range(parallel_num)]
    storage_task = asyncio.create_task(storage_worker())

    # Progress reporting task
    async def progress_reporter() -> None:
        """Periodically report processing progress."""
        while not processing_done.is_set() or not storage_done.is_set():
            await asyncio.sleep(20)  # Report every 20 seconds
            if not processing_done.is_set():
                logger.info(f"Progress: {processed_count}/{total_files} files processed")
            if not storage_done.is_set():
                logger.info(f"Progress: {stored_count}/{total_files} files stored")
        logger.info("Progress reporter: Finished")

    progress_task = asyncio.create_task(progress_reporter())

    try:
        # Wait for processing to complete
        await processing_done.wait()
        processing_time = datetime.now(timezone.utc)
        logger.info(f"All files processed ({processed_count}/{total_files}) in {(processing_time - start_time).total_seconds():.2f} seconds")

        # Signal storage worker to stop
        await storage_queue.put(None)

        # Wait for storage to complete
        await storage_done.wait()
        storage_time = datetime.now(timezone.utc)
        logger.info(f"All files stored ({stored_count}/{total_files}) in {(storage_time - processing_time).total_seconds():.2f} seconds")

        # Calculate total time
        total_time = datetime.now(timezone.utc)
        logger.info(f"Total processing time: {(total_time - start_time).total_seconds():.2f} seconds")

    except Exception as e:
        logger.error(f"Processing pipeline error: {e}")
        logger.error(f"Progress at error: {processed_count}/{total_files} processed, {stored_count}/{total_files} stored")

        # Cancel all tasks
        progress_task.cancel()
        for task in worker_tasks:
            task.cancel()
        storage_task.cancel()
        producer_task.cancel()

        # Log task cancellation status
        logger.error("Cancelling all tasks due to error")
        raise

    finally:
        # Cancel progress reporter
        progress_task.cancel()

        # Wait for all tasks to complete
        results = await asyncio.gather(
            *worker_tasks,
            storage_task,
            producer_task,
            progress_task,
            return_exceptions=True
        )

        # Check for exceptions in tasks
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                if i < len(worker_tasks):
                    logger.warning(f"Worker {i} raised exception: {result}")
                elif i == len(worker_tasks):
                    logger.warning(f"Storage worker raised exception: {result}")
                elif i == len(worker_tasks) + 1:
                    logger.warning(f"Producer raised exception: {result}")
                else:
                    logger.warning(f"Progress reporter raised exception: {result}")

    # Verify completion
    if processed_count == total_files and stored_count == total_files:
        logger.info("✓ All code processing completed successfully")
    else:
        logger.warning(f"⚠ Processing incomplete: {processed_count}/{total_files} processed, {stored_count}/{total_files} stored")

    logger.info("=" * 50 + "\n")

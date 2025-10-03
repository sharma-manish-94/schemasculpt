#!/usr/bin/env python3
"""
Hardware-Optimized Data Ingestion Script for SchemaSculpt AI Security RAG.
Optimized for Intel i5-8400 (6-core CPU) with intelligent resource management.
"""

import os
import sys
import multiprocessing as mp
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

try:
    from langchain_community.document_loaders import (
        DirectoryLoader, PyPDFLoader, TextLoader,
        UnstructuredMarkdownLoader, WebBaseLoader
    )
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from langchain_community.vectorstores import Chroma
    # Try new package first, fall back to old one
    try:
        from langchain_huggingface import HuggingFaceEmbeddings
    except ImportError:
        from langchain_community.embeddings import HuggingFaceEmbeddings
    DEPENDENCIES_AVAILABLE = True
except ImportError as e:
    DEPENDENCIES_AVAILABLE = False
    IMPORT_ERROR = str(e)

# Hardware-specific optimizations for Intel i5-8400 + NVIDIA 3060 12GB
CPU_CORES = 6  # Intel i5-8400 physical cores
MAX_WORKERS = min(4, CPU_CORES - 1)  # Leave 2 cores for system
BATCH_SIZE = 32  # Increased for GPU processing
GPU_BATCH_SIZE = 64  # Larger batches for GPU embeddings
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 150

# Paths
SCRIPT_DIR = Path(__file__).parent
KNOWLEDGE_BASE_DIR = SCRIPT_DIR / "knowledge_base"
VECTOR_STORE_DIR = SCRIPT_DIR / "vector_store"
COLLECTION_NAME = "security_knowledge_base"

# Security-focused web sources
WEB_SOURCES = [
    "https://owasp.org/www-project-api-security/",
    "https://cheatsheetseries.owasp.org/cheatsheets/REST_Security_Cheat_Sheet.html",
    "https://datatracker.ietf.org/doc/html/rfc6749",  # OAuth 2.0
    "https://datatracker.ietf.org/doc/html/rfc7519",  # JWT
    "https://openid.net/specs/openid-connect-core-1_0.html",
]

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(SCRIPT_DIR / 'ingest_data.log')
    ]
)
logger = logging.getLogger(__name__)


def check_dependencies() -> bool:
    """Check if all required dependencies are available."""
    if not DEPENDENCIES_AVAILABLE:
        logger.error(f"Missing dependencies: {IMPORT_ERROR}")
        logger.error("Install required packages:")
        logger.error("pip install langchain langchain-community chromadb sentence-transformers pypdf unstructured beautifulsoup4 html2text")
        return False
    return True


def check_system_resources() -> Dict[str, Any]:
    """Check available system resources and optimize accordingly."""
    gpu_available = False
    gpu_memory_gb = 0
    device = "cpu"

    # Check for GPU availability
    try:
        import torch
        if torch.cuda.is_available():
            gpu_available = True
            device = "cuda"
            gpu_memory_gb = torch.cuda.get_device_properties(0).total_memory / (1024**3)
            logger.info(f"GPU detected: {torch.cuda.get_device_name(0)} with {gpu_memory_gb:.1f}GB VRAM")
        else:
            logger.info("CUDA not available, using CPU")
    except ImportError:
        logger.info("PyTorch not available, using CPU")

    try:
        import psutil

        # Get memory info
        memory = psutil.virtual_memory()
        available_gb = memory.available / (1024**3)

        # Get CPU info
        cpu_count = psutil.cpu_count()
        cpu_percent = psutil.cpu_percent(interval=1)

        logger.info(f"System Resources: {available_gb:.1f}GB RAM available, {cpu_count} CPUs, {cpu_percent}% CPU usage")

        # Optimize batch sizes based on available hardware
        if gpu_available and gpu_memory_gb >= 8:
            # NVIDIA 3060 12GB - use GPU optimized settings
            batch_size = GPU_BATCH_SIZE
            embedding_batch_size = 128  # Larger batches for GPU
            logger.info(f"Using GPU-optimized settings for {gpu_memory_gb:.1f}GB GPU")
        elif available_gb >= 16:
            batch_size = BATCH_SIZE
            embedding_batch_size = 64
            logger.info("Using high-memory CPU settings")
        elif available_gb >= 8:
            batch_size = 24
            embedding_batch_size = 32
            logger.info("Using medium-memory CPU settings")
        else:
            batch_size = 16
            embedding_batch_size = 16
            logger.warning("Low memory detected, using conservative settings")

        return {
            "batch_size": batch_size,
            "embedding_batch_size": embedding_batch_size,
            "max_workers": min(MAX_WORKERS, cpu_count - 1),
            "available_memory_gb": available_gb,
            "gpu_available": gpu_available,
            "gpu_memory_gb": gpu_memory_gb,
            "device": device,
            "cpu_usage": cpu_percent
        }
    except ImportError:
        logger.warning("psutil not available, using default resource settings")
        device_settings = "cuda" if gpu_available else "cpu"
        return {
            "batch_size": GPU_BATCH_SIZE if gpu_available else BATCH_SIZE,
            "embedding_batch_size": 128 if gpu_available else 32,
            "max_workers": MAX_WORKERS,
            "available_memory_gb": 8.0,
            "gpu_available": gpu_available,
            "gpu_memory_gb": gpu_memory_gb,
            "device": device_settings,
            "cpu_usage": 0
        }


def load_local_documents() -> List[Any]:
    """Load documents from local knowledge base with optimized threading."""
    all_documents = []

    if not KNOWLEDGE_BASE_DIR.exists():
        logger.warning(f"Knowledge base directory not found: {KNOWLEDGE_BASE_DIR}")
        return all_documents

    logger.info(f"Loading documents from {KNOWLEDGE_BASE_DIR}")

    # Load different file types with optimized settings
    loaders = [
        {
            "name": "PDF",
            "glob": "**/*.pdf",
            "loader_cls": PyPDFLoader,
            "use_multithreading": True
        },
        {
            "name": "Markdown",
            "glob": "**/*.md",
            "loader_cls": UnstructuredMarkdownLoader,
            "use_multithreading": True
        },
        {
            "name": "Text",
            "glob": "**/*.txt",
            "loader_cls": TextLoader,
            "use_multithreading": True
        }
    ]

    for loader_config in loaders:
        try:
            logger.info(f"Loading {loader_config['name']} files...")
            loader = DirectoryLoader(
                str(KNOWLEDGE_BASE_DIR),
                glob=loader_config["glob"],
                loader_cls=loader_config["loader_cls"],
                show_progress=True,
                use_multithreading=loader_config["use_multithreading"],
                max_concurrency=MAX_WORKERS
            )
            documents = loader.load()
            all_documents.extend(documents)
            logger.info(f"Loaded {len(documents)} {loader_config['name']} document(s)")
        except Exception as e:
            logger.error(f"Error loading {loader_config['name']} files: {e}")

    return all_documents


def load_web_documents(max_workers: int = 2) -> List[Any]:
    """Load documents from web sources with controlled concurrency."""
    web_documents = []

    if not WEB_SOURCES:
        return web_documents

    logger.info(f"Loading {len(WEB_SOURCES)} document(s) from web sources...")

    def load_single_url(url: str) -> Optional[Any]:
        """Load a single URL with error handling."""
        try:
            logger.info(f"Loading: {url}")
            loader = WebBaseLoader([url])
            docs = loader.load()
            logger.info(f"Successfully loaded {url}")
            return docs
        except Exception as e:
            logger.error(f"Failed to load {url}: {e}")
            return None

    # Use ThreadPoolExecutor for controlled concurrency
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_url = {executor.submit(load_single_url, url): url for url in WEB_SOURCES}

        for future in as_completed(future_to_url):
            url = future_to_url[future]
            try:
                docs = future.result(timeout=60)  # 60 second timeout per URL
                if docs:
                    web_documents.extend(docs)
            except Exception as e:
                logger.error(f"Error processing {url}: {e}")

    logger.info(f"Loaded {len(web_documents)} web document(s)")
    return web_documents


def optimize_text_splitting(documents: List[Any], batch_size: int) -> List[Any]:
    """Split documents into chunks with CPU-optimized processing."""
    if not documents:
        return []

    logger.info(f"Splitting {len(documents)} documents into chunks...")

    # Use optimized splitter settings
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=len,
        separators=["\n\n", "\n", " ", ""]
    )

    # Process in batches to manage memory
    all_chunks = []
    for i in range(0, len(documents), batch_size):
        batch = documents[i:i + batch_size]
        logger.info(f"Processing batch {i//batch_size + 1}/{(len(documents) + batch_size - 1)//batch_size}")

        try:
            chunks = text_splitter.split_documents(batch)
            all_chunks.extend(chunks)
        except Exception as e:
            logger.error(f"Error splitting batch {i//batch_size + 1}: {e}")

    logger.info(f"Split into {len(all_chunks)} text chunks")
    return all_chunks


def create_embeddings_and_vectorstore(chunks: List[Any], resources: Dict[str, Any]) -> bool:
    """Create embeddings and vector store with GPU/CPU optimization."""
    if not chunks:
        logger.error("No chunks to process")
        return False

    device = resources["device"]
    embedding_batch_size = resources["embedding_batch_size"]
    gpu_available = resources["gpu_available"]

    logger.info(f"Initializing embedding model ({device.upper()}-optimized)...")

    try:
        # GPU/CPU-optimized embedding configuration
        model_kwargs = {
            'device': device,
            'trust_remote_code': False
        }

        encode_kwargs = {
            'normalize_embeddings': True,
            'batch_size': embedding_batch_size,
            'show_progress_bar': True,
            'convert_to_tensor': True
        }

        # Add device to encode_kwargs if supported
        if device == "cuda":
            encode_kwargs['device'] = device

        embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs=model_kwargs,
            encode_kwargs=encode_kwargs
        )

        logger.info(f"Creating vector store with {len(chunks)} chunks...")

        # Create vector store with progress tracking
        VECTOR_STORE_DIR.mkdir(parents=True, exist_ok=True)

        # Optimize vector batch size based on hardware
        if gpu_available:
            # GPU can handle larger batches efficiently
            vector_batch_size = min(200, len(chunks))
            logger.info(f"Using GPU-optimized vector batch size: {vector_batch_size}")
        else:
            # CPU processing - smaller batches
            vector_batch_size = min(100, embedding_batch_size * 2)
            logger.info(f"Using CPU-optimized vector batch size: {vector_batch_size}")

        if len(chunks) <= vector_batch_size:
            # Process all at once if small enough
            logger.info("Processing all chunks in single batch")
            db = Chroma.from_documents(
                chunks,
                embeddings,
                persist_directory=str(VECTOR_STORE_DIR),
                collection_name=COLLECTION_NAME
            )
        else:
            # Process in batches for large datasets
            logger.info(f"Processing {len(chunks)} chunks in batches of {vector_batch_size}")
            db = None
            for i in range(0, len(chunks), vector_batch_size):
                batch = chunks[i:i + vector_batch_size]
                batch_num = i//vector_batch_size + 1
                total_batches = (len(chunks) + vector_batch_size - 1)//vector_batch_size
                logger.info(f"Processing embedding batch {batch_num}/{total_batches} ({len(batch)} chunks)")

                try:
                    if db is None:
                        db = Chroma.from_documents(
                            batch,
                            embeddings,
                            persist_directory=str(VECTOR_STORE_DIR),
                            collection_name=COLLECTION_NAME
                        )
                    else:
                        db.add_documents(batch)

                    # Force garbage collection for GPU memory management
                    if gpu_available:
                        import gc
                        gc.collect()
                        try:
                            import torch
                            torch.cuda.empty_cache()
                        except:
                            pass

                except Exception as e:
                    logger.error(f"Error processing batch {batch_num}: {e}")
                    # Continue with next batch rather than failing completely
                    continue

        # Persist the database
        if hasattr(db, 'persist'):
            db.persist()

        logger.info(f"Vector store created successfully in '{VECTOR_STORE_DIR}'")
        return True

    except Exception as e:
        logger.error(f"Failed to create vector store: {e}")
        return False


def main():
    """Main ingestion workflow with hardware optimization."""
    logger.info("Starting SchemaSculpt AI Security Knowledge Base Ingestion")
    logger.info(f"Hardware: Intel i5-8400 (6 cores) optimization enabled")

    # Check dependencies
    if not check_dependencies():
        return 1

    # Check system resources and optimize
    resources = check_system_resources()
    batch_size = resources["batch_size"]
    max_workers = resources["max_workers"]
    device = resources["device"]
    gpu_available = resources["gpu_available"]

    logger.info(f"Using optimized settings: device={device}, batch_size={batch_size}, max_workers={max_workers}")
    if gpu_available:
        logger.info(f"GPU acceleration enabled with {resources['gpu_memory_gb']:.1f}GB VRAM")

    start_time = time.time()

    try:
        # Load all documents
        all_documents = []

        # Load local documents
        local_docs = load_local_documents()
        all_documents.extend(local_docs)

        # Load web documents (use fewer workers for web requests)
        web_docs = load_web_documents(max_workers=min(2, max_workers))
        all_documents.extend(web_docs)

        if not all_documents:
            logger.error("No documents found to process. Check your knowledge base directory and internet connection.")
            return 1

        logger.info(f"Total documents loaded: {len(all_documents)}")

        # Split documents into chunks
        chunks = optimize_text_splitting(all_documents, batch_size)

        if not chunks:
            logger.error("No chunks created from documents")
            return 1

        # Create embeddings and vector store
        success = create_embeddings_and_vectorstore(chunks, resources)

        if not success:
            logger.error("Failed to create vector store")
            return 1

        elapsed_time = time.time() - start_time
        logger.info(f"Ingestion completed successfully in {elapsed_time:.2f} seconds")
        logger.info(f"Processed {len(all_documents)} documents into {len(chunks)} chunks")
        logger.info(f"Vector store ready for RAG-enhanced security analysis")

        return 0

    except KeyboardInterrupt:
        logger.info("Ingestion interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
"""
RAG Service for SchemaSculpt AI - Security Analysis Context Retrieval.
Provides intelligent context retrieval for security analysis using vector embeddings.
"""

import os
from typing import List, Dict, Any, Optional
from pathlib import Path

try:
    import chromadb
    # Try new package first, fall back to old one
    try:
        from langchain_huggingface import HuggingFaceEmbeddings
    except ImportError:
        from langchain_community.embeddings import HuggingFaceEmbeddings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False

from ..core.config import settings
from ..core.logging import get_logger
from ..core.exceptions import SchemaSculptException


class RAGService:
    """
    RAG service for retrieving security-related context from knowledge base.
    Integrates with ChromaDB for vector search and HuggingFace embeddings.
    """

    def __init__(self):
        self.logger = get_logger("rag_service")
        self.vector_store_dir = Path(settings.ai_service_data_dir) / "vector_store"
        self.embedding_model = None
        self.vector_store = None
        self.collection_name = "security_knowledge_base"

        if not CHROMADB_AVAILABLE:
            self.logger.warning("ChromaDB dependencies not available. RAG service disabled.")
            return

        self._initialize_embeddings()
        self._initialize_vector_store()

    def _initialize_embeddings(self) -> None:
        """Initialize embedding model with GPU/CPU optimization."""
        try:
            # Check for GPU availability
            device = "cpu"
            batch_size = 32
            model_kwargs = {
                'device': 'cpu',
                'trust_remote_code': False
            }

            try:
                import torch
                if torch.cuda.is_available():
                    device = "cuda"
                    batch_size = 64  # Larger batch for GPU
                    model_kwargs = {
                        'device': 'cuda',
                        'trust_remote_code': False
                    }
                    self.logger.info(f"GPU detected: {torch.cuda.get_device_name(0)}, using CUDA acceleration")
                else:
                    self.logger.info("CUDA not available, using CPU")
            except ImportError:
                self.logger.info("PyTorch not available, using CPU")

            encode_kwargs = {
                'normalize_embeddings': True,
                'batch_size': batch_size,
                'convert_to_tensor': True
            }

            # Add device to encode_kwargs if supported
            if device == "cuda":
                encode_kwargs['device'] = device

            # Use smaller, faster embedding model for better performance
            self.embedding_model = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L12-v2",  # Smaller, faster model
                model_kwargs=model_kwargs,
                encode_kwargs=encode_kwargs
            )
            self.logger.info(f"Embedding model initialized successfully on {device.upper()}")
        except Exception as e:
            self.logger.error(f"Failed to initialize embedding model: {e}")
            raise SchemaSculptException(
                "RAG_INIT_ERROR",
                f"Failed to initialize RAG embedding model: {e}"
            )

    def _initialize_vector_store(self) -> None:
        """Initialize ChromaDB vector store."""
        try:
            if not self.vector_store_dir.exists():
                self.logger.warning(f"Vector store directory not found: {self.vector_store_dir}")
                return

            client = chromadb.PersistentClient(path=str(self.vector_store_dir))

            # Try to get existing collection, create if doesn't exist
            try:
                self.vector_store = client.get_collection(name=self.collection_name)
                self.logger.info(f"Loaded existing vector store collection: {self.collection_name}")
            except ValueError:
                # Collection doesn't exist - try legacy name for backward compatibility
                try:
                    self.vector_store = client.get_collection(name="langchain")
                    self.logger.info("Loaded legacy 'langchain' collection")
                except ValueError:
                    self.logger.warning("No vector store collection found. Run ingest_data.py first.")

        except Exception as e:
            self.logger.error(f"Failed to initialize vector store: {e}")
            raise SchemaSculptException(
                "RAG_INIT_ERROR",
                f"Failed to initialize vector store: {e}"
            )

    async def retrieve_security_context(self, query: str, n_results: int = 5) -> Dict[str, Any]:
        """
        Retrieve security-related context for the given query.

        Args:
            query: Security analysis query
            n_results: Number of relevant documents to retrieve

        Returns:
            Dictionary containing retrieved context and metadata
        """
        if not self.is_available():
            return {
                "context": "RAG service not available. Performing analysis without additional context.",
                "sources": [],
                "relevance_scores": []
            }

        try:
            # Generate embedding for the query
            results = self.vector_store.query(
                query_texts=[query],
                n_results=n_results,
                include=["documents", "metadatas", "distances"]
            )

            if not results['documents'] or not results['documents'][0]:
                return {
                    "context": "No relevant security context found in knowledge base.",
                    "sources": [],
                    "relevance_scores": []
                }

            # Combine retrieved documents with source information
            documents = results['documents'][0]
            metadatas = results.get('metadatas', [[{}] * len(documents)])[0]
            distances = results.get('distances', [[1.0] * len(documents)])[0]

            # Format context with source attribution
            context_parts = []
            sources = []

            for i, (doc, metadata, distance) in enumerate(zip(documents, metadatas, distances)):
                source = metadata.get('source', f'Document {i+1}')
                sources.append(source)

                context_parts.append(f"[Source: {source}]\n{doc}")

            combined_context = "\n\n---\n\n".join(context_parts)

            # Convert distances to relevance scores (lower distance = higher relevance)
            relevance_scores = [max(0, 1 - d) for d in distances]

            self.logger.info(f"Retrieved {len(documents)} relevant documents for security analysis")

            return {
                "context": combined_context,
                "sources": sources,
                "relevance_scores": relevance_scores,
                "total_documents": len(documents)
            }

        except Exception as e:
            self.logger.error(f"Error retrieving security context: {e}")
            return {
                "context": f"Error retrieving context: {e}",
                "sources": [],
                "relevance_scores": []
            }

    def is_available(self) -> bool:
        """Check if RAG service is available and properly initialized."""
        return (
            CHROMADB_AVAILABLE and
            self.embedding_model is not None and
            self.vector_store is not None
        )

    async def get_knowledge_base_stats(self) -> Dict[str, Any]:
        """Get statistics about the knowledge base."""
        if not self.is_available():
            return {
                "available": False,
                "error": "RAG service not initialized"
            }

        try:
            count = self.vector_store.count()
            return {
                "available": True,
                "document_count": count,
                "collection_name": self.collection_name,
                "vector_store_path": str(self.vector_store_dir)
            }
        except Exception as e:
            self.logger.error(f"Error getting knowledge base stats: {e}")
            return {
                "available": False,
                "error": str(e)
            }
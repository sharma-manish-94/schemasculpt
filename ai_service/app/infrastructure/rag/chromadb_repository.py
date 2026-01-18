"""
ChromaDB RAG Repository.

Provides a ChromaDB implementation of IRAGRepository.
Wraps the existing RAGService functionality with the new domain interface.
"""

import hashlib
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.domain.interfaces.rag_repository import (
    IRAGRepository,
    RAGDocument,
    RAGQueryResult,
)

logger = logging.getLogger(__name__)

# Check if ChromaDB dependencies are available
try:
    import chromadb
    from sentence_transformers import SentenceTransformer

    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    logger.warning(
        "ChromaDB dependencies not available. "
        "Install with: pip install chromadb sentence-transformers"
    )


class ChromaDBRepository(IRAGRepository):
    """
    ChromaDB implementation of IRAGRepository.

    Features:
    - Dual knowledge bases (attacker_kb, governance_kb)
    - Local embeddings with sentence-transformers
    - Persistent storage with ChromaDB
    - Lazy initialization of collections

    Usage:
        repo = ChromaDBRepository(persist_directory="/data/chroma_db")
        result = await repo.query(
            query="SQL injection vulnerabilities",
            collection="attacker_kb",
            n_results=5
        )
    """

    # Default collection names
    ATTACKER_KB = "attacker_knowledge"
    GOVERNANCE_KB = "governance_knowledge"
    VALID_COLLECTIONS = {ATTACKER_KB, GOVERNANCE_KB, "attacker_kb", "governance_kb"}

    def __init__(
        self,
        persist_directory: str,
        embedding_model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
    ):
        """
        Initialize the ChromaDB repository.

        Args:
            persist_directory: Directory for persistent storage.
            embedding_model_name: Name of the sentence-transformers model.
        """
        self._persist_dir = Path(persist_directory)
        self._embedding_model_name = embedding_model_name
        self._client: Optional[Any] = None
        self._embedding_model: Optional[Any] = None
        self._collections: Dict[str, Any] = {}

        if CHROMADB_AVAILABLE:
            self._initialize()

    def _initialize(self) -> None:
        """Initialize ChromaDB client and embedding model."""
        try:
            # Ensure directory exists
            self._persist_dir.mkdir(parents=True, exist_ok=True)

            # Initialize ChromaDB client
            self._client = chromadb.PersistentClient(path=str(self._persist_dir))
            logger.info(f"ChromaDB initialized at {self._persist_dir}")

            # Initialize embedding model
            self._embedding_model = SentenceTransformer(self._embedding_model_name)
            device = str(self._embedding_model.device)
            logger.info(f"Embedding model loaded on {device}")

            # Try to load existing collections
            self._load_collections()

        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
            self._client = None

    def _load_collections(self) -> None:
        """Load existing collections if available."""
        if self._client is None:
            return

        for name in [self.ATTACKER_KB, self.GOVERNANCE_KB]:
            try:
                self._collections[name] = self._client.get_collection(name=name)
                logger.info(f"Loaded collection: {name}")
            except Exception:
                logger.debug(f"Collection {name} not found (will be created on demand)")

    def _normalize_collection_name(self, collection: str) -> str:
        """Normalize collection name to internal format."""
        mapping = {
            "attacker_kb": self.ATTACKER_KB,
            "governance_kb": self.GOVERNANCE_KB,
        }
        return mapping.get(collection, collection)

    def _get_or_create_collection(self, collection: str) -> Any:
        """Get or create a collection."""
        normalized = self._normalize_collection_name(collection)

        if normalized in self._collections:
            return self._collections[normalized]

        if self._client is None:
            raise RuntimeError("ChromaDB client not initialized")

        try:
            coll = self._client.get_collection(name=normalized)
        except Exception:
            coll = self._client.create_collection(
                name=normalized,
                metadata={"description": f"{normalized} Knowledge Base"},
            )
            logger.info(f"Created collection: {normalized}")

        self._collections[normalized] = coll
        return coll

    def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text."""
        if self._embedding_model is None:
            raise RuntimeError("Embedding model not initialized")
        return self._embedding_model.encode([text])[0].tolist()

    def _generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        if self._embedding_model is None:
            raise RuntimeError("Embedding model not initialized")
        return self._embedding_model.encode(texts).tolist()

    async def query(
        self,
        query: str,
        collection: str,
        n_results: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> RAGQueryResult:
        """Query the knowledge base for relevant documents."""
        if not self.is_available():
            return RAGQueryResult(
                documents=[],
                scores=[],
                query=query,
                collection=collection,
            )

        try:
            normalized = self._normalize_collection_name(collection)

            if normalized not in self._collections:
                return RAGQueryResult(
                    documents=[],
                    scores=[],
                    query=query,
                    collection=collection,
                )

            coll = self._collections[normalized]
            query_embedding = self._generate_embedding(query)

            results = coll.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=filter_metadata,
                include=["documents", "metadatas", "distances"],
            )

            # Convert to domain objects
            documents = []
            scores = []

            if results["documents"] and results["documents"][0]:
                docs = results["documents"][0]
                metadatas = results.get("metadatas", [[{}] * len(docs)])[0]
                distances = results.get("distances", [[1.0] * len(docs)])[0]
                ids = results.get("ids", [[f"doc_{i}" for i in range(len(docs))]])[0]

                for doc_id, doc, metadata, distance in zip(
                    ids, docs, metadatas, distances
                ):
                    documents.append(
                        RAGDocument(
                            id=doc_id,
                            content=doc,
                            metadata=metadata or {},
                        )
                    )
                    # Convert distance to similarity score
                    scores.append(max(0, 1 - distance))

            logger.debug(f"Query returned {len(documents)} documents from {normalized}")

            return RAGQueryResult(
                documents=documents,
                scores=scores,
                query=query,
                collection=normalized,
            )

        except Exception as e:
            logger.error(f"Error querying {collection}: {e}")
            return RAGQueryResult(
                documents=[],
                scores=[],
                query=query,
                collection=collection,
            )

    async def add_documents(
        self,
        documents: List[str],
        collection: str,
        ids: Optional[List[str]] = None,
        metadata: Optional[List[Dict[str, Any]]] = None,
        **kwargs: Any,
    ) -> int:
        """Add documents to the knowledge base."""
        if not self.is_available():
            return 0

        try:
            coll = self._get_or_create_collection(collection)

            # Generate IDs if not provided
            if ids is None:
                ids = [hashlib.md5(doc.encode()).hexdigest() for doc in documents]

            # Generate embeddings
            embeddings = self._generate_embeddings(documents)

            # Prepare metadata
            if metadata is None:
                metadata = [{}] * len(documents)

            coll.add(
                documents=documents,
                embeddings=embeddings,
                metadatas=metadata,
                ids=ids,
            )

            logger.info(f"Added {len(documents)} documents to {collection}")
            return len(documents)

        except Exception as e:
            logger.error(f"Error adding documents to {collection}: {e}")
            return 0

    async def delete_documents(
        self,
        collection: str,
        ids: Optional[List[str]] = None,
        filter_metadata: Optional[Dict[str, Any]] = None,
    ) -> int:
        """Delete documents from the knowledge base."""
        if not self.is_available():
            return 0

        try:
            normalized = self._normalize_collection_name(collection)
            if normalized not in self._collections:
                return 0

            coll = self._collections[normalized]

            if ids:
                coll.delete(ids=ids)
                return len(ids)
            elif filter_metadata:
                coll.delete(where=filter_metadata)
                return -1  # Unknown count
            else:
                return 0

        except Exception as e:
            logger.error(f"Error deleting documents from {collection}: {e}")
            return 0

    async def get_collections(self) -> List[str]:
        """Get list of available collections."""
        if self._client is None:
            return []

        try:
            collections = self._client.list_collections()
            return [c.name for c in collections]
        except Exception as e:
            logger.error(f"Error listing collections: {e}")
            return []

    async def get_collection_stats(self, collection: str) -> Dict[str, Any]:
        """Get statistics for a collection."""
        normalized = self._normalize_collection_name(collection)

        if normalized not in self._collections:
            return {
                "name": normalized,
                "available": False,
                "document_count": 0,
            }

        try:
            coll = self._collections[normalized]
            count = coll.count()

            return {
                "name": normalized,
                "available": True,
                "document_count": count,
                "metadata": coll.metadata,
            }

        except Exception as e:
            logger.error(f"Error getting stats for {collection}: {e}")
            return {
                "name": normalized,
                "available": False,
                "error": str(e),
            }

    def is_available(self) -> bool:
        """Check if the RAG service is available."""
        return (
            CHROMADB_AVAILABLE
            and self._client is not None
            and self._embedding_model is not None
        )

    async def health_check(self) -> bool:
        """Check if the RAG backend is healthy."""
        if not CHROMADB_AVAILABLE:
            return False

        try:
            # Try to list collections as a health check
            if self._client is not None:
                self._client.list_collections()
                return True
            return False
        except Exception as e:
            logger.error(f"RAG health check failed: {e}")
            return False

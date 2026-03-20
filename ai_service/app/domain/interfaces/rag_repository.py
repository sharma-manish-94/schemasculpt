"""
RAG (Retrieval-Augmented Generation) Repository Interface.

Defines the contract for RAG/vector store implementations (ChromaDB, Pinecone, etc.).
This abstraction allows swapping vector databases without changing service code.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class RAGDocument:
    """Represents a document in the RAG knowledge base."""

    id: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    embedding: Optional[List[float]] = None


@dataclass
class RAGQueryResult:
    """Result from a RAG query."""

    documents: List[RAGDocument]
    scores: List[float]
    query: str
    collection: str


class IRAGRepository(ABC):
    """
    Abstract interface for RAG (Retrieval-Augmented Generation) repositories.

    All vector store implementations must implement this interface.
    This supports the Dual-RAG architecture (Attacker KB + Governance KB).

    Usage:
        # In service layer
        class SecurityService:
            def __init__(self, rag: IRAGRepository):
                self._rag = rag

            async def get_attack_context(self, vulnerability: str) -> str:
                result = await self._rag.query(
                    query=vulnerability,
                    collection="attacker_kb",
                    n_results=5
                )
                return self._format_context(result.documents)
    """

    @abstractmethod
    async def query(
        self,
        query: str,
        collection: str,
        n_results: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> RAGQueryResult:
        """
        Query the knowledge base for relevant documents.

        Args:
            query: The search query text.
            collection: Name of the collection to search (e.g., "attacker_kb", "governance_kb").
            n_results: Maximum number of results to return.
            filter_metadata: Optional metadata filters.
            **kwargs: Additional provider-specific parameters.

        Returns:
            RAGQueryResult containing matching documents and similarity scores.
        """

    @abstractmethod
    async def add_documents(
        self,
        documents: List[str],
        collection: str,
        ids: Optional[List[str]] = None,
        metadata: Optional[List[Dict[str, Any]]] = None,
        **kwargs: Any,
    ) -> int:
        """
        Add documents to the knowledge base.

        Args:
            documents: List of document texts to add.
            collection: Name of the collection to add to.
            ids: Optional list of document IDs. Auto-generated if None.
            metadata: Optional list of metadata dicts for each document.
            **kwargs: Additional provider-specific parameters.

        Returns:
            Number of documents added.
        """

    @abstractmethod
    async def delete_documents(
        self,
        collection: str,
        ids: Optional[List[str]] = None,
        filter_metadata: Optional[Dict[str, Any]] = None,
    ) -> int:
        """
        Delete documents from the knowledge base.

        Args:
            collection: Name of the collection.
            ids: Optional list of document IDs to delete.
            filter_metadata: Optional metadata filter for bulk deletion.

        Returns:
            Number of documents deleted.
        """

    @abstractmethod
    async def get_collections(self) -> List[str]:
        """
        Get list of available collections.

        Returns:
            List of collection names.
        """

    @abstractmethod
    async def get_collection_stats(self, collection: str) -> Dict[str, Any]:
        """
        Get statistics for a collection.

        Args:
            collection: Name of the collection.

        Returns:
            Dictionary with collection statistics (document count, etc.).
        """

    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if the RAG service is available.

        Returns:
            True if available, False otherwise.
        """

    @abstractmethod
    async def health_check(self) -> bool:
        """
        Check if the RAG backend is healthy.

        Returns:
            True if healthy, False otherwise.
        """

"""
RAG Service for SchemaSculpt AI - Dual Expert Knowledge Bases

This is THE game-changer that transforms SchemaSculpt from an AI tool to an AI security expert.

Two Specialized Knowledge Bases:
1. Attacker Knowledge Base: Offensive security (OWASP, MITRE ATT&CK, exploit patterns)
2. Governance Knowledge Base: Risk frameworks (CVSS, DREAD), compliance (GDPR, HIPAA)

Each agent consults its specialized KB, becoming a domain expert.
"""

import hashlib
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import chromadb
    from sentence_transformers import SentenceTransformer

    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False

from ..core.config import settings
from ..core.exceptions import SchemaSculptException
from ..core.logging import get_logger


class RAGService:
    """
    Enhanced RAG service with dual specialized knowledge bases

    Architecture:
    - Attacker KB: For ThreatModelingAgent (think like a hacker)
    - Governance KB: For SecurityReporterAgent (think like a CISO)
    - Local embeddings: sentence-transformers (no API calls, free)
    - Vector store: ChromaDB (persistent, local)
    """

    def __init__(self):
        self.logger = get_logger("rag_service")
        self.vector_store_dir = Path(settings.ai_service_data_dir) / "vector_store"

        # Dual knowledge bases
        self.attacker_kb = None
        self.governance_kb = None
        self.embedding_model = None

        if not CHROMADB_AVAILABLE:
            self.logger.warning(
                "ChromaDB dependencies not available. RAG service disabled."
            )
            self.logger.warning(
                "Install with: pip install chromadb sentence-transformers"
            )
            return

        self._initialize_embeddings()
        self._initialize_vector_stores()

    def _initialize_embeddings(self) -> None:
        """Initialize sentence-transformers embedding model with GPU/CPU optimization."""
        try:
            # Use direct sentence-transformers for better control
            model_name = "sentence-transformers/all-MiniLM-L6-v2"

            self.embedding_model = SentenceTransformer(model_name)

            # Check device
            device = str(self.embedding_model.device)
            self.logger.info(f"Embedding model '{model_name}' initialized on {device}")

        except Exception as e:
            self.logger.error(f"Failed to initialize embedding model: {e}")
            raise SchemaSculptException(
                "RAG_INIT_ERROR", f"Failed to initialize RAG embedding model: {e}"
            )

    def _initialize_vector_stores(self) -> None:
        """Initialize ChromaDB vector stores for dual knowledge bases."""
        try:
            self.vector_store_dir.mkdir(parents=True, exist_ok=True)

            client = chromadb.PersistentClient(path=str(self.vector_store_dir))

            # Initialize Attacker Knowledge Base (for ThreatModelingAgent)
            try:
                self.attacker_kb = client.get_collection(name="attacker_knowledge")
                self.logger.info("Loaded existing Attacker Knowledge Base")
            except Exception:
                self.logger.warning(
                    "Attacker KB not found. Will be created during ingestion."
                )
                self.attacker_kb = None

            # Initialize Governance Knowledge Base (for SecurityReporterAgent)
            try:
                self.governance_kb = client.get_collection(name="governance_knowledge")
                self.logger.info("Loaded existing Governance Knowledge Base")
            except Exception:
                self.logger.warning(
                    "Governance KB not found. Will be created during ingestion."
                )
                self.governance_kb = None

        except Exception as e:
            self.logger.error(f"Failed to initialize vector stores: {e}")
            raise SchemaSculptException(
                "RAG_INIT_ERROR", f"Failed to initialize vector stores: {e}"
            )

    async def retrieve_security_context(
        self, query: str, n_results: int = 5
    ) -> Dict[str, Any]:
        """
        Retrieve security context from knowledge bases (backward compatibility wrapper).

        Queries the Attacker Knowledge Base for security analysis.
        This is a compatibility method for existing endpoints.

        Args:
            query: Security analysis query
            n_results: Number of relevant documents to retrieve

        Returns:
            Dictionary with security context
        """
        return await self.query_attacker_knowledge(query, n_results)

    async def query_attacker_knowledge(
        self, query: str, n_results: int = 5
    ) -> Dict[str, Any]:
        """
        Query the Attacker Knowledge Base (offensive security expertise).

        This KB contains:
        - OWASP API Security Top 10
        - MITRE ATT&CK patterns
        - Real-world exploit techniques
        - Attack methodology documentation

        Used by: ThreatModelingAgent to think like a penetration tester

        Args:
            query: Threat modeling query
            n_results: Number of relevant attack patterns to retrieve

        Returns:
            Dictionary with offensive security context
        """
        if not CHROMADB_AVAILABLE or self.attacker_kb is None:
            return {
                "context": "Attacker KB not available. Analysis based on LLM knowledge only.",
                "sources": [],
                "relevance_scores": [],
            }

        try:
            # Generate embedding for query
            query_embedding = self.embedding_model.encode([query])[0].tolist()

            # Query ChromaDB
            results = self.attacker_kb.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                include=["documents", "metadatas", "distances"],
            )

            return self._format_rag_results(results, "Attacker KB")

        except Exception as e:
            self.logger.error(f"Error querying Attacker KB: {e}")
            return {
                "context": f"Error retrieving attack patterns: {e}",
                "sources": [],
                "relevance_scores": [],
            }

    async def query_governance_knowledge(
        self, query: str, n_results: int = 5
    ) -> Dict[str, Any]:
        """
        Query the Governance Knowledge Base (defensive security & compliance).

        This KB contains:
        - CVSS scoring methodology
        - DREAD risk framework
        - GDPR, HIPAA, PCI-DSS compliance requirements
        - Security best practices & standards

        Used by: SecurityReporterAgent to assess business impact like a CISO

        Args:
            query: Risk assessment or compliance query
            n_results: Number of relevant governance docs to retrieve

        Returns:
            Dictionary with governance/compliance context
        """
        if not CHROMADB_AVAILABLE or self.governance_kb is None:
            return {
                "context": "Governance KB not available. Analysis based on LLM knowledge only.",
                "sources": [],
                "relevance_scores": [],
            }

        try:
            # Generate embedding for query
            query_embedding = self.embedding_model.encode([query])[0].tolist()

            # Query ChromaDB
            results = self.governance_kb.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                include=["documents", "metadatas", "distances"],
            )

            return self._format_rag_results(results, "Governance KB")

        except Exception as e:
            self.logger.error(f"Error querying Governance KB: {e}")
            return {
                "context": f"Error retrieving governance context: {e}",
                "sources": [],
                "relevance_scores": [],
            }

    def _format_rag_results(
        self, results: Dict[str, Any], kb_name: str
    ) -> Dict[str, Any]:
        """Format RAG query results into standardized response."""
        if not results["documents"] or not results["documents"][0]:
            return {
                "context": f"No relevant context found in {kb_name}.",
                "sources": [],
                "relevance_scores": [],
            }

        documents = results["documents"][0]
        metadatas = results.get("metadatas", [[{}] * len(documents)])[0]
        distances = results.get("distances", [[1.0] * len(documents)])[0]

        # Format context with source attribution
        context_parts = []
        sources = []

        for i, (doc, metadata, distance) in enumerate(
            zip(documents, metadatas, distances)
        ):
            source = metadata.get("source", f"{kb_name} Document {i+1}")
            sources.append(source)
            context_parts.append(f"[Source: {source}]\n{doc}")

        combined_context = "\n\n---\n\n".join(context_parts)

        # Convert distances to relevance scores (lower distance = higher relevance)
        relevance_scores = [max(0, 1 - d) for d in distances]

        self.logger.info(
            f"Retrieved {len(documents)} documents from {kb_name} "
            f"(avg relevance: {sum(relevance_scores)/len(relevance_scores):.2f})"
        )

        return {
            "context": combined_context,
            "sources": sources,
            "relevance_scores": relevance_scores,
            "total_documents": len(documents),
            "knowledge_base": kb_name,
        }

    def is_available(self) -> bool:
        """Check if RAG service is available and properly initialized."""
        return (
            CHROMADB_AVAILABLE
            and self.embedding_model is not None
            and (self.attacker_kb is not None or self.governance_kb is not None)
        )

    def attacker_kb_available(self) -> bool:
        """Check if Attacker Knowledge Base is available."""
        return CHROMADB_AVAILABLE and self.attacker_kb is not None

    def governance_kb_available(self) -> bool:
        """Check if Governance Knowledge Base is available."""
        return CHROMADB_AVAILABLE and self.governance_kb is not None

    async def get_knowledge_base_stats(self) -> Dict[str, Any]:
        """Get statistics about both knowledge bases."""
        if not CHROMADB_AVAILABLE:
            return {"available": False, "error": "ChromaDB not installed"}

        try:
            stats = {
                "available": True,
                "vector_store_path": str(self.vector_store_dir),
                "attacker_kb": {
                    "available": self.attacker_kb is not None,
                    "document_count": (
                        self.attacker_kb.count() if self.attacker_kb else 0
                    ),
                    "description": "Offensive security expertise (OWASP, MITRE ATT&CK)",
                },
                "governance_kb": {
                    "available": self.governance_kb is not None,
                    "document_count": (
                        self.governance_kb.count() if self.governance_kb else 0
                    ),
                    "description": "Risk frameworks and compliance (CVSS, DREAD, GDPR)",
                },
                "total_documents": 0,
            }

            stats["total_documents"] = (
                stats["attacker_kb"]["document_count"]
                + stats["governance_kb"]["document_count"]
            )

            return stats

        except Exception as e:
            self.logger.error(f"Error getting knowledge base stats: {e}")
            return {"available": False, "error": str(e)}

    def ingest_documents(
        self,
        documents: List[str],
        metadatas: List[Dict[str, Any]],
        knowledge_base: str = "attacker",
    ) -> Dict[str, Any]:
        """
        Ingest documents into specified knowledge base.

        Args:
            documents: List of document texts
            metadatas: List of metadata dicts (must match documents length)
            knowledge_base: "attacker" or "governance"

        Returns:
            Ingestion result statistics
        """
        if not CHROMADB_AVAILABLE or self.embedding_model is None:
            return {"success": False, "error": "RAG service not available"}

        try:
            # Generate embeddings
            self.logger.info(f"Generating embeddings for {len(documents)} documents...")
            embeddings = self.embedding_model.encode(documents).tolist()

            # Generate unique IDs
            doc_ids = [hashlib.md5(doc.encode()).hexdigest() for doc in documents]

            # Get or create target collection
            client = chromadb.PersistentClient(path=str(self.vector_store_dir))

            collection_name = (
                "attacker_knowledge"
                if knowledge_base == "attacker"
                else "governance_knowledge"
            )

            try:
                collection = client.get_collection(name=collection_name)
                self.logger.info(f"Using existing collection: {collection_name}")
            except Exception:
                collection = client.create_collection(
                    name=collection_name,
                    metadata={
                        "description": f"{knowledge_base.title()} Knowledge Base"
                    },
                )
                self.logger.info(f"Created new collection: {collection_name}")

            # Add documents
            collection.add(
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas,
                ids=doc_ids,
            )

            # Update instance reference
            if knowledge_base == "attacker":
                self.attacker_kb = collection
            else:
                self.governance_kb = collection

            self.logger.info(
                f"Successfully ingested {len(documents)} documents into {collection_name}"
            )

            return {
                "success": True,
                "knowledge_base": knowledge_base,
                "documents_added": len(documents),
                "collection_name": collection_name,
            }

        except Exception as e:
            self.logger.error(f"Error ingesting documents: {e}")
            return {"success": False, "error": str(e)}

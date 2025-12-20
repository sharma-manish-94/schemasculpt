#!/usr/bin/env python3
"""
RAG Knowledge Base Management CLI

Simple command-line tool for managing RAG knowledge bases.
This script provides commands for initializing, re-ingesting, and checking RAG status.

Usage:
    python manage_rag.py init          # Initialize knowledge bases (automatic on app startup)
    python manage_rag.py reingest      # Force re-ingestion of all documents
    python manage_rag.py status        # Check knowledge base status
    python manage_rag.py query <text>  # Test query against knowledge bases
"""

import argparse
import asyncio
import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.logging import get_logger
from app.services.rag_initializer import RAGInitializer
from app.services.rag_service import RAGService

logger = get_logger("manage_rag")


async def init_knowledge_bases(force: bool = False):
    """Initialize knowledge bases."""
    print("=" * 70)
    print("RAG Knowledge Base Initialization")
    print("=" * 70)

    try:
        initializer = RAGInitializer()
        result = await initializer.initialize_knowledge_bases(force_reingest=force)

        if result.get("status") == "success":
            print(f"\n✅ Initialization successful!")
            print(f"   Total documents ingested: {result.get('total_documents', 0)}")
            print(
                f"\n   Attacker KB: {result['attacker_kb'].get('documents_added', 0)} documents"
            )
            print(f"   Sources: {', '.join(result['attacker_kb'].get('sources', []))}")
            print(
                f"\n   Governance KB: {result['governance_kb'].get('documents_added', 0)} documents"
            )
            print(
                f"   Sources: {', '.join(result['governance_kb'].get('sources', []))}"
            )
        elif result.get("status") == "already_initialized":
            print("\n✅ Knowledge bases already initialized")
            print("   Use 'python manage_rag.py reingest' to force re-ingestion")
        else:
            print(f"\n⚠️  Initialization completed with warnings:")
            print(f"   {result}")

    except Exception as e:
        print(f"\n❌ Initialization failed: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


async def show_status():
    """Show knowledge base status."""
    print("=" * 70)
    print("RAG Knowledge Base Status")
    print("=" * 70)

    try:
        rag_service = RAGService()
        stats = await rag_service.get_knowledge_base_stats()

        if not stats.get("available"):
            print(f"\n❌ RAG service not available")
            print(f"   Error: {stats.get('error', 'Unknown')}")
            print("\nInstall dependencies with:")
            print("   pip install chromadb sentence-transformers")
            return

        print(f"\n✅ RAG service is available")
        print(f"   Vector store: {stats.get('vector_store_path', 'Unknown')}")

        print(f"\n📚 Attacker Knowledge Base:")
        attacker_kb = stats.get("attacker_kb", {})
        if attacker_kb.get("available"):
            print(f"   Status: ✅ Available")
            print(f"   Documents: {attacker_kb.get('document_count', 0)}")
            print(f"   Description: {attacker_kb.get('description', '')}")
        else:
            print(f"   Status: ❌ Not initialized")
            print(f"   Run: python manage_rag.py init")

        print(f"\n🔐 Governance Knowledge Base:")
        governance_kb = stats.get("governance_kb", {})
        if governance_kb.get("available"):
            print(f"   Status: ✅ Available")
            print(f"   Documents: {governance_kb.get('document_count', 0)}")
            print(f"   Description: {governance_kb.get('description', '')}")
        else:
            print(f"   Status: ❌ Not initialized")
            print(f"   Run: python manage_rag.py init")

        print(f"\n📊 Total documents: {stats.get('total_documents', 0)}")

    except Exception as e:
        print(f"\n❌ Failed to get status: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


async def test_query(query: str, kb_name: str = "attacker", n_results: int = 3):
    """Test RAG query."""
    print("=" * 70)
    print(f"RAG Query Test - {kb_name.title()} KB")
    print("=" * 70)
    print(f"\n🔍 Query: {query}")
    print("-" * 70)

    try:
        rag_service = RAGService()

        if kb_name == "attacker":
            results = await rag_service.query_attacker_knowledge(query, n_results)
        elif kb_name == "governance":
            results = await rag_service.query_governance_knowledge(query, n_results)
        else:
            print(f"❌ Invalid knowledge base: {kb_name}")
            print("   Valid options: attacker, governance")
            return

        if results.get("total_documents", 0) == 0:
            print("\n⚠️  No results found")
            print("   Knowledge base may not be initialized")
            print("   Run: python manage_rag.py init")
            return

        print(f"\n📚 Found {results.get('total_documents', 0)} relevant documents")
        print(
            f"   Average relevance: {sum(results.get('relevance_scores', [0])) / max(len(results.get('relevance_scores', [1])), 1):.2f}"
        )
        print("\n" + "-" * 70)

        # Show top results
        sources = results.get("sources", [])
        context = results.get("context", "")

        # Split context by separator
        context_parts = context.split("\n\n---\n\n")

        for i, (part, source) in enumerate(zip(context_parts, sources)):
            print(f"\nResult {i+1}:")
            print(f"Source: {source}")
            print(f"Relevance: {results.get('relevance_scores', [0])[i]:.2f}")
            print(f"\n{part[:500]}...")
            print("-" * 70)

    except Exception as e:
        print(f"\n❌ Query failed: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="RAG Knowledge Base Management CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Initialize knowledge bases (happens automatically on app startup)
  python manage_rag.py init

  # Force re-ingestion of all documents
  python manage_rag.py reingest

  # Check status
  python manage_rag.py status

  # Test query on attacker KB
  python manage_rag.py query "SQL injection patterns"

  # Test query on governance KB
  python manage_rag.py query "GDPR compliance requirements" --kb governance
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Init command
    init_parser = subparsers.add_parser("init", help="Initialize knowledge bases")

    # Reingest command
    reingest_parser = subparsers.add_parser(
        "reingest", help="Force re-ingestion of all documents"
    )

    # Status command
    status_parser = subparsers.add_parser("status", help="Show knowledge base status")

    # Query command
    query_parser = subparsers.add_parser("query", help="Test RAG query")
    query_parser.add_argument("text", help="Query text")
    query_parser.add_argument(
        "--kb",
        choices=["attacker", "governance"],
        default="attacker",
        help="Knowledge base to query",
    )
    query_parser.add_argument(
        "-n", "--num-results", type=int, default=3, help="Number of results to return"
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    # Execute command
    if args.command == "init":
        asyncio.run(init_knowledge_bases(force=False))
    elif args.command == "reingest":
        print("⚠️  This will re-ingest all documents, replacing existing ones.")
        confirm = input("Continue? (yes/no): ")
        if confirm.lower() in ["yes", "y"]:
            asyncio.run(init_knowledge_bases(force=True))
        else:
            print("Cancelled")
    elif args.command == "status":
        asyncio.run(show_status())
    elif args.command == "query":
        asyncio.run(test_query(args.text, args.kb, args.num_results))


if __name__ == "__main__":
    main()

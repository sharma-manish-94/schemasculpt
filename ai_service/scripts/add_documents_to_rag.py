#!/usr/bin/env python3
"""
Add Documents to RAG - Document Ingestion Utility

This script allows you to add custom documents to the RAG knowledge bases.
Supports: TXT, PDF, JSON, Markdown

Usage:
    # Add a single document
    python scripts/add_documents_to_rag.py --file ./my_doc.pdf --kb attacker

    # Add all documents from a directory
    python scripts/add_documents_to_rag.py --directory ./raw_documents --kb governance

    # Add with metadata
    python scripts/add_documents_to_rag.py --file cvss_guide.pdf --kb governance --metadata '{"source": "FIRST", "version": "3.1"}'
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional

# Add parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import chromadb
    from sentence_transformers import SentenceTransformer

    DEPS_AVAILABLE = True
except ImportError as e:
    DEPS_AVAILABLE = False
    print(f"ERROR: Required dependencies not installed: {e}")
    print("\nInstall with:")
    print("  pip install chromadb sentence-transformers pypdf")
    sys.exit(1)


class DocumentIngestionTool:
    """Tool for adding documents to RAG knowledge bases."""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.vector_store_dir = self.project_root / "vector_store"

        print("📦 Initializing embedding model...")
        self.embedding_model = SentenceTransformer(
            "sentence-transformers/all-MiniLM-L6-v2"
        )
        print(f"✅ Loaded on {self.embedding_model.device}")

        print("📦 Connecting to ChromaDB...")
        self.client = chromadb.PersistentClient(path=str(self.vector_store_dir))
        print(f"✅ Connected to {self.vector_store_dir}")

        # Verify collections exist
        try:
            self.attacker_kb = self.client.get_collection("attacker_knowledge")
            print(f"✅ Attacker KB: {self.attacker_kb.count()} documents")
        except:
            print("⚠️  Attacker KB not found. Run init_knowledge_base.py first.")
            self.attacker_kb = None

        try:
            self.governance_kb = self.client.get_collection("governance_knowledge")
            print(f"✅ Governance KB: {self.governance_kb.count()} documents")
        except:
            print("⚠️  Governance KB not found. Run init_knowledge_base.py first.")
            self.governance_kb = None

    def create_embedding_function(self):
        """Create ChromaDB-compatible embedding function."""

        class EmbeddingFunction:
            def __init__(self, model):
                self.model = model

            def __call__(self, input):
                return self.model.encode(input).tolist()

        return EmbeddingFunction(self.embedding_model)

    def read_text_file(self, file_path: Path) -> str:
        """Read plain text or markdown file."""
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()

    def read_pdf_file(self, file_path: Path) -> str:
        """Read PDF file and extract text."""
        try:
            from pypdf import PdfReader
        except ImportError:
            print("❌ pypdf not installed. Install with: pip install pypdf")
            return None

        try:
            reader = PdfReader(str(file_path))
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n\n"
            return text.strip()
        except Exception as e:
            print(f"❌ Error reading PDF: {e}")
            return None

    def read_json_file(self, file_path: Path) -> List[Dict]:
        """Read JSON file with structured knowledge."""
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # If it's a knowledge base format, extract documents
        documents = []

        if isinstance(data, list):
            # Array of documents
            for item in data:
                if isinstance(item, dict) and "content" in item:
                    documents.append(item)
                elif isinstance(item, str):
                    documents.append({"content": item})
        elif isinstance(data, dict):
            # Check for our knowledge base format
            if "owasp_vulnerabilities" in data:
                for vuln in data["owasp_vulnerabilities"]:
                    doc_text = self.format_owasp_vuln(vuln)
                    documents.append(
                        {
                            "content": doc_text,
                            "metadata": {
                                "type": "owasp_vulnerability",
                                "category": vuln.get("category"),
                                "risk_level": vuln.get("risk_level"),
                            },
                        }
                    )

            if "common_vulnerabilities" in data:
                for vuln in data["common_vulnerabilities"]:
                    doc_text = self.format_common_vuln(vuln)
                    documents.append(
                        {
                            "content": doc_text,
                            "metadata": {
                                "type": "common_vulnerability",
                                "name": vuln.get("name"),
                                "category": vuln.get("category"),
                            },
                        }
                    )

            if "attack_patterns" in data:
                for pattern in data["attack_patterns"]:
                    doc_text = self.format_attack_pattern(pattern)
                    documents.append(
                        {
                            "content": doc_text,
                            "metadata": {
                                "type": "attack_pattern",
                                "name": pattern.get("name"),
                                "pattern_type": pattern.get("type"),
                            },
                        }
                    )

        return documents

    def format_owasp_vuln(self, vuln: Dict) -> str:
        """Format OWASP vulnerability as text."""
        text = f"""
OWASP {vuln.get('category', 'Unknown')}
Risk Level: {vuln.get('risk_level', 'Unknown')}

Description: {vuln.get('description', '')}

Attack Scenarios:
{chr(10).join(f"- {scenario}" for scenario in vuln.get('attack_scenarios', []))}

Remediation:
{chr(10).join(f"- {fix}" for fix in vuln.get('remediation', []))}

Technical Indicators:
{chr(10).join(f"- {indicator}" for indicator in vuln.get('technical_indicators', []))}
        """.strip()
        return text

    def format_common_vuln(self, vuln: Dict) -> str:
        """Format common vulnerability as text."""
        text = f"""
{vuln.get('name', 'Unknown Vulnerability')}
Category: {vuln.get('category', 'General')}

Description: {vuln.get('description', '')}

Indicators:
{chr(10).join(f"- {indicator}" for indicator in vuln.get('indicators', []))}

Exploitation:
{chr(10).join(f"- {exploit}" for exploit in vuln.get('exploitation', []))}

Mitigation:
{chr(10).join(f"- {mit}" for mit in vuln.get('mitigation', []))}
        """.strip()
        return text

    def format_attack_pattern(self, pattern: Dict) -> str:
        """Format attack pattern as text."""
        text = f"""
Attack Pattern: {pattern.get('name', 'Unknown')}
Type: {pattern.get('type', 'General')}

Description: {pattern.get('description', '')}

Prerequisites:
{chr(10).join(f"- {req}" for req in pattern.get('prerequisites', []))}

Steps:
{chr(10).join(f"{i+1}. {step}" for i, step in enumerate(pattern.get('steps', [])))}

Indicators:
{chr(10).join(f"- {ind}" for ind in pattern.get('indicators', []))}

Defenses:
{chr(10).join(f"- {defense}" for defense in pattern.get('defenses', []))}
        """.strip()
        return text

    def chunk_text(
        self, text: str, chunk_size: int = 500, overlap: int = 50
    ) -> List[str]:
        """Split text into overlapping chunks."""
        words = text.split()
        chunks = []

        for i in range(0, len(words), chunk_size - overlap):
            chunk = " ".join(words[i : i + chunk_size])
            if len(chunk.strip()) > 50:  # Skip very small chunks
                chunks.append(chunk.strip())

        return chunks

    def add_document(
        self,
        file_path: Path,
        kb_name: str,
        metadata: Optional[Dict] = None,
        chunk_size: int = 500,
    ) -> int:
        """
        Add a document to the knowledge base.

        Args:
            file_path: Path to document
            kb_name: 'attacker' or 'governance'
            metadata: Optional metadata dict
            chunk_size: Size of text chunks

        Returns:
            Number of chunks added
        """
        # Select collection
        if kb_name == "attacker":
            collection = self.attacker_kb
        elif kb_name == "governance":
            collection = self.governance_kb
        else:
            raise ValueError(
                f"Invalid KB name: {kb_name}. Use 'attacker' or 'governance'"
            )

        if collection is None:
            raise ValueError(
                f"{kb_name} KB not found. Run init_knowledge_base.py first."
            )

        # Read file based on extension
        suffix = file_path.suffix.lower()

        if suffix in [".txt", ".md"]:
            print(f"📄 Reading text file: {file_path.name}")
            content = self.read_text_file(file_path)
            if not content:
                print(f"⚠️  Empty file: {file_path}")
                return 0

            # Chunk the text
            chunks = self.chunk_text(content, chunk_size)
            documents_to_add = [
                {
                    "content": chunk,
                    "metadata": {
                        **(metadata or {}),
                        "source_file": file_path.name,
                        "file_type": suffix,
                        "chunk_index": i,
                    },
                }
                for i, chunk in enumerate(chunks)
            ]

        elif suffix == ".pdf":
            print(f"📕 Reading PDF file: {file_path.name}")
            content = self.read_pdf_file(file_path)
            if not content:
                return 0

            # Chunk the PDF text
            chunks = self.chunk_text(content, chunk_size)
            documents_to_add = [
                {
                    "content": chunk,
                    "metadata": {
                        **(metadata or {}),
                        "source_file": file_path.name,
                        "file_type": "pdf",
                        "chunk_index": i,
                    },
                }
                for i, chunk in enumerate(chunks)
            ]

        elif suffix == ".json":
            print(f"📋 Reading JSON file: {file_path.name}")
            documents_to_add = self.read_json_file(file_path)
            if not documents_to_add:
                print(f"⚠️  No documents extracted from JSON")
                return 0

            # Add source file to metadata
            for doc in documents_to_add:
                if "metadata" not in doc:
                    doc["metadata"] = {}
                doc["metadata"]["source_file"] = file_path.name
                if metadata:
                    doc["metadata"].update(metadata)

        else:
            print(f"❌ Unsupported file type: {suffix}")
            return 0

        # Add documents to collection
        print(f"  Adding {len(documents_to_add)} chunks...")

        documents = []
        metadatas = []
        ids = []

        for doc in documents_to_add:
            content = doc.get("content", "")
            if len(content.strip()) < 20:  # Skip very short content
                continue

            doc_metadata = doc.get("metadata", {})

            # Generate unique ID
            unique_str = f"{file_path.name}_{content[:100]}"
            doc_id = hashlib.md5(unique_str.encode()).hexdigest()

            documents.append(content)
            metadatas.append(doc_metadata)
            ids.append(doc_id)

        # Add in batches
        batch_size = 100
        for i in range(0, len(documents), batch_size):
            batch_docs = documents[i : i + batch_size]
            batch_meta = metadatas[i : i + batch_size]
            batch_ids = ids[i : i + batch_size]

            collection.add(documents=batch_docs, metadatas=batch_meta, ids=batch_ids)

        print(f"✅ Added {len(documents)} chunks to {kb_name}_knowledge")
        return len(documents)

    def add_directory(
        self,
        directory: Path,
        kb_name: str,
        metadata: Optional[Dict] = None,
        recursive: bool = False,
    ) -> int:
        """Add all supported documents from a directory."""
        total_chunks = 0

        pattern = "**/*" if recursive else "*"
        supported_extensions = [".txt", ".md", ".pdf", ".json"]

        for file_path in directory.glob(pattern):
            if file_path.is_file() and file_path.suffix.lower() in supported_extensions:
                try:
                    chunks = self.add_document(file_path, kb_name, metadata)
                    total_chunks += chunks
                except Exception as e:
                    print(f"❌ Error processing {file_path.name}: {e}")

        return total_chunks

    def query_knowledge_base(self, query: str, kb_name: str, n_results: int = 3):
        """Query the knowledge base to test retrieval."""
        if kb_name == "attacker":
            collection = self.attacker_kb
        elif kb_name == "governance":
            collection = self.governance_kb
        else:
            raise ValueError(f"Invalid KB name: {kb_name}")

        if collection is None:
            print(f"❌ {kb_name} KB not available")
            return

        results = collection.query(query_texts=[query], n_results=n_results)

        print(f"\n🔍 Query: {query}")
        print(f"📚 Knowledge Base: {kb_name}_knowledge")
        print("-" * 70)

        for i, (doc, metadata) in enumerate(
            zip(results["documents"][0], results["metadatas"][0])
        ):
            print(f"\nResult {i+1}:")
            print(f"Source: {metadata.get('source_file', 'Unknown')}")
            print(f"Type: {metadata.get('type', metadata.get('file_type', 'Unknown'))}")
            print(f"Content: {doc[:300]}...")
            print("-" * 70)


def main():
    parser = argparse.ArgumentParser(
        description="Add documents to RAG knowledge bases",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Add single PDF to attacker knowledge base
  python add_documents_to_rag.py --file mitre_attack.pdf --kb attacker

  # Add all files from directory to governance KB
  python add_documents_to_rag.py --directory ./compliance_docs --kb governance

  # Add with custom metadata
  python add_documents_to_rag.py --file cvss.pdf --kb governance --metadata '{"version": "3.1", "source": "FIRST"}'

  # Test query
  python add_documents_to_rag.py --query "SQL injection attack patterns" --kb attacker
        """,
    )

    parser.add_argument("--file", type=Path, help="Single file to add")
    parser.add_argument("--directory", type=Path, help="Directory of files to add")
    parser.add_argument(
        "--kb", choices=["attacker", "governance"], help="Knowledge base to add to"
    )
    parser.add_argument(
        "--metadata", type=str, help="JSON string of metadata to attach"
    )
    parser.add_argument(
        "--chunk-size", type=int, default=500, help="Chunk size for text splitting"
    )
    parser.add_argument(
        "--recursive", action="store_true", help="Recursively process directory"
    )
    parser.add_argument("--query", type=str, help="Test query against knowledge base")

    args = parser.parse_args()

    if not DEPS_AVAILABLE:
        sys.exit(1)

    try:
        tool = DocumentIngestionTool()

        # Parse metadata if provided
        metadata = None
        if args.metadata:
            try:
                metadata = json.loads(args.metadata)
            except json.JSONDecodeError:
                print(f"❌ Invalid JSON metadata: {args.metadata}")
                sys.exit(1)

        # Test query mode
        if args.query:
            if not args.kb:
                print("❌ --kb required for query")
                sys.exit(1)
            tool.query_knowledge_base(args.query, args.kb)
            return

        # Add file
        if args.file:
            if not args.kb:
                print("❌ --kb required when adding files")
                sys.exit(1)

            if not args.file.exists():
                print(f"❌ File not found: {args.file}")
                sys.exit(1)

            tool.add_document(args.file, args.kb, metadata, args.chunk_size)

        # Add directory
        elif args.directory:
            if not args.kb:
                print("❌ --kb required when adding directory")
                sys.exit(1)

            if not args.directory.exists():
                print(f"❌ Directory not found: {args.directory}")
                sys.exit(1)

            total = tool.add_directory(
                args.directory, args.kb, metadata, args.recursive
            )
            print(f"\n🎉 Total chunks added: {total}")

        else:
            parser.print_help()

    except KeyboardInterrupt:
        print("\n\n⚠️  Cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

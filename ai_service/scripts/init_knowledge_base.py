#!/usr/bin/env python3
"""
Knowledge Base Initialization Script

This script populates the ChromaDB vector store with security knowledge for RAG.
Run this once after installing dependencies to enable the AI explanation system.

Usage:
    python scripts/init_knowledge_base.py
"""

import sys
from pathlib import Path
import json
import hashlib

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
    print("  pip install chromadb sentence-transformers pypdf beautifulsoup4")
    sys.exit(1)


class KnowledgeBaseInitializer:
    """Initialize the knowledge base with security documents."""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.vector_store_dir = self.project_root / "vector_store"
        self.knowledge_base_dir = self.project_root / "knowledge_base"

        print(f"Project root: {self.project_root}")
        print(f"Vector store: {self.vector_store_dir}")
        print(f"Knowledge base: {self.knowledge_base_dir}")

        # Initialize embedding model
        print("\n📦 Initializing embedding model...")
        self.embedding_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        print(f"✅ Embedding model loaded on {self.embedding_model.device}")

        # Initialize ChromaDB client
        print("\n📦 Initializing ChromaDB...")
        self.vector_store_dir.mkdir(parents=True, exist_ok=True)
        self.client = chromadb.PersistentClient(path=str(self.vector_store_dir))
        print(f"✅ ChromaDB initialized at {self.vector_store_dir}")

    def create_embedding_function(self):
        """Create ChromaDB-compatible embedding function."""
        class EmbeddingFunction:
            def __init__(self, model):
                self.model = model

            def __call__(self, input):
                return self.model.encode(input).tolist()

        return EmbeddingFunction(self.embedding_model)

    def initialize_attacker_kb(self):
        """Initialize Attacker Knowledge Base from security_knowledge.json."""
        print("\n🔍 Initializing Attacker Knowledge Base...")

        knowledge_file = self.knowledge_base_dir / "security_knowledge.json"
        if not knowledge_file.exists():
            print(f"⚠️  {knowledge_file} not found. Skipping...")
            return

        # Load knowledge
        with open(knowledge_file, "r") as f:
            knowledge = json.load(f)

        # Delete existing collection if it exists
        try:
            self.client.delete_collection(name="attacker_knowledge")
            print("  Deleted existing attacker_knowledge collection")
        except Exception:
            pass

        # Create new collection
        collection = self.client.create_collection(
            name="attacker_knowledge",
            embedding_function=self.create_embedding_function(),
            metadata={"description": "Offensive security knowledge for threat modeling"}
        )

        # Prepare documents
        documents = []
        metadatas = []
        ids = []

        # Process OWASP vulnerabilities
        if "owasp_vulnerabilities" in knowledge:
            for vuln in knowledge["owasp_vulnerabilities"]:
                doc_text = f"""
OWASP {vuln['category']}
Risk Level: {vuln.get('risk_level', 'Unknown')}

Description: {vuln['description']}

Attack Scenarios:
{chr(10).join(f"- {scenario}" for scenario in vuln.get('attack_scenarios', []))}

Remediation:
{chr(10).join(f"- {fix}" for fix in vuln.get('remediation', []))}
                """.strip()

                doc_id = hashlib.md5(f"owasp_{vuln['category']}".encode()).hexdigest()
                documents.append(doc_text)
                metadatas.append({
                    "type": "owasp_vulnerability",
                    "category": vuln["category"],
                    "risk_level": vuln.get("risk_level", "Unknown")
                })
                ids.append(doc_id)

        # Process common vulnerabilities
        if "common_vulnerabilities" in knowledge:
            for vuln in knowledge["common_vulnerabilities"]:
                doc_text = f"""
{vuln['name']}
Category: {vuln.get('category', 'General')}

Description: {vuln['description']}

Indicators:
{chr(10).join(f"- {indicator}" for indicator in vuln.get('indicators', []))}

Exploitation:
{chr(10).join(f"- {exploit}" for exploit in vuln.get('exploitation', []))}

Mitigation:
{chr(10).join(f"- {mit}" for mit in vuln.get('mitigation', []))}
                """.strip()

                doc_id = hashlib.md5(f"vuln_{vuln['name']}".encode()).hexdigest()
                documents.append(doc_text)
                metadatas.append({
                    "type": "common_vulnerability",
                    "name": vuln["name"],
                    "category": vuln.get("category", "General")
                })
                ids.append(doc_id)

        # Process attack patterns
        if "attack_patterns" in knowledge:
            for pattern in knowledge["attack_patterns"]:
                doc_text = f"""
Attack Pattern: {pattern['name']}
Type: {pattern.get('type', 'Unknown')}

Description: {pattern['description']}

Prerequisites:
{chr(10).join(f"- {req}" for req in pattern.get('prerequisites', []))}

Steps:
{chr(10).join(f"{i+1}. {step}" for i, step in enumerate(pattern.get('steps', [])))}

Indicators:
{chr(10).join(f"- {ind}" for ind in pattern.get('indicators', []))}

Defenses:
{chr(10).join(f"- {defense}" for defense in pattern.get('defenses', []))}
                """.strip()

                doc_id = hashlib.md5(f"pattern_{pattern['name']}".encode()).hexdigest()
                documents.append(doc_text)
                metadatas.append({
                    "type": "attack_pattern",
                    "name": pattern["name"],
                    "pattern_type": pattern.get("type", "Unknown")
                })
                ids.append(doc_id)

        # Add to collection
        if documents:
            print(f"  Adding {len(documents)} documents to attacker_knowledge...")
            collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            print(f"✅ Attacker KB initialized with {len(documents)} documents")
        else:
            print("⚠️  No documents found in security_knowledge.json")

    def initialize_governance_kb(self):
        """Initialize Governance Knowledge Base from OWASP PDF."""
        print("\n🔐 Initializing Governance Knowledge Base...")

        pdf_file = self.knowledge_base_dir / "OWASP_Application_Security_Verification_Standard_5.0.0_en.pdf"

        if not pdf_file.exists():
            print(f"⚠️  {pdf_file} not found. Creating empty governance KB...")
            # Create empty collection for future use
            try:
                self.client.delete_collection(name="governance_knowledge")
            except Exception:
                pass

            collection = self.client.create_collection(
                name="governance_knowledge",
                embedding_function=self.create_embedding_function(),
                metadata={"description": "Compliance and governance knowledge"}
            )

            # Add some basic governance knowledge
            documents = [
                """
GDPR Compliance for APIs
The General Data Protection Regulation (GDPR) requires:
- Explicit consent for data collection
- Right to data portability
- Right to erasure (right to be forgotten)
- Data minimization principles
- Privacy by design
- Breach notification within 72 hours
Violations can result in fines up to €20 million or 4% of global revenue.
                """.strip(),
                """
PCI-DSS Compliance for APIs
Payment Card Industry Data Security Standard requires:
- Strong access control measures
- Encryption of cardholder data in transit and at rest
- Regular security testing
- Network segmentation
- Multi-factor authentication for system access
APIs handling payment card data must comply with all 12 requirements.
                """.strip(),
                """
API Security Best Practices
- Implement OAuth 2.0 or similar authentication
- Use HTTPS/TLS for all communications
- Implement rate limiting to prevent abuse
- Validate all input data
- Use API keys with proper rotation policies
- Implement comprehensive logging and monitoring
- Follow principle of least privilege
                """.strip()
            ]

            metadatas = [
                {"type": "compliance", "standard": "GDPR", "domain": "Privacy"},
                {"type": "compliance", "standard": "PCI-DSS", "domain": "Payment Security"},
                {"type": "best_practice", "category": "API Security", "domain": "General"}
            ]

            ids = [
                hashlib.md5("gdpr_basics".encode()).hexdigest(),
                hashlib.md5("pci_dss_basics".encode()).hexdigest(),
                hashlib.md5("api_security_basics".encode()).hexdigest()
            ]

            collection.add(documents=documents, metadatas=metadatas, ids=ids)
            print(f"✅ Governance KB initialized with {len(documents)} basic documents")
            print("  Note: To add OWASP ASVS content, place the PDF in knowledge_base/ and install pypdf")
            return

        # Try to parse PDF
        try:
            from pypdf import PdfReader
            print(f"  Parsing {pdf_file.name}...")

            reader = PdfReader(str(pdf_file))
            print(f"  Found {len(reader.pages)} pages")

            # Delete existing collection
            try:
                self.client.delete_collection(name="governance_knowledge")
                print("  Deleted existing governance_knowledge collection")
            except Exception:
                pass

            # Create new collection
            collection = self.client.create_collection(
                name="governance_knowledge",
                embedding_function=self.create_embedding_function(),
                metadata={"description": "OWASP ASVS and governance knowledge"}
            )

            # Extract text from pages in chunks
            documents = []
            metadatas = []
            ids = []

            for page_num, page in enumerate(reader.pages):
                text = page.extract_text()
                if len(text.strip()) < 50:  # Skip empty/short pages
                    continue

                # Split into paragraphs (chunks of ~500 chars)
                paragraphs = []
                current_chunk = ""
                for line in text.split("\n"):
                    if len(current_chunk) + len(line) > 500 and current_chunk:
                        paragraphs.append(current_chunk.strip())
                        current_chunk = line
                    else:
                        current_chunk += " " + line

                if current_chunk.strip():
                    paragraphs.append(current_chunk.strip())

                for idx, para in enumerate(paragraphs):
                    doc_id = hashlib.md5(f"asvs_p{page_num}_{idx}".encode()).hexdigest()
                    documents.append(para)
                    metadatas.append({
                        "type": "owasp_asvs",
                        "source": "OWASP ASVS 5.0.0",
                        "page": page_num + 1
                    })
                    ids.append(doc_id)

            # Add to collection in batches (ChromaDB has limits)
            batch_size = 100
            for i in range(0, len(documents), batch_size):
                batch_docs = documents[i:i+batch_size]
                batch_meta = metadatas[i:i+batch_size]
                batch_ids = ids[i:i+batch_size]

                collection.add(
                    documents=batch_docs,
                    metadatas=batch_meta,
                    ids=batch_ids
                )
                print(f"  Added batch {i//batch_size + 1}/{(len(documents)-1)//batch_size + 1}")

            print(f"✅ Governance KB initialized with {len(documents)} chunks from OWASP ASVS")

        except ImportError:
            print("⚠️  pypdf not installed. Install with: pip install pypdf")
            print("  Creating governance KB with basic content only...")
            self.initialize_governance_kb()  # Fallback to basic content

        except Exception as e:
            print(f"❌ Error parsing PDF: {e}")
            print("  Creating governance KB with basic content only...")
            # Fallback to basic content
            self.initialize_governance_kb()

    def verify_installation(self):
        """Verify the knowledge bases are properly installed."""
        print("\n🔍 Verifying installation...")

        try:
            attacker_kb = self.client.get_collection(name="attacker_knowledge")
            attacker_count = attacker_kb.count()
            print(f"✅ Attacker KB: {attacker_count} documents")
        except Exception as e:
            print(f"❌ Attacker KB verification failed: {e}")

        try:
            governance_kb = self.client.get_collection(name="governance_knowledge")
            governance_count = governance_kb.count()
            print(f"✅ Governance KB: {governance_count} documents")
        except Exception as e:
            print(f"❌ Governance KB verification failed: {e}")

        print("\n🎉 Knowledge base initialization complete!")
        print("\nYou can now use the AI explanation system and RAG-enhanced security analysis.")

    def run(self):
        """Run the full initialization process."""
        print("=" * 70)
        print("SchemaSculpt Knowledge Base Initialization")
        print("=" * 70)

        self.initialize_attacker_kb()
        self.initialize_governance_kb()
        self.verify_installation()


if __name__ == "__main__":
    if not DEPS_AVAILABLE:
        sys.exit(1)

    try:
        initializer = KnowledgeBaseInitializer()
        initializer.run()
    except KeyboardInterrupt:
        print("\n\n⚠️  Initialization cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Initialization failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

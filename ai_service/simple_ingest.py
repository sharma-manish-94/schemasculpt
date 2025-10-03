#!/usr/bin/env python3
"""
Simple knowledge base ingestion without heavy dependencies.
Creates a basic vector store for the security analysis.
"""

import os
import json
from pathlib import Path

# Simplified knowledge base for demonstration
SECURITY_KNOWLEDGE = [
    {
        "topic": "Authentication",
        "content": "OpenAPI specifications should include proper authentication schemes. Common issues: missing auth, weak auth methods, exposed credentials in examples.",
        "category": "security"
    },
    {
        "topic": "Authorization",
        "content": "APIs must implement proper authorization controls. Common issues: missing role-based access, insufficient endpoint protection, privilege escalation risks.",
        "category": "security"
    },
    {
        "topic": "Input Validation",
        "content": "All API inputs must be validated. Common issues: missing validation schemas, inadequate type checking, injection vulnerabilities.",
        "category": "security"
    },
    {
        "topic": "Data Exposure",
        "content": "APIs should not expose sensitive data unnecessarily. Common issues: returning sensitive fields, lack of field filtering, verbose error messages.",
        "category": "security"
    },
    {
        "topic": "HTTPS/TLS",
        "content": "APIs must use HTTPS for all communications. Common issues: HTTP servers defined, missing security requirements, weak TLS configuration.",
        "category": "security"
    }
]

def create_simple_knowledge_base():
    """Create a simple JSON-based knowledge base."""
    kb_dir = Path("knowledge_base")
    kb_dir.mkdir(exist_ok=True)

    # Write security knowledge as JSON
    kb_file = kb_dir / "security_knowledge.json"
    with open(kb_file, "w") as f:
        json.dump(SECURITY_KNOWLEDGE, f, indent=2)

    print(f"Created simple knowledge base at {kb_file}")
    print(f"Added {len(SECURITY_KNOWLEDGE)} security knowledge entries")

if __name__ == "__main__":
    create_simple_knowledge_base()
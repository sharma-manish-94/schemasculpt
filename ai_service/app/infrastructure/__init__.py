"""
Infrastructure Layer.

This layer contains concrete implementations of the domain interfaces.
Each sub-module provides implementations for specific infrastructure concerns:

- llm/: LLM provider implementations (Ollama, HuggingFace, OpenAI)
- cache/: Cache implementations (Redis, in-memory)
- rag/: RAG/vector store implementations (ChromaDB)
- validation/: Spec validation implementations (Prance)

The infrastructure layer depends on external libraries and services.
Domain and application layers depend on interfaces, not implementations.
"""

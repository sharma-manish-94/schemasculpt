import json
from typing import Any, Dict, List, Optional

from app.core.logging import get_logger
from app.schemas.ai_schemas import LLMParameters
from app.services.agents.base_agent import BaseAgent
from app.services.llm_service import LLMService
from app.services.repomind_client import RepoMindClient

logger = get_logger("discovery_agent")


class DiscoveryAgent(BaseAgent):
    """
    Intelligent Agent that uses LLM reasoning to discover code handlers.
    Uses high-precision LSP tools for compiler-grade accuracy.
    """

    def __init__(
        self, name: str, description: str, llm_service: Optional[LLMService] = None
    ):
        super().__init__(name, description)
        self.llm_service = llm_service or LLMService()

    def _define_capabilities(self) -> List[str]:
        return [
            "correlate_endpoint",
            "hierarchical_search",
            "intelligent_discovery",
            "lsp_precision",
        ]

    async def execute(
        self, task: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        input_data = task.get("input_data", {})
        return await self.correlate(
            repo_name=input_data.get("repo_name"),
            path=input_data.get("path"),
            method=input_data.get("method"),
            operation_id=input_data.get("operation_id"),
        )

    async def correlate(
        self, repo_name: str, path: str, method: str, operation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        logger.info(
            f"DiscoveryAgent: Starting high-precision discovery for {method} {path}"
        )

        system_prompt = """
        You are Odysseus, the code-aware discovery engine of SchemaSculpt.
        Your goal is to find the EXACT route handler (Controller/Router) for an API endpoint.

        CONTEXT:
        - Prioritize classes named '*Controller', '*Router', or files in 'api/', 'routers/', 'controllers/'.
        - You MUST return a 'final_answer' once you have found a matching candidate.

        AVAILABLE TOOLS:
        1. correlate_spec_to_code(repo_name, openapi_path, http_method):
           Finds handlers by structural path match.
        2. resolve_symbol(symbol_name, repo_filter, prefer_lsp=True):
           ULTRA PRECISE. Use this to get exact code, file, and lines for a handler.
        3. semantic_grep(query, repo_filter):
           Finds code by searching for concepts like "GET handler for health".

        REASONING PROCESS:
        1. Use 'correlate_spec_to_code' or 'semantic_grep' to find candidates.
        2. If you see a candidate that perfectly matches the path and method (e.g. 'simple_health_check' for '/health'), USE IT.
        3. Before providing 'final_answer', you can use 'resolve_symbol' to get the full snippet.
        4. YOU MUST PROVIDE A 'final_answer' ACTION TO FINISH.

        RESPONSE FORMAT (Strict JSON):
        {
            "thought": "your reasoning",
            "action": "tool_name" | "final_answer",
            "action_input": { ... },
            "best_match": {
                "handler": "method_name",
                "qualified_name": "Full.Class.Name or module.function",
                "file": "path/to/controller.py",
                "start_line": 10,
                "end_line": 30,
                "language": "python" | "java",
                "code_snippet": "...",
                "confidence": 0.95
            }
        }
        """

        # Provide initial context to the LLM
        user_history = f"Find the handler for {method} {path} (Operation ID: {operation_id or 'N/A'}) in repository '{repo_name}'."

        async with RepoMindClient() as client:
            for turn in range(4):  # Increased to 4 turns
                logger.info(f"DiscoveryAgent: Turn {turn + 1}")

                llm_params = LLMParameters(model="mistral", temperature=0.1)
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_history},
                ]

                try:
                    logger.info(
                        f"DiscoveryAgent: Calling LLM with history length: {len(user_history)}"
                    )
                    response_text = await self.llm_service._call_llm_with_retry(
                        messages, llm_params
                    )
                    logger.info(f"DiscoveryAgent: Raw LLM Response: {response_text}")

                    decision = json.loads(response_text)
                    logger.info(f"DiscoveryAgent Thought: {decision.get('thought')}")

                    action = decision.get("action")
                    if action == "final_answer":
                        match = decision.get("best_match", {})
                        if match.get("qualified_name") and match.get("file"):
                            logger.info(
                                f"Odysseus found match: {match.get('qualified_name')}"
                            )
                            return {
                                "matched": True,
                                "best_match": match,
                                "candidates_found": 1,
                            }
                        user_history += "\nObservation: final_answer missing fields. Provide qualified_name and file."
                        continue

                    # Execute chosen tool
                    logger.info(f"Action: Calling {action}")
                    obs = await self._call_tool(
                        client, action, decision.get("action_input", {})
                    )

                    # Feed observation back to LLM
                    user_history += f"\nAction: {action}\nObservation: {json.dumps(obs)[:2000]}"  # Truncate large results

                except Exception as e:
                    logger.error(f"DiscoveryAgent loop failed: {e}")
                    break

            # Ultimate Fallback
            logger.info("DiscoveryAgent: ReAct loop exhausted. Falling back.")
            final_correlation = await client.correlate_spec_to_code(
                repo_name, path, method
            )
            if not final_correlation or final_correlation.get("matched") is None:
                return {"matched": False, "best_match": None, "candidates_found": 0}
            return final_correlation

    async def _call_tool(
        self, client: RepoMindClient, name: str, args: Dict[str, Any]
    ) -> Any:
        if name == "correlate_spec_to_code":
            return await client.correlate_spec_to_code(
                args.get("repo_name"), args.get("openapi_path"), args.get("http_method")
            )
        elif name == "resolve_symbol":
            return await client.call_tool(
                "resolve_symbol",
                {
                    "symbol_name": args.get("symbol_name"),
                    "repo_filter": args.get("repo_filter"),
                    "prefer_lsp": True,
                    "repo_path": "",
                },
            )
        elif name == "semantic_grep":
            return await client.semantic_grep(
                args.get("query"), repo_filter=args.get("repo_filter")
            )
        elif name == "get_context":
            return await client.get_context(
                args.get("symbol_name"), repo_filter=args.get("repo_filter")
            )
        return {"error": f"Unknown tool: {name}"}

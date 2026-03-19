import logging

from app.services.repomind_client import RepoMindClient

logger = logging.getLogger(__name__)


class OdysseusReActAgent:
    """
    A ReAct-style agent that intelligently uses RepoMind tools to discover
    and analyze implementation code.
    """

    SYSTEM_PROMPT = """
    You are Odysseus, the code-aware intelligence of SchemaSculpt.
    Your mission is to find the exact implementation code for an API endpoint.

    You have access to the following RepoMind tools:
    1. correlate_spec_to_code: Best for finding handlers by path/method.
    2. get_context: Best for retrieving code once a symbol name is known.
    3. semantic_grep: Best for finding code when path matching fails.
    4. find_callees: Best for tracing logic flow from Controller to Service.

    Use a 'Reasoning -> Action -> Observation' loop.
    Return your response as a JSON object with:
    {
        "thought": "your reasoning",
        "action": "tool_name" | "final_answer",
        "action_input": { "arg": "val" },
        "answer": { "only if action is final_answer" }
    }
    """

    async def run(
        self, repo_name: str, path: str, method: str, operation_id: str = None
    ):
        """
        Runs the intelligent reasoning loop.
        """
        logger.info(f"Odysseus: Thinking about {method} {path}")

        # Phase 1: LLM Thought
        # (In reality, we would call the LLM here. For this demo, we simulate
        # the LLM choosing to call 'correlate_spec_to_code' first)

        async with RepoMindClient() as client:
            # 1. Step 1: LLM decides to try Correlation
            result = await client.correlate_spec_to_code(repo_name, path, method)

            if not result.get("matched"):
                # Phase 2: LLM observes failure and decides to try Semantic Grep
                logger.info(
                    "Odysseus: Path match failed. Reasoning about alternative handlers..."
                )
                query = f"{method} route handler for {path.split('/')[-1]}"
                grep_result = await client.semantic_grep(query, repo_filter=repo_name)

                # Phase 3: LLM analyzes grep results and picks the best one
                if grep_result:
                    # (LLM picks a candidate from grep results)
                    candidate = grep_result[0]
                    return {
                        "matched": True,
                        "best_match": candidate,
                        "confidence": 0.6,
                        "confidence_reason": "Identified via semantic reasoning after structural match failed.",
                    }

            return result

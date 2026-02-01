import logging
from typing import Any, Dict, List

from .base_agent import LLMAgent

logger = logging.getLogger(__name__)


class RemediationAgent(LLMAgent):
    """
    An agent specialized in fixing vulnerable code snippets.
    """

    def __init__(self, llm_service):
        super().__init__(
            name="RemediationAgent",
            description="Generates code fixes for identified security vulnerabilities.",
            llm_service=llm_service,
        )

    def _build_prompt(
        self, vulnerable_code: str, language: str, vulnerability_type: str
    ) -> str:
        """Constructs the prompt for the LLM to generate a code fix."""

        return f"""
You are an expert security developer and a master of secure coding practices.
Your task is to fix a security vulnerability in a given code snippet.

**Vulnerability Type:** {vulnerability_type}
**Programming Language:** {language}

**Vulnerable Code:**
```{language}
{vulnerable_code}
```

**Instructions:**
1.  Analyze the provided code and the vulnerability type.
2.  Rewrite the entire code snippet with the vulnerability fixed.
3.  Ensure the corrected code is secure, correct, and maintains the original functionality.
4.  Add comments only where necessary to explain the security fix.
5.  Your response MUST contain ONLY the complete, fixed code block, including the necessary imports if they are missing.
6.  Do NOT include any explanations, introductions, or markdown formatting like ``` before or after the code. Just output the raw, fixed code.
"""

    async def execute(
        self, task: Dict[str, Any], context: Any = None
    ) -> Dict[str, Any]:
        """
        Takes a vulnerable piece of code and returns a suggested fix.
        """
        vulnerable_code = task.get("vulnerable_code")
        language = task.get("language")
        vulnerability_type = task.get("vulnerability_type")

        if not all([vulnerable_code, language, vulnerability_type]):
            return {
                "success": False,
                "error": "Missing required parameters for remediation.",
            }

        logger.info(
            f"[{self.name}] Generating fix for a {vulnerability_type} in {language}."
        )

        prompt = self._build_prompt(vulnerable_code, language, vulnerability_type)

        try:
            response = await self.llm_service.generate(
                model="mistral:7b-instruct",  # Or a more code-specific model
                prompt=prompt,
                temperature=0.2,  # Low temperature for more deterministic, correct code
                max_tokens=2048,
            )

            fixed_code = response.get("response", "").strip()

            # Clean up potential markdown code block fences
            if fixed_code.startswith("```"):
                lines = fixed_code.split("\n")
                fixed_code = "\n".join(
                    lines[1:-1] if lines[-1].strip() == "```" else lines[1:]
                )

            if not fixed_code:
                return {"success": False, "error": "AI failed to generate a fix."}

            return {"success": True, "suggested_fix": fixed_code}

        except Exception as e:
            logger.error(
                f"[{self.name}] Error during code remediation: {e}", exc_info=True
            )
            return {"success": False, "error": str(e)}

    def can_handle_task(self, task_type: str) -> bool:
        return task_type == "suggest_fix"

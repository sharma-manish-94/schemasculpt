# Attack Path Simulation Troubleshooting Guide

## Problem Summary

The Attack Path Simulation feature was not finding attack chains even though vulnerabilities were being detected.

## Root Cause Analysis

### Issue #1: Missing `generate()` Method ✅ FIXED
**Problem:** The `ThreatModelingAgent` was calling `self.llm_service.generate()` but `LLMService` didn't have this method.

**Symptoms:**
- Execution time: ~1-2ms (way too fast)
- Tokens used: 0 (LLM not being called)
- No attack chains found

**Fix Applied:**
Added `generate()` method to `LLMService` at line 995:
```python
async def generate(
    self,
    prompt: str,
    model: str = None,
    temperature: float = 0.7,
    max_tokens: int = 2048
) -> Dict[str, Any]:
    # Calls Ollama chat endpoint and returns response + tokens_used
```

### Issue #2: Wrong Model Name ✅ FIXED
**Problem:** Code was calling `model="mistral"` but Ollama has `"mistral:7b-instruct"`.

**Fix Applied:**
Updated both agents:
- `threat_modeling_agent.py:110`
- `security_reporter_agent.py:257`

### Issue #3: LLM Returns Valid JSON But Parsing May Fail ⚠️ IN PROGRESS
**Problem:** The LLM CAN generate valid attack chain JSON (verified with direct test), but the full workflow isn't capturing it.

**Test Results:**
```
✅ Direct LLM test: Found 1 attack chain in 796 tokens
❌ Full workflow: Found 0 chains despite using 2149 tokens
```

**Possible causes:**
1. The prompt is too long/complex for the model
2. JSON parsing is silently failing
3. Pydantic validation is rejecting the response
4. The vulnerabilities aren't being described clearly enough

## How to Debug Further

### Step 1: Check the LLM Response

The code now has debug output (line 125-128 in `threat_modeling_agent.py`):
```python
print(f"\n{'='*80}")
print(f"[DEBUG] LLM Response (first 1000 chars):")
print(llm_text[:1000])
print(f"{'='*80}\n")
```

**To see it:**
```bash
cd ai_service
uvicorn app.main:app --reload
# In another terminal:
curl -X POST http://localhost:8000/ai/security/attack-path-simulation \
  -H "Content-Type: application/json" \
  -d @/path/to/test_spec.json
# Look for the DEBUG output in the uvicorn console
```

### Step 2: Check Individual Components

Test each component separately:

**Test 1: Can LLM generate valid JSON?**
```python
python3 /tmp/test_llm_directly.py
```
Expected: ✅ Valid JSON with attack chains

**Test 2: Are vulnerabilities being found?**
```bash
curl -X POST http://localhost:8000/ai/security/analyze \
  -H "Content-Type: application/json" \
  -d '{"spec_text": "..."}'
```
Expected: List of security issues

**Test 3: Is the orchestrator calling all agents?**
Check execution time:
- < 5ms = Scanner only (LLM not called)
- 10-30s = All agents working

### Step 3: Simplify the Prompt

The current prompt is very detailed. If it's too long, the model might get confused. Try this simplified version:

```python
prompt = f"""Find attack chains in these vulnerabilities:

{vulnerabilities_text}

Return JSON:
{{
  "attack_chains": [
    {{
      "name": "Attack name",
      "severity": "CRITICAL",
      "attack_goal": "What happens",
      "steps": [
        {{
          "step_number": 1,
          "endpoint": "/path",
          "http_method": "GET",
          "description": "What attacker does"
        }}
      ]
    }}
  ]
}}

ONLY return valid JSON, no explanation.
"""
```

## Quick Fixes to Try

### Fix A: Use a Larger Model
Mistral 7B might struggle with complex JSON. Try:
```bash
ollama pull codellama:13b-instruct
```

Then update the code:
```python
model="codellama:13b-instruct"
```

### Fix B: Relax Pydantic Validation
The `AttackStep` and `AttackChain` models might be rejecting valid responses. Add:
```python
class Config:
    extra = "ignore"  # Ignore extra fields from LLM
```

### Fix C: Add Retry Logic
If JSON parsing fails, retry with a simpler prompt:
```python
if not attack_chains:
    # Retry with simpler prompt
    simple_prompt = build_simple_prompt(vulnerabilities)
    response = await self.llm_service.generate(...)
```

## Testing the Fix

### Test Scenario: Privilege Escalation

Use this spec (guaranteed to have chainable vulnerabilities):

```yaml
openapi: 3.0.0
paths:
  /users/{id}:
    get:
      parameters:
        - name: id
          in: path
          schema:
            type: integer
      responses:
        '200':
          content:
            application/json:
              schema:
                properties:
                  id: {type: integer}
                  role: {type: string}  # EXPOSES ROLE
    put:
      parameters:
        - name: id
          in: path
          schema:
            type: integer}
      requestBody:
        content:
          application/json:
            schema:
              properties:
                name: {type: string}
                role: {type: string}  # ACCEPTS ROLE (Mass Assignment)
      responses:
        '200': {description: OK}
```

**Expected Result:**
```json
{
  "total_chains_found": 1,
  "critical_chains": [
    {
      "name": "Privilege Escalation via Mass Assignment",
      "steps": 2
    }
  ]
}
```

## Verification Checklist

- [ ] Ollama is running: `curl http://localhost:11434/api/tags`
- [ ] Mistral model exists: Check output includes `"mistral:7b-instruct"`
- [ ] AI service starts: `uvicorn app.main:app --reload`
- [ ] Direct LLM test works: `python3 /tmp/test_llm_directly.py`
- [ ] Scanner finds vulnerabilities: Check `total_vulnerabilities > 0`
- [ ] LLM is being called: Check `tokens_used > 0`
- [ ] Execution takes 10-30s (not < 5ms)
- [ ] Debug output shows LLM response
- [ ] Response is valid JSON
- [ ] Attack chains are parsed successfully

## Next Steps

1. **If tokens_used = 0**: LLM not being called
   → Check if `generate()` method exists in `LLMService`

2. **If tokens_used > 0 but no chains**: LLM called but response invalid
   → Check DEBUG output to see what LLM returned
   → Verify JSON structure matches expected format

3. **If JSON valid but still no chains**: Pydantic validation failing
   → Check error logs for validation errors
   → Add `extra = "ignore"` to Pydantic models

4. **If all else fails**: Use a different approach
   → Skip LLM, use rule-based chain detection
   → Or use a more powerful model (GPT-4, Claude, etc.)

## Contact Points

- LLM Service: `ai_service/app/services/llm_service.py:995`
- Threat Agent: `ai_service/app/services/agents/threat_modeling_agent.py:40`
- Orchestrator: `ai_service/app/services/agents/attack_path_orchestrator.py:26`
- Endpoint: `ai_service/app/api/endpoints.py:1843`

## Success Criteria

✅ Attack Path Simulation is working when:
1. Execution time: 15-30 seconds
2. Tokens used: 1000-3000
3. Attack chains found: > 0 for vulnerable specs
4. Report includes detailed steps
5. Business impact is described
6. Remediation steps are provided

---

**Status:** Partially Fixed
- ✅ LLM is now being called (tokens > 0)
- ⚠️ But chains aren't being discovered yet
- 🔍 Need to check LLM response format

**Last Updated:** 2025-11-14 18:45

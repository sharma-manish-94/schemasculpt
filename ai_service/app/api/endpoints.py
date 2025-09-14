import uuid
import requests
import json
import httpx
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from prance import ResolvingParser
from ..schemas.ai_schemas import AIRequest, AIResponse, MockStartRequest, MockStartResponse
from ..services.llm_service import LLMService

router = APIRouter()
llm_service = LLMService()

MOCKED_APIS = {}


@router.post("/process", response_model=AIResponse)
def process_specification(request: AIRequest):
    updated_spec = llm_service.process_ai_request(request.specText, request.prompt)
    return AIResponse(updatedSpecText=updated_spec)


@router.post("/mock/start", response_model=MockStartResponse)
def start_mock_server(request: MockStartRequest):
    """Parses a spec, stores it, and returns a unique ID and URL for mocking."""
    mock_id = str(uuid.uuid4())
    try:
        # We use a parser to resolve any internal $refs
        parser = ResolvingParser(spec_string=request.specText, backend='openapi-spec-validator')
        MOCKED_APIS[mock_id] = parser.specification
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid OpenAPI Spec: {e}")

    return MockStartResponse(mock_id=mock_id, base_url=f"/mock/{mock_id}")


@router.put("/mock/{mock_id}")
def update_mock_server(mock_id: str, request: MockStartRequest):
    """Updates the specification for an existing mock server session."""
    if mock_id not in MOCKED_APIS:
        raise HTTPException(status_code=404, detail="Mock server not found.")

    try:
        parser = ResolvingParser(spec_string=request.specText, backend='openapi-spec-validator')
        MOCKED_APIS[mock_id] = parser.specification
        return {"message": f"Mock server {mock_id} updated successfully."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid OpenAPI Spec: {e}")

@router.get("/mock/{mock_id}")
@router.get("/mock/{mock_id}/")
def welcome_mock_server(mock_id: str):
    """Provides a friendly welcome message at the root of the mock server."""
    if mock_id not in MOCKED_APIS:
        raise HTTPException(status_code=404, detail="Mock server not found.")

    spec_info = MOCKED_APIS[mock_id].get('info', {})
    spec_title = spec_info.get('title', 'Untitled API')
    spec_version = spec_info.get('version', '')

    return {
        "message": f"Mock server for '{spec_title} v{spec_version}' is running.",
        "docs": "To get a mock response, append a valid path from your specification to this URL (e.g., /pets)."
    }
@router.api_route("/mock/{mock_id}/{full_path:path}")
async def handle_mock_request(mock_id: str, full_path: str, request: Request):
    """Catch-all endpoint to handle requests to the mock server."""
    if mock_id not in MOCKED_APIS:
        raise HTTPException(status_code=404, detail="Mock server not found.")

    spec = MOCKED_APIS[mock_id]
    http_method = request.method.lower()

    path_to_lookup = f'/{full_path}'
    path_spec = spec.get('paths', {}).get(path_to_lookup)
    if not path_spec or http_method not in path_spec:
        raise HTTPException(status_code=404, detail=f"Endpoint {http_method.upper()} {path_to_lookup} not found in spec.")

    operation_spec = path_spec[http_method]

    try:
        response_schema = operation_spec['responses']['200']['content']['application/json']['schema']
    except KeyError:
        return JSONResponse(content={"message": "OK"}, status_code=200)

    data_gen_prompt = f"""[INST] You are a JSON data generation bot. Based on the following OpenAPI schema, generate one realistic JSON object example that conforms to the schema.
Only output the raw JSON object. Do not add explanations or markdown fences.

<SCHEMA>
{response_schema}
</SCHEMA>
[/INST]"""

    payload = {
        "model": "mistral",
        "messages": [{"role": "user", "content": data_gen_prompt}],
        "stream": False,
        "format": "json"
    }

    # Use the asynchronous httpx client
    async with httpx.AsyncClient() as client:
        response = await client.post("http://localhost:11434/api/chat", json=payload, timeout=60.0)

    if response.status_code == 200:
        # Parse the AI's string response into a Python dictionary
        generated_json_str = response.json()['message']['content']
        try:
            content_as_dict = json.loads(generated_json_str)
            return JSONResponse(content=content_as_dict)
        except json.JSONDecodeError:
            # If the AI returns a non-JSON string, return it as plain text
            return JSONResponse(content={"error": "AI returned invalid JSON", "raw_response": generated_json_str}, status_code=500)
    else:
        raise HTTPException(status_code=500, detail=f"Error from LLM: {response.text}")

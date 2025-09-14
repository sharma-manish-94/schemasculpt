from pydantic import BaseModel

class AIRequest(BaseModel):
    specText: str
    prompt: str

class AIResponse(BaseModel):
    updatedSpecText: str

class MockStartRequest(BaseModel):
    specText: str

class MockStartResponse(BaseModel):
    mock_id: str
    base_url: str
from pydantic import BaseModel, Field


class SuggestFixRequest(BaseModel):
    vulnerable_code: str = Field(..., description="The snippet of vulnerable code.")
    language: str = Field(..., description="The programming language of the code.")
    vulnerability_type: str = Field(
        ...,
        description="A description of the vulnerability (e.g., 'BOLA', 'SQL Injection').",
    )


class SuggestFixResponse(BaseModel):
    suggested_fix: str = Field(
        ..., description="The complete, fixed code block suggested by the AI."
    )

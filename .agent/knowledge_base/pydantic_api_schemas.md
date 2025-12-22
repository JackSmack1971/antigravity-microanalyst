# Pattern: Pydantic-based API Contract Enforcement

## Context
Use this when building REST APIs (especially with FastAPI) to ensure strict data validation and synchronization between backend and frontend.

## Problem
APIs often return inconsistent data structures, leading to frontend crashes or "undefined" errors. Documentation frequently goes out of sync with actual code.

## Solution
Centralize all API response models in a `schemas.py` file using Pydantic. Use these models as `response_model` in FastAPI route handlers.

### 1. Define Model
```python
from pydantic import BaseModel, Field
from typing import List, Optional

class ThesisResponse(BaseModel):
    decision: str = Field(..., description="BUY, SELL, or HOLD")
    confidence: float = Field(..., description="Confidence score from 0.0 to 1.0")
    logs: List[str] = Field(default_factory=list)
```

### 2. Enforce in Route
```python
from src.server.schemas import ThesisResponse

@router.get("/latest/thesis", response_model=ThesisResponse)
async def get_latest_thesis():
    # FastAPI automatically validates data against ThesisResponse
    return data 
```

## Gotchas
- **Compatibility**: If a route can return multiple types (e.g., a "waiting" status vs the actual data), use `Union` in the `response_model`.
- **Nesting**: Use `Optional` for fields that might be null in certain states to avoid validation errors.
- **Documentation**: Provide clear `description` fields in `Field(...)` to improve the auto-generated Swagger/OpenAPI docs.

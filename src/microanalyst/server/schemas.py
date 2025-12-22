from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class HealthResponse(BaseModel):
    status: str
    service: str

class ThesisResponse(BaseModel):
    decision: str = Field(..., description="BUY, SELL, or HOLD")
    confidence: float = Field(..., description="Confidence score from 0.0 to 1.0")
    allocation_pct: float = Field(..., description="Percentage of portfolio to allocate")
    reasoning: str = Field(..., description="Summary reasoning for the decision")
    bull_case: Optional[str] = Field(None, description="The retail/bullish perspective")
    bear_case: Optional[str] = Field(None, description="The whale/bearish perspective")
    macro_thesis: Optional[str] = Field(None, description="The macro economist perspective")
    logs: List[str] = Field(default_factory=list, description="System logs from the debate")
    status: Optional[str] = None
    thesis: Optional[Any] = None

class ThesisWrapper(BaseModel):
    status: Optional[str] = None
    thesis: Optional[ThesisResponse] = None

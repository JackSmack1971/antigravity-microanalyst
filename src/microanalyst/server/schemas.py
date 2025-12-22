"""Pydantic response schemas for the Antigravity Swarm API.

This module defines the data models used for API request/response validation and
documentation. All models use Pydantic v2 for automatic validation and OpenAPI
schema generation.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class HealthResponse(BaseModel):
    """Health check response schema.
    
    Attributes:
        status: Current operational status of the API server (e.g., "online", "degraded").
        service: Human-readable service identifier name.
    
    Example:
        >>> health = HealthResponse(status="online", service="Antigravity Swarm API")
        >>> health.status
        'online'
    """
    status: str
    service: str

class ThesisResponse(BaseModel):
    """Market thesis response schema from the adversarial agent swarm.
    
    Represents the synthesized output of multi-agent debate including trading
    decision, confidence scoring, allocation recommendations, and diverse
    perspectives from specialized analyst personas.
    
    Attributes:
        decision: Trading action recommendation. Must be "BUY", "SELL", or "HOLD".
        confidence: Confidence score ranging from 0.0 (no confidence) to 1.0 (maximum confidence).
        allocation_pct: Recommended percentage of portfolio to allocate to this position (0.0-100.0).
        reasoning: Summary reasoning and rationale for the decision from the facilitator agent.
        bull_case: Optional bullish perspective from the Retail Momentum analyst persona.
        bear_case: Optional bearish/cautious perspective from the Whale Sniper analyst persona.
        macro_thesis: Optional structural correlation analysis from the Macro Economist persona.
        logs: System logs documenting the agent debate process and decision flow.
        status: Optional status field for compatibility (e.g., "waiting_for_swarm").
        thesis: Optional nested thesis object for wrapper compatibility.
    
    Example:
        >>> thesis = ThesisResponse(
        ...     decision="BUY",
        ...     confidence=0.85,
        ...     allocation_pct=50.0,
        ...     reasoning="Market momentum accelerating with institutional support",
        ...     bull_case="[RETAIL]: Strong breakout signal...",
        ...     logs=["Debate initiated", "Facilitator reached consensus"]
        ... )
        >>> thesis.decision
        'BUY'
        >>> thesis.confidence
        0.85
    
    Note:
        This schema is used by the `/api/v1/latest/thesis` endpoint. The agent
        swarm generates this data asynchronously via the AgentCoordinator workflow.
    """
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
    """Wrapper schema for thesis availability status.
    
    Used when the agent swarm has not yet generated a thesis. Provides a
    standardized response format indicating the system is waiting for data.
    
    Attributes:
        status: Status message (e.g., "waiting_for_swarm", "error").
        thesis: The actual ThesisResponse object if available, otherwise None.
    
    Example:
        >>> wrapper = ThesisWrapper(status="waiting_for_swarm", thesis=None)
        >>> wrapper.status
        'waiting_for_swarm'
        >>> wrapper.thesis is None
        True
    """
    status: Optional[str] = None
    thesis: Optional[ThesisResponse] = None


# src/microanalyst/agents/schemas.py

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Any, Optional
from datetime import datetime

class AgentRole(Enum):
    """Specialized agent roles"""
    DATA_COLLECTOR = "data_collector"         # Fetches raw data
    VALIDATOR = "validator"                   # Validates data quality
    ANALYST_TECHNICAL = "analyst_technical"   # Technical analysis
    ANALYST_SENTIMENT = "analyst_sentiment"   # Sentiment analysis
    ANALYST_RISK = "analyst_risk"             # Risk assessment
    SYNTHESIZER = "synthesizer"               # Combines analyses
    DECISION_MAKER = "decision_maker"         # Final recommendations
    EXECUTOR = "executor"                     # Executes actions
    PREDICTION_ORACLE = "prediction_oracle"   # Forecasts T+24h signals
    ANALYST_MACRO = "analyst_macro"           # Macro correlation analysis

@dataclass
class AgentCapability:
    """Agent capability specification"""
    role: AgentRole
    tools: List[str]                          # Available tools
    input_schema: Dict[str, Any]              # Expected inputs
    output_schema: Dict[str, Any]             # Produced outputs
    dependencies: List[AgentRole]             # Depends on these roles
    parallel_safe: bool                       # Can run in parallel

@dataclass
class AgentTask:
    """Task assignment for an agent"""
    task_id: str
    role: AgentRole
    priority: int                             # 1-10
    inputs: Dict[str, Any]
    expected_outputs: List[str]
    deadline: Optional[datetime] = None
    retry_policy: Dict[str, Any] = field(default_factory=dict)
    status: str = "pending"
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

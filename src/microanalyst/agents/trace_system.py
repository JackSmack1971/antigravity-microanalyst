from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Literal
from datetime import datetime
import json
from pathlib import Path
import os

@dataclass
class TraceEvent:
    """Single event in agent execution trace"""
    timestamp: datetime
    agent_id: str
    agent_role: str
    event_type: Literal["decision", "tool_call", "data_access", "reasoning_step", "error"]
    description: str
    inputs: Dict[str, Any]
    outputs: Dict[str, Any]
    reasoning: Optional[str] = None
    confidence: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class AgentTrace:
    """Complete execution trace for an agent task"""
    trace_id: str
    objective: str
    agent_id: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    status: Literal["running", "completed", "failed"] = "running"
    events: List[TraceEvent] = field(default_factory=list)
    final_result: Optional[Dict[str, Any]] = None
    total_tool_calls: int = 0
    total_reasoning_steps: int = 0
    
    def add_event(self, event: TraceEvent):
        self.events.append(event)
        if event.event_type == "tool_call":
            self.total_tool_calls += 1
        elif event.event_type == "reasoning_step":
            self.total_reasoning_steps += 1

class TraceCollector:
    """Collects and persists agent execution traces"""
    
    def __init__(self, trace_dir: Path = Path("traces")):
        self.trace_dir = trace_dir
        self.trace_dir.mkdir(parents=True, exist_ok=True)
        self.active_traces: Dict[str, AgentTrace] = {}
    
    def start_trace(
        self,
        trace_id: str,
        objective: str,
        agent_id: str
    ) -> AgentTrace:
        """Initialize new trace"""
        trace = AgentTrace(
            trace_id=trace_id,
            objective=objective,
            agent_id=agent_id,
            started_at=datetime.now(),
            status="running"
        )
        self.active_traces[trace_id] = trace
        return trace
    
    def record_event(
        self,
        trace_id: str,
        event_type: Literal["decision", "tool_call", "data_access", "reasoning_step", "error"],
        description: str,
        inputs: Dict = None,
        outputs: Dict = None,
        reasoning: str = None,
        confidence: float = None,
        **metadata
    ):
        """Record event in active trace"""
        trace = self.active_traces.get(trace_id)
        if not trace:
            return
        
        event = TraceEvent(
            timestamp=datetime.now(),
            agent_id=trace.agent_id,
            agent_role=metadata.get('role', 'unknown'),
            event_type=event_type,
            description=description,
            inputs=inputs or {},
            outputs=outputs or {},
            reasoning=reasoning,
            confidence=confidence,
            metadata=metadata
        )
        
        trace.add_event(event)
    
    def complete_trace(
        self,
        trace_id: str,
        final_result: Dict[str, Any],
        status: Literal["completed", "failed"] = "completed"
    ):
        """Mark trace as completed and persist"""
        trace = self.active_traces.get(trace_id)
        if not trace:
            return
        
        trace.completed_at = datetime.now()
        trace.status = status
        trace.final_result = final_result
        
        # Persist to disk
        self._save_trace(trace)
        
        # Remove from active
        del self.active_traces[trace_id]
    
    def _save_trace(self, trace: AgentTrace):
        """Save trace to JSON file"""
        filename = f"{trace.trace_id}_{trace.started_at.strftime('%Y%m%d_%H%M%S')}.json"
        filepath = self.trace_dir / filename
        
        with open(filepath, 'w') as f:
            json.dump({
                'trace_id': trace.trace_id,
                'objective': trace.objective,
                'agent_id': trace.agent_id,
                'started_at': trace.started_at.isoformat(),
                'completed_at': trace.completed_at.isoformat() if trace.completed_at else None,
                'status': trace.status,
                'total_tool_calls': trace.total_tool_calls,
                'total_reasoning_steps': trace.total_reasoning_steps,
                'events': [
                    {
                        'timestamp': e.timestamp.isoformat(),
                        'agent_role': e.agent_role,
                        'event_type': e.event_type,
                        'description': e.description,
                        'inputs': e.inputs,
                        'outputs': e.outputs,
                        'reasoning': e.reasoning,
                        'confidence': e.confidence,
                        'metadata': e.metadata
                    }
                    for e in trace.events
                ],
                'final_result': trace.final_result
            }, f, indent=2, default=str)
    
    def generate_explainability_report(
        self,
        trace_id: str
    ) -> str:
        """Generate human-readable explanation of agent reasoning"""
        
        # Load trace
        trace_files = list(self.trace_dir.glob(f"{trace_id}_*.json"))
        if not trace_files:
            return "Trace not found"
        
        # Sort by timestamp to get the latest if multiple exist
        trace_files.sort(key=os.path.getmtime, reverse=True)
        
        with open(trace_files[0]) as f:
            trace_data = json.load(f)
        
        # Build narrative
        report = [
            f"# Agent Reasoning Explanation",
            f"",
            f"**Objective**: {trace_data['objective']}",
            f"**Agent**: {trace_data['agent_id']}",
            f"**Duration**: {trace_data['started_at']} → {trace_data['completed_at']}",
            f"**Status**: {trace_data['status']}",
            f"",
            f"## Decision Chain",
            f""
        ]
        
        for i, event in enumerate(trace_data['events'], 1):
            report.append(f"### Event {i}: {event['description']} ({event['event_type']})")
            report.append(f"- **Role**: {event['agent_role']}")
            if event['reasoning']:
                report.append(f"- **Reasoning**: {event['reasoning']}")
            if event['confidence'] is not None:
                report.append(f"- **Confidence**: {event['confidence']:.2%}")
            
            if event['inputs'] and event['event_type'] == 'tool_call':
                report.append(f"- **Inputs**: `{json.dumps(event['inputs'])}`")
            
            report.append("")
        
        report.append(f"## Final Outcome")
        report.append(f"```json")
        report.append(json.dumps(trace_data['final_result'], indent=2))
        report.append(f"```")
        
        return "\n".join(report)

# Global trace collector
trace_collector = TraceCollector()

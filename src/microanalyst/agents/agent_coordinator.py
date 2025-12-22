# src/microanalyst/agents/agent_coordinator.py

import asyncio
import logging
import json
from datetime import datetime
from typing import List, Dict, Any, Optional

from src.microanalyst.agents.schemas import AgentRole, AgentCapability, AgentTask
from src.microanalyst.agents.registry import registry
from src.microanalyst.agents.trace_system import trace_collector

# Task Handlers
from src.microanalyst.agents.tasks.data_collection import handle_data_collection
from src.microanalyst.agents.tasks.analysts import (
    handle_technical_analysis,
    handle_sentiment_analysis,
    handle_risk_analysis,
    handle_macro_analysis
)
from src.microanalyst.agents.tasks.decision import (
    handle_synthesis,
    handle_decision_maker,
    handle_prediction_oracle,
    handle_validation
)

logger = logging.getLogger(__name__)

class AgentCoordinator:
    """
    Orchestrates multi-agent collaboration on market analysis.
    Uses a Modular Registry pattern to decouple orchestration from task logic.
    """
    
    def __init__(self):
        self.agents: Dict[str, AgentCapability] = {}
        self.results: Dict[str, Any] = {}
        self._initialize_registry()
        self._register_default_agents()
    
    def _initialize_registry(self):
        """Initialize the task registry with modular handlers"""
        registry.register(AgentRole.DATA_COLLECTOR, handle_data_collection)
        registry.register(AgentRole.VALIDATOR, handle_validation)
        registry.register(AgentRole.ANALYST_TECHNICAL, handle_technical_analysis)
        registry.register(AgentRole.ANALYST_SENTIMENT, handle_sentiment_analysis)
        registry.register(AgentRole.ANALYST_RISK, handle_risk_analysis)
        registry.register(AgentRole.ANALYST_MACRO, handle_macro_analysis)
        registry.register(AgentRole.SYNTHESIZER, handle_synthesis)
        registry.register(AgentRole.DECISION_MAKER, handle_decision_maker)
        registry.register(AgentRole.PREDICTION_ORACLE, handle_prediction_oracle)

    def _register_default_agents(self):
        """Register capability specification for standard agent roles"""
        
        # Data Collector
        self.agents['data_collector'] = AgentCapability(
            role=AgentRole.DATA_COLLECTOR,
            tools=['fetch_price', 'fetch_flows', 'fetch_derivatives', 'fetch_synthetic'],
            input_schema={'lookback_days': int, 'sources': list},
            output_schema={'price_data': dict, 'flow_data': dict, 'derivatives_data': dict, 'synthetic_metrics': dict},
            dependencies=[],
            parallel_safe=True
        )
        
        # Validator
        self.agents['validator'] = AgentCapability(
            role=AgentRole.VALIDATOR,
            tools=['validate_schema', 'check_freshness', 'cross_validate'],
            input_schema={'raw_data': dict},
            output_schema={'validation_report': dict, 'quality_score': float},
            dependencies=[AgentRole.DATA_COLLECTOR],
            parallel_safe=False
        )

        # Prediction Oracle
        self.agents['prediction_oracle'] = AgentCapability(
            role=AgentRole.PREDICTION_ORACLE,
            tools=['predict_24h', 'aggregate_features'],
            input_schema={'raw_price_history': dict, 'context_metadata': dict},
            output_schema={'direction': str, 'confidence': float, 'price_target': float},
            dependencies=[AgentRole.DATA_COLLECTOR, AgentRole.ANALYST_SENTIMENT],
            parallel_safe=True
        )
        
        # Technical Analyst
        self.agents['analyst_technical'] = AgentCapability(
            role=AgentRole.ANALYST_TECHNICAL,
            tools=['calculate_indicators', 'detect_patterns', 'find_support_resistance'],
            input_schema={'price_data': dict},
            output_schema={'technical_signals': list, 'key_levels': dict},
            dependencies=[AgentRole.VALIDATOR],
            parallel_safe=True
        )
        
        # Sentiment Analyst
        self.agents['analyst_sentiment'] = AgentCapability(
            role=AgentRole.ANALYST_SENTIMENT,
            tools=['analyze_flows', 'detect_divergences', 'sentiment_score'],
            input_schema={'flow_data': dict, 'price_data': dict},
            output_schema={'sentiment_indicators': dict, 'flow_analysis': dict},
            dependencies=[AgentRole.VALIDATOR],
            parallel_safe=True
        )
        
        # Risk Analyst
        self.agents['analyst_risk'] = AgentCapability(
            role=AgentRole.ANALYST_RISK,
            tools=['calculate_volatility', 'identify_tail_risks', 'position_sizing'],
            input_schema={'price_data': dict, 'derivatives_data': dict},
            output_schema={'risk_assessment': dict, 'recommended_sizing': float},
            dependencies=[AgentRole.VALIDATOR],
            parallel_safe=True
        )
        
        # Synthesizer
        self.agents['synthesizer'] = AgentCapability(
            role=AgentRole.SYNTHESIZER,
            tools=['build_reasoning_graph', 'resolve_conflicts', 'generate_narrative'],
            input_schema={'technical_signals': list, 'sentiment_indicators': dict, 'risk_assessment': dict},
            output_schema={'market_context': dict, 'confidence_score': float},
            dependencies=[AgentRole.ANALYST_TECHNICAL, AgentRole.ANALYST_SENTIMENT, AgentRole.ANALYST_RISK],
            parallel_safe=False
        )
        
        # Decision Maker
        self.agents['decision_maker'] = AgentCapability(
            role=AgentRole.DECISION_MAKER,
            tools=['evaluate_opportunities', 'prioritize_actions', 'risk_reward'],
            input_schema={'market_context': dict},
            output_schema={'recommendations': list, 'execution_plan': dict},
            dependencies=[AgentRole.SYNTHESIZER],
            parallel_safe=False
        )

        # Macro Analyst
        self.agents['analyst_macro'] = AgentCapability(
            role=AgentRole.ANALYST_MACRO,
            tools=['analyze_correlations', 'macro_regime_detection'],
            input_schema={'raw_price_history': dict, 'macro_series': dict},
            output_schema={'regime': str, 'confidence': float, 'correlations': list},
            dependencies=[AgentRole.DATA_COLLECTOR],
            parallel_safe=True
        )
    
    async def execute_multi_agent_workflow(
        self,
        objective: str,
        parameters: Dict[str, Any],
        status_callback: Optional[Any] = None
    ) -> Dict[str, Any]:
        """Orchestrates the multi-agent execution pipeline."""
        start_time = datetime.now()
        trace_id = f"trace_{objective.lower().replace(' ', '_')}_{start_time.strftime('%Y%m%d_%H%M%S')}"
        trace_collector.start_trace(trace_id, objective, "coordinator")
        
        # 1. Task Decomposition
        tasks = self._decompose_objective(objective, parameters)
        trace_collector.record_event(
            trace_id, "decision", "Objective decomposed into tasks",
            inputs=parameters, outputs={'task_ids': [t.task_id for t in tasks]},
            role="coordinator"
        )
        
        # 2. Topological Sort (dependency resolution)
        execution_order = self._compute_execution_order(tasks)
        logger.info(f"Executing multi-agent workflow for objective: {objective}")
        
        # 3. Execute in stages
        for stage_idx, stage_tasks in enumerate(execution_order):
            stage_name = f"Stage {stage_idx + 1}/{len(execution_order)}"
            logger.info(f"Starting {stage_name} ({len(stage_tasks)} tasks)")
            
            if status_callback:
                task_summaries = ", ".join([str(t.role.value).split('.')[-1] for t in stage_tasks])
                status_callback(f"Initiating {stage_name}: {task_summaries}")

            # Parallel execution within stage
            stage_results = await asyncio.gather(*[
                self._execute_agent_task(task, trace_id) for task in stage_tasks
            ], return_exceptions=True)
            
            # Store results
            for task, result in zip(stage_tasks, stage_results):
                if isinstance(result, Exception):
                    logger.error(f"Task {task.task_id} failed: {result}")
                    task.status = "failed"
                    task.error = str(result)
                    trace_collector.record_event(
                        trace_id, "error", f"Task {task.task_id} failed",
                        inputs=task.inputs, outputs={'error': str(result)},
                        role=task.role.value
                    )
                else:
                    self.results[task.task_id] = result
                    task.status = "completed"
                    task.result = result
                    trace_collector.record_event(
                        trace_id, "decision", f"Task {task.task_id} completed",
                        inputs=task.inputs, outputs=result,
                        role=task.role.value
                    )
        
        # 4. Final synthesis
        final_result = {}
        for task_id, result in self.results.items():
            if task_id.startswith("decide"):
                final_result = result
                break
        
        total_time = (datetime.now() - start_time).total_seconds()
        workflow_summary = {
            'objective': objective,
            'final_result': final_result,
            'tasks_executed': [t.task_id for t in tasks],
            'execution_time': total_time
        }
        trace_collector.complete_trace(trace_id, workflow_summary)
        return workflow_summary
    
    def _decompose_objective(self, objective: str, parameters: Dict[str, Any]) -> List[AgentTask]:
        """Decomposes an objective into atomic agent tasks."""
        tasks = []
        if "comprehensive_analysis" in objective.lower():
            tasks.extend([
                AgentTask("collect_data", AgentRole.DATA_COLLECTOR, 10, parameters, ['price_data', 'flow_data']),
                AgentTask("validate_data", AgentRole.VALIDATOR, 9, {'depends_on': 'collect_data'}, ['validation_report']),
                AgentTask("analyze_technical", AgentRole.ANALYST_TECHNICAL, 8, {'depends_on': 'validate_data'}, ['technical_signals']),
                AgentTask("analyze_sentiment", AgentRole.ANALYST_SENTIMENT, 8, {'depends_on': 'validate_data'}, ['sentiment_indicators']),
                AgentTask("analyze_risk", AgentRole.ANALYST_RISK, 8, {'depends_on': 'validate_data'}, ['risk_assessment']),
                AgentTask("analyze_macro", AgentRole.ANALYST_MACRO, 8, {'depends_on': 'collect_data'}, ['regime']),
                AgentTask("predict_oracle", AgentRole.PREDICTION_ORACLE, 7, {'depends_on': 'collect_data'}, ['direction']),
                AgentTask("synthesize", AgentRole.SYNTHESIZER, 5, {'depends_on': ['analyze_technical', 'analyze_sentiment', 'analyze_risk', 'analyze_macro', 'predict_oracle']}, ['market_context']),
                AgentTask("decide", AgentRole.DECISION_MAKER, 1, {'depends_on': 'synthesize'}, ['recommendations'])
            ])
        else:
            # Simple fallback
            tasks.append(AgentTask("collect_data", AgentRole.DATA_COLLECTOR, 10, parameters, ['price_data']))
            tasks.append(AgentTask("decide", AgentRole.DECISION_MAKER, 1, {'depends_on': 'collect_data'}, ['recommendations']))
        return tasks
    
    def _compute_execution_order(self, tasks: List[AgentTask]) -> List[List[AgentTask]]:
        """Topological sort with parallel grouping for task execution."""
        task_map = {t.task_id: t for t in tasks}
        in_degree = {tid: 0 for tid in task_map}
        graph = {tid: [] for tid in task_map}
        
        for task in tasks:
            depends_on = task.inputs.get('depends_on', [])
            if isinstance(depends_on, str): depends_on = [depends_on]
            
            in_degree[task.task_id] = len(depends_on)
            for dep_id in depends_on:
                if dep_id in graph: graph[dep_id].append(task.task_id)
        
        execution_order = []
        while task_map:
            ready_ids = [tid for tid, degree in in_degree.items() if degree == 0 and tid in task_map]
            if not ready_ids: break
            ready_tasks = [task_map[tid] for tid in ready_ids]
            execution_order.append(ready_tasks)
            for tid in ready_ids:
                del task_map[tid]
                for neighbor_id in graph[tid]:
                    if neighbor_id in in_degree: in_degree[neighbor_id] -= 1
        return execution_order
    
    async def _execute_agent_task(self, task: AgentTask, trace_id: str = None) -> Dict[str, Any]:
        """Delegates task execution to the appropriate registry handler."""
        task.started_at = datetime.now()
        task.status = "running"
        
        handler = registry.get_handler(task.role)
        if not handler: raise ValueError(f"No handler registered for role {task.role}")
        
        # Resolve dependencies via Blackboard pattern (cumulative context)
        resolved_inputs = {}
        # Merge all previous results in the order they were completed
        for prev_res in self.results.values():
            resolved_inputs.update(prev_res)
            
        # Ensure specific task inputs override blackboard defaults
        final_inputs = {**resolved_inputs, **task.inputs}
        
        if trace_id:
            trace_collector.record_event(
                trace_id, "reasoning_step", f"Agent {task.role.value} starting {task.task_id}",
                inputs=final_inputs, role=task.role.value, confidence=0.95
            )
        
        result = await handler(final_inputs)
        task.completed_at = datetime.now()
        return result

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    coordinator = AgentCoordinator()
    async def run_test():
        result = await coordinator.execute_multi_agent_workflow("comprehensive_analysis", {"lookback_days": 30})
        print(json.dumps(result, indent=2))
    asyncio.run(run_test())

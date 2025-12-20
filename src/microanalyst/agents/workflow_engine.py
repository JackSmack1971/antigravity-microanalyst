# src/microanalyst/agents/workflow_engine.py
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Callable, Union
from enum import Enum
import asyncio
import logging
from datetime import datetime
import json
import hashlib
from pathlib import Path
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

class WorkflowStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"
    CANCELLED = "cancelled"

class TaskType(Enum):
    DATA_LOAD = "data_load"
    CALCULATION = "calculation"
    ANALYSIS = "analysis"
    SYNTHESIS = "synthesis"
    VISUALIZATION = "visualization"
    EXPORT = "export"

@dataclass
class WorkflowTask:
    """Single task within a workflow."""
    task_id: str
    task_type: TaskType
    function: Callable
    params: Dict[str, Any]
    dependencies: List[str] = field(default_factory=list)
    retry_policy: Optional[Dict] = None
    timeout_seconds: int = 300
    cache_result: bool = True
    parallel_safe: bool = True
    
    # Runtime state
    status: WorkflowStatus = WorkflowStatus.PENDING
    result: Any = None
    error: Optional[Exception] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    execution_time: float = 0.0

@dataclass
class WorkflowDefinition:
    """Complete workflow specification."""
    workflow_id: str
    name: str
    description: str
    version: str
    tasks: List[WorkflowTask]
    parameters: Dict[str, Any] = field(default_factory=dict)
    outputs: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def get_task(self, task_id: str) -> Optional[WorkflowTask]:
        return next((t for t in self.tasks if t.task_id == task_id), None)
    
    def get_dependencies_for(self, task_id: str) -> List[WorkflowTask]:
        """Get all dependency tasks for a given task."""
        task = self.get_task(task_id)
        if not task:
            return []
        return [self.get_task(dep_id) for dep_id in task.dependencies]
    
    def get_execution_order(self) -> List[List[str]]:
        """
        Compute execution order using topological sort.
        Returns list of task groups that can be executed in parallel.
        """
        # Build dependency graph
        graph = {task.task_id: set(task.dependencies) for task in self.tasks}
        in_degree = {task.task_id: len(task.dependencies) for task in self.tasks}
        
        execution_order = []
        
        while graph:
            # Find tasks with no dependencies
            ready = [tid for tid, deps in graph.items() if in_degree[tid] == 0]
            
            if not ready:
                raise ValueError("Circular dependency detected in workflow")
            
            execution_order.append(ready)
            
            # Remove ready tasks from graph
            for tid in ready:
                del graph[tid]
                # Update in_degree for dependent tasks
                for other_tid in list(graph.keys()):
                    if tid in graph[other_tid]:
                        graph[other_tid].remove(tid)
                        in_degree[other_tid] -= 1
        
        return execution_order

@dataclass
class WorkflowExecution:
    """Runtime execution state."""
    execution_id: str
    workflow_def: WorkflowDefinition
    status: WorkflowStatus
    parameters: Dict[str, Any]
    
    # Execution tracking
    started_at: datetime
    completed_at: Optional[datetime] = None
    execution_time: float = 0.0
    
    # Results
    task_results: Dict[str, Any] = field(default_factory=dict)
    final_result: Optional[Dict[str, Any]] = None
    error: Optional[Exception] = None
    
    # Progress tracking
    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    
    def progress_percentage(self) -> float:
        if self.total_tasks == 0:
            return 0.0
        return (self.completed_tasks / self.total_tasks) * 100

class WorkflowEngine:
    """
    Orchestrates workflow execution with:
    - Dependency resolution
    - Parallel execution
    - Checkpointing and recovery
    - Result caching
    - Progress tracking
    """
    
    def __init__(self, cache_dir: Path = None, redis_client=None, enable_tracing: bool = True):
        self.workflows: Dict[str, WorkflowDefinition] = {}
        self.executions: Dict[str, WorkflowExecution] = {}
        self.cache_dir = cache_dir or Path("workflow_cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.redis = redis_client
        self.enable_tracing = enable_tracing
        if enable_tracing:
            from src.microanalyst.agents.trace_system import trace_collector
            self.tracer = trace_collector
        
        logger.info("WorkflowEngine initialized")
    
    def register_workflow(self, workflow: WorkflowDefinition):
        """Register a workflow definition."""
        self.workflows[workflow.workflow_id] = workflow
        logger.info(f"Registered workflow: {workflow.workflow_id} (v{workflow.version})")
    
    async def execute(self, 
                     workflow_id: str,
                     parameters: Dict[str, Any] = None,
                     checkpoint_interval: int = 5) -> Dict[str, Any]:
        """
        Execute a workflow asynchronously.
        
        Args:
            workflow_id: Registered workflow identifier
            parameters: Runtime parameters
            checkpoint_interval: Save state every N tasks
        
        Returns:
            Final workflow results
        """
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not registered")
        
        # Create execution context
        execution_id = self._generate_execution_id(workflow_id, parameters)
        execution = WorkflowExecution(
            execution_id=execution_id,
            workflow_def=workflow,
            status=WorkflowStatus.RUNNING,
            parameters=parameters or {},
            started_at=datetime.now(),
            total_tasks=len(workflow.tasks)
        )
        
        self.executions[execution_id] = execution
        return await self._run_execution(execution, checkpoint_interval)

    async def start_execution(self, 
                            workflow_id: str,
                            parameters: Dict[str, Any] = None,
                            checkpoint_interval: int = 5) -> str:
        """
        Start a workflow in the background and return the execution_id immediately.
        """
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not registered")
        
        execution_id = self._generate_execution_id(workflow_id, parameters)
        execution = WorkflowExecution(
            execution_id=execution_id,
            workflow_def=workflow,
            status=WorkflowStatus.RUNNING,
            parameters=parameters or {},
            started_at=datetime.now(),
            total_tasks=len(workflow.tasks)
        )
        
        self.executions[execution_id] = execution
        
        # Run in background
        asyncio.create_task(self._run_execution(execution, checkpoint_interval))
        
        return execution_id

    async def _run_execution(self, execution: WorkflowExecution, checkpoint_interval: int) -> Dict[str, Any]:
        """Core execution loop logic."""
        execution_id = execution.execution_id
        workflow = execution.workflow_def
        
        logger.info(f"Starting workflow execution: {execution_id}")
        
        try:
            if self.enable_tracing:
                self.tracer.start_trace(
                    trace_id=execution_id,
                    objective=f"Execute workflow: {workflow.workflow_id}",
                    agent_id="workflow_engine"
                )
                self.tracer.record_event(
                    trace_id=execution_id,
                    event_type="decision",
                    description=f"Starting workflow {workflow.workflow_id}",
                    inputs=execution.parameters,
                    reasoning=f"Workflow engine triggered for {workflow.workflow_id}",
                    role="orchestrator"
                )
            # Get execution order (topological sort)
            execution_order = workflow.get_execution_order()
            
            # Execute task groups in order (parallel within groups)
            for task_group in execution_order:
                await self._execute_task_group(execution, task_group)
                
                # Checkpoint
                if execution.completed_tasks % checkpoint_interval == 0:
                    await self._checkpoint(execution)
            
            # Finalize execution state
            execution.status = WorkflowStatus.COMPLETED
            execution.completed_at = datetime.now()
            execution.execution_time = (execution.completed_at - execution.started_at).total_seconds()
            
            # Synthesize final result
            final_result = self._synthesize_results(execution)
            execution.final_result = final_result
            
            logger.info(f"Workflow completed: {execution_id} ({execution.execution_time:.2f}s)")
            
            if self.enable_tracing:
                self.tracer.complete_trace(
                    trace_id=execution_id,
                    final_result=final_result,
                    status=execution.status.value
                )
            
            return final_result
            
        except Exception as e:
            execution.status = WorkflowStatus.FAILED
            execution.error = e
            execution.completed_at = datetime.now()
            logger.error(f"Workflow failed: {execution_id} - {e}")
            
            if self.enable_tracing:
                self.tracer.record_event(
                    trace_id=execution_id,
                    event_type="error",
                    description=f"Workflow failed: {str(e)}",
                    role="orchestrator"
                )
                self.tracer.complete_trace(
                    trace_id=execution_id,
                    final_result={"error": str(e)},
                    status=execution.status.value
                )
            raise
    
    async def _execute_task_group(self, execution: WorkflowExecution, task_ids: List[str]):
        """Execute a group of tasks in parallel."""
        tasks = [execution.workflow_def.get_task(tid) for tid in task_ids]
        
        # Check if all tasks are parallel-safe
        if all(t.parallel_safe for t in tasks):
            # Execute in parallel
            results = await asyncio.gather(
                *[self._execute_task(execution, task) for task in tasks],
                return_exceptions=True
            )
            
            for task, result in zip(tasks, results):
                if isinstance(result, Exception):
                    logger.error(f"Task {task.task_id} failed: {result}")
                    execution.failed_tasks += 1
                    task.error = result
                    task.status = WorkflowStatus.FAILED
                else:
                    execution.task_results[task.task_id] = result
                    execution.completed_tasks += 1
        else:
            # Execute sequentially (one task requires sequential execution)
            for task in tasks:
                try:
                    result = await self._execute_task(execution, task)
                    execution.task_results[task.task_id] = result
                    execution.completed_tasks += 1
                except Exception as e:
                    logger.error(f"Task {task.task_id} failed: {e}")
                    execution.failed_tasks += 1
                    task.error = e
                    task.status = WorkflowStatus.FAILED
    
    async def _execute_task(self, execution: WorkflowExecution, task: WorkflowTask) -> Any:
        """Execute a single task with retry logic and caching."""
        logger.info(f"Executing task: {task.task_id}")
        
        task.started_at = datetime.now()
        task.status = WorkflowStatus.RUNNING
        
        # Resolve dependencies and check for failures
        dep_results = {}
        for dep_id in task.dependencies:
            dep_task = execution.workflow_def.get_task(dep_id)
            if dep_task and dep_task.status == WorkflowStatus.FAILED:
                task.status = WorkflowStatus.FAILED
                task.error = ValueError(f"Dependency {dep_id} failed")
                logger.error(f"Task {task.task_id} failed because dependency {dep_id} failed")
                raise task.error
            
            if dep_id not in execution.task_results:
                task.status = WorkflowStatus.FAILED
                task.error = KeyError(f"Dependency {dep_id} result missing")
                raise task.error
                
            dep_results[dep_id] = execution.task_results[dep_id]
        
        # Check cache
        if task.cache_result:
            cached_result = await self._get_cached_result(task, execution.parameters)
            if cached_result is not None:
                logger.info(f"Task {task.task_id} result retrieved from cache")
                task.result = cached_result
                task.status = WorkflowStatus.COMPLETED
                task.completed_at = datetime.now()
                return cached_result
        
        # Merge task params with dependencies and workflow params
        task_params = {
            **execution.parameters,
            **task.params,
            **dep_results
        }
        
        # Execute with retry policy
        retry_policy = task.retry_policy or {"max_attempts": 1, "backoff": 1}
        max_attempts = retry_policy.get("max_attempts", 1)
        backoff = retry_policy.get("backoff", 1)
        
        for attempt in range(max_attempts):
            try:
                # Execute with timeout
                result = await asyncio.wait_for(
                    task.function(**task_params),
                    timeout=task.timeout_seconds
                )
                
                task.result = result
                task.status = WorkflowStatus.COMPLETED
                task.completed_at = datetime.now()
                task.execution_time = (task.completed_at - task.started_at).total_seconds()
                
                # Cache result
                if task.cache_result:
                    await self._cache_result(task, execution.parameters, result)
                
                logger.info(f"Task {task.task_id} completed ({task.execution_time:.2f}s)")
                return result
                
            except asyncio.TimeoutError:
                logger.warning(f"Task {task.task_id} timed out (attempt {attempt + 1}/{max_attempts})")
                if attempt < max_attempts - 1:
                    await asyncio.sleep(backoff * (2 ** attempt))
                else:
                    raise
                    
            except Exception as e:
                logger.warning(f"Task {task.task_id} failed (attempt {attempt + 1}/{max_attempts}): {e}")
                if attempt < max_attempts - 1:
                    await asyncio.sleep(backoff * (2 ** attempt))
                else:
                    raise
        
        raise RuntimeError(f"Task {task.task_id} failed after {max_attempts} attempts")
    
    async def _get_cached_result(self, task: WorkflowTask, params: Dict) -> Optional[Any]:
        """Retrieve cached result if available."""
        cache_key = self._generate_cache_key(task.task_id, params, task.params)
        
        # Try Redis
        if self.redis:
            cached = await self.redis.get(f"workflow_cache:{cache_key}")
            if cached:
                return self._deserialize_result(json.loads(cached))
        
        # Fallback to file cache
        cache_file = self.cache_dir / f"{cache_key}.json"
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    return self._deserialize_result(json.load(f))
            except Exception as e:
                logger.warning(f"Failed to read cache for {task.task_id}: {e}")
        
        return None
    
    async def _cache_result(self, task: WorkflowTask, params: Dict, result: Any):
        """Cache task result."""
        cache_key = self._generate_cache_key(task.task_id, params, task.params)
        
        try:
            # Handle DataFrames specially
            serialized_data = self._serialize_result(result)
            serialized_json = json.dumps(serialized_data, default=str)
            
            if self.redis:
                await self.redis.setex(f"workflow_cache:{cache_key}", 3600, serialized_json)
            
            # File cache
            cache_file = self.cache_dir / f"{cache_key}.json"
            with open(cache_file, 'w') as f:
                f.write(serialized_json)
                
        except Exception as e:
            logger.warning(f"Failed to cache result for {task.task_id}: {e}")

    def _serialize_result(self, result: Any) -> Any:
        """Helper to serialize complex types like DataFrames."""
        if isinstance(result, pd.DataFrame):
            return {"__type__": "pd.DataFrame", "data": result.to_json(orient='split', date_format='iso')}
        elif isinstance(result, dict):
            return {k: self._serialize_result(v) for k, v in result.items()}
        elif isinstance(result, list):
            return [self._serialize_result(v) for v in result]
        return result

    def _deserialize_result(self, result: Any) -> Any:
        """Helper to deserialize complex types."""
        if isinstance(result, dict) and "__type__" in result:
            if result["__type__"] == "pd.DataFrame":
                return pd.read_json(result["data"], orient='split')
        elif isinstance(result, dict):
            return {k: self._deserialize_result(v) for k, v in result.items()}
        elif isinstance(result, list):
            return [self._deserialize_result(v) for v in result]
        return result

    
    async def _checkpoint(self, execution: WorkflowExecution):
        """Save execution state for recovery."""
        checkpoint_file = self.cache_dir / f"{execution.execution_id}_checkpoint.json"
        
        checkpoint_data = {
            "execution_id": execution.execution_id,
            "workflow_id": execution.workflow_def.workflow_id,
            "status": execution.status.value,
            "started_at": execution.started_at.isoformat(),
            "completed_tasks": execution.completed_tasks,
            "failed_tasks": execution.failed_tasks,
            "task_results": {k: str(v) for k, v in execution.task_results.items()}  # Simplified serialization
        }
        
        with open(checkpoint_file, 'w') as f:
            json.dump(checkpoint_data, f, indent=2)
        
        logger.debug(f"Checkpoint saved: {checkpoint_file}")
    
    def _synthesize_results(self, execution: WorkflowExecution) -> Dict[str, Any]:
        """Combine task results into final output."""
        # Extract specified outputs
        final_result = {
            "workflow_id": execution.workflow_def.workflow_id,
            "execution_id": execution.execution_id,
            "status": execution.status.value,
            "execution_time": execution.execution_time,
            "completed_tasks": execution.completed_tasks,
            "failed_tasks": execution.failed_tasks,
            "outputs": {}
        }
        
        # Include specified output tasks
        for output_task_id in execution.workflow_def.outputs:
            if output_task_id in execution.task_results:
                final_result["outputs"][output_task_id] = execution.task_results[output_task_id]
        
        return final_result
    
    def _generate_execution_id(self, workflow_id: str, params: Dict) -> str:
        """Generate unique execution identifier."""
        timestamp = datetime.now().isoformat()
        content = f"{workflow_id}:{timestamp}:{json.dumps(params, sort_keys=True)}"
        return hashlib.md5(content.encode()).hexdigest()[:16]
    
    def _generate_cache_key(self, task_id: str, workflow_params: Dict, task_params: Dict) -> str:
        """Generate cache key for task result."""
        content = f"{task_id}:{json.dumps(workflow_params, sort_keys=True)}:{json.dumps(task_params, sort_keys=True)}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def get_execution_status(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get current status of a workflow execution."""
        execution = self.executions.get(execution_id)
        if not execution:
            return None
        
        return {
            "execution_id": execution_id,
            "workflow_id": execution.workflow_def.workflow_id,
            "status": execution.status.value,
            "progress_pct": execution.progress_percentage(),
            "completed_tasks": execution.completed_tasks,
            "failed_tasks": execution.failed_tasks,
            "total_tasks": execution.total_tasks,
            "started_at": execution.started_at.isoformat(),
            "execution_time": (datetime.now() - execution.started_at).total_seconds()
        }


# ===================================================================
# WORKFLOW BUILDER - Declarative Workflow Construction
# ===================================================================

class WorkflowBuilder:
    """Fluent API for building workflows."""
    
    def __init__(self, workflow_id: str, name: str):
        self.workflow_id = workflow_id
        self.name = name
        self.tasks: List[WorkflowTask] = []
        self.description = ""
        self.version = "1.0.0"
        self.outputs = []
        self.metadata = {}
    
    def with_description(self, description: str):
        self.description = description
        return self
    
    def with_version(self, version: str):
        self.version = version
        return self
    
    def add_task(self,
                task_id: str,
                task_type: TaskType,
                function: Callable,
                params: Dict = None,
                dependencies: List[str] = None,
                **kwargs):
        """Add a task to the workflow."""
        task = WorkflowTask(
            task_id=task_id,
            task_type=task_type,
            function=function,
            params=params or {},
            dependencies=dependencies or [],
            **kwargs
        )
        self.tasks.append(task)
        return self
    
    def with_outputs(self, *output_task_ids: str):
        """Specify which task results should be included in final output."""
        self.outputs.extend(output_task_ids)
        return self
    
    def build(self) -> WorkflowDefinition:
        """Build the workflow definition."""
        return WorkflowDefinition(
            workflow_id=self.workflow_id,
            name=self.name,
            description=self.description,
            version=self.version,
            tasks=self.tasks,
            outputs=self.outputs,
            metadata=self.metadata
        )


# ===================================================================
# PRE-BUILT WORKFLOWS
# ===================================================================

class ResearchWorkflows:
    """Collection of pre-built research workflows."""
    
    def __init__(self, engine: WorkflowEngine):
        self.engine = engine
        self._register_all_workflows()
    
    def _register_all_workflows(self):
        """Register all pre-built workflows."""
        self.engine.register_workflow(self.build_price_action_workflow())
        self.engine.register_workflow(self.build_sentiment_workflow())
        self.engine.register_workflow(self.build_derivatives_workflow())
        self.engine.register_workflow(self.build_comprehensive_workflow())
        self.engine.register_workflow(self.build_correlation_workflow())
        self.engine.register_workflow(self.build_risk_assessment_workflow())
        
        logger.info("Registered 6 research workflows")
    
    # ===================================================================
    # WORKFLOW 1: Price Action Deep Dive
    # ===================================================================
    
    def build_price_action_workflow(self) -> WorkflowDefinition:
        """
        Comprehensive price action analysis:
        - Multi-timeframe structure
        - Support/resistance levels
        - Technical indicators
        - Chart patterns
        - Confluence zones
        """
        builder = (WorkflowBuilder("price_action_deep_dive", "Price Action Deep Dive")
            .with_description("Comprehensive technical analysis of price structure")
            .with_version("2.0.0"))
        
        # Task 1: Load price data
        builder.add_task(
            task_id="load_price_data",
            task_type=TaskType.DATA_LOAD,
            function=self._load_price_data,
            params={},
            cache_result=True,
            timeout_seconds=30
        )
        
        # Task 2: Calculate technical indicators
        builder.add_task(
            task_id="calculate_indicators",
            task_type=TaskType.CALCULATION,
            function=self._calculate_indicators,
            params={},
            dependencies=["load_price_data"],
            parallel_safe=True
        )
        
        # Task 3: Detect support/resistance
        builder.add_task(
            task_id="detect_support_resistance",
            task_type=TaskType.ANALYSIS,
            function=self._detect_support_resistance,
            params={},
            dependencies=["load_price_data"],
            parallel_safe=True
        )
        
        # Task 4: Identify chart patterns
        builder.add_task(
            task_id="detect_patterns",
            task_type=TaskType.ANALYSIS,
            function=self._detect_chart_patterns,
            params={},
            dependencies=["load_price_data"],
            parallel_safe=True
        )
        
        # Task 5: Calculate confluence zones
        builder.add_task(
            task_id="calculate_confluence",
            task_type=TaskType.ANALYSIS,
            function=self._calculate_confluence_zones,
            params={},
            dependencies=["load_price_data", "detect_support_resistance"],
            parallel_safe=True
        )
        
        # Task 6: Detect signals
        builder.add_task(
            task_id="detect_signals",
            task_type=TaskType.ANALYSIS,
            function=self._detect_trading_signals,
            params={},
            dependencies=["load_price_data", "calculate_indicators", "calculate_confluence"]
        )
        
        # Task 7: Synthesize analysis
        builder.add_task(
            task_id="synthesize_analysis",
            task_type=TaskType.SYNTHESIS,
            function=self._synthesize_price_analysis,
            params={},
            dependencies=[
                "calculate_indicators",
                "detect_support_resistance",
                "detect_patterns",
                "calculate_confluence",
                "detect_signals"
            ]
        )
        
        builder.with_outputs("synthesize_analysis")
        
        return builder.build()
    
    # ===================================================================
    # WORKFLOW 2: Sentiment Analysis
    # ===================================================================
    
    def build_sentiment_workflow(self) -> WorkflowDefinition:
        """
        ETF flow and market sentiment analysis:
        - Flow trends and reversals
        - Institutional positioning
        - Sentiment divergences
        """
        builder = (WorkflowBuilder("sentiment_analysis", "Market Sentiment Analysis")
            .with_description("Analyze ETF flows and institutional sentiment")
            .with_version("2.0.0"))
        
        # Task 1: Load ETF flow data
        builder.add_task(
            task_id="load_flow_data",
            task_type=TaskType.DATA_LOAD,
            function=self._load_etf_data,
            params={}
        )
        
        # Task 2: Load price data for context
        builder.add_task(
            task_id="load_price_data",
            task_type=TaskType.DATA_LOAD,
            function=self._load_price_data,
            params={},
            parallel_safe=True
        )
        
        # Task 3: Calculate flow metrics
        builder.add_task(
            task_id="calculate_flow_metrics",
            task_type=TaskType.CALCULATION,
            function=self._calculate_flow_metrics,
            params={},
            dependencies=["load_flow_data"]
        )
        
        # Task 4: Detect flow anomalies
        builder.add_task(
            task_id="detect_flow_anomalies",
            task_type=TaskType.ANALYSIS,
            function=self._detect_flow_anomalies,
            params={},
            dependencies=["load_flow_data", "calculate_flow_metrics"]
        )
        
        # Task 5: Calculate price-flow divergence
        builder.add_task(
            task_id="analyze_divergence",
            task_type=TaskType.ANALYSIS,
            function=self._analyze_price_flow_divergence,
            params={},
            dependencies=["load_price_data", "load_flow_data"]
        )
        
        # Task 6: Sentiment synthesis
        builder.add_task(
            task_id="synthesize_sentiment",
            task_type=TaskType.SYNTHESIS,
            function=self._synthesize_sentiment_analysis,
            params={},
            dependencies=[
                "calculate_flow_metrics",
                "detect_flow_anomalies",
                "analyze_divergence"
            ]
        )
        
        builder.with_outputs("synthesize_sentiment")
        
        return builder.build()
    
    # ===================================================================
    # WORKFLOW 3: Derivatives Positioning
    # ===================================================================
    
    def build_derivatives_workflow(self) -> WorkflowDefinition:
        """
        Analyze derivatives market positioning:
        - Funding rates
        - Open interest
        - Liquidation levels
        - Options skew
        """
        builder = (WorkflowBuilder("derivatives_analysis", "Derivatives Market Analysis")
            .with_description("Analyze futures and options positioning")
            .with_version("1.0.0"))
        
        # Task 1: Load derivatives data
        builder.add_task(
            task_id="load_derivatives_data",
            task_type=TaskType.DATA_LOAD,
            function=self._load_derivatives_data,
            params={}
        )
        
        # Task 2: Analyze funding rates
        builder.add_task(
            task_id="analyze_funding",
            task_type=TaskType.ANALYSIS,
            function=self._analyze_funding_rates,
            params={},
            dependencies=["load_derivatives_data"]
        )
        
        # Task 3: Analyze open interest
        builder.add_task(
            task_id="analyze_open_interest",
            task_type=TaskType.ANALYSIS,
            function=self._analyze_open_interest,
            params={},
            dependencies=["load_derivatives_data"]
        )
        
        # Task 4: Identify liquidation clusters
        builder.add_task(
            task_id="identify_liquidation_levels",
            task_type=TaskType.ANALYSIS,
            function=self._identify_liquidation_levels,
            params={},
            dependencies=["load_derivatives_data"]
        )
        
        # Task 5: Synthesize derivatives view
        builder.add_task(
            task_id="synthesize_derivatives",
            task_type=TaskType.SYNTHESIS,
            function=self._synthesize_derivatives_analysis,
            params={},
            dependencies=[
                "analyze_funding",
                "analyze_open_interest",
                "identify_liquidation_levels"
            ]
        )
        
        builder.with_outputs("synthesize_derivatives")
        
        return builder.build()
    
    # ===================================================================
    # WORKFLOW 4: Comprehensive Market Report
    # ===================================================================
    
    def build_comprehensive_workflow(self) -> WorkflowDefinition:
        """
        Complete market analysis combining all factors:
        - Price action
        - Sentiment
        - Derivatives
        - Regime detection
        - Risk assessment
        """
        builder = (WorkflowBuilder("comprehensive_report", "Comprehensive Market Report")
            .with_description("Full-spectrum market analysis")
            .with_version("2.0.0"))
        
        # Task 1: Execute price action workflow
        builder.add_task(
            task_id="price_action_analysis",
            task_type=TaskType.ANALYSIS,
            function=lambda **kwargs: self.engine.execute("price_action_deep_dive", kwargs),
            params={}
        )
        
        # Task 2: Execute sentiment workflow
        builder.add_task(
            task_id="sentiment_analysis",
            task_type=TaskType.ANALYSIS,
            function=lambda **kwargs: self.engine.execute("sentiment_analysis", kwargs),
            params={},
            parallel_safe=True
        )
        
        # Task 3: Execute derivatives workflow
        builder.add_task(
            task_id="derivatives_analysis",
            task_type=TaskType.ANALYSIS,
            function=lambda **kwargs: self.engine.execute("derivatives_analysis", kwargs),
            params={},
            parallel_safe=True
        )
        
        # Task 4: Detect market regime
        builder.add_task(
            task_id="detect_regime",
            task_type=TaskType.ANALYSIS,
            function=self._detect_market_regime,
            params={}
        )
        
        # Task 5: Cross-factor synthesis
        builder.add_task(
            task_id="synthesize_comprehensive",
            task_type=TaskType.SYNTHESIS,
            function=self._synthesize_comprehensive_report,
            params={},
            dependencies=[
                "price_action_analysis",
                "sentiment_analysis",
                "derivatives_analysis",
                "detect_regime"
            ]
        )
        
        # Task 6: Generate executive summary
        builder.add_task(
            task_id="generate_executive_summary",
            task_type=TaskType.SYNTHESIS,
            function=self._generate_executive_summary,
            params={},
            dependencies=["synthesize_comprehensive"]
        )
        
        builder.with_outputs("synthesize_comprehensive", "generate_executive_summary")
        
        return builder.build()
    
    # ===================================================================
    # WORKFLOW 5: Correlation Analysis
    # ===================================================================
    
    def build_correlation_workflow(self) -> WorkflowDefinition:
        """
        Analyze correlations across datasets:
        - Price-flow correlation
        - Price-OI correlation
        - Inter-timeframe correlations
        """
        builder = (WorkflowBuilder("correlation_analysis", "Cross-Factor Correlation")
            .with_description("Analyze relationships between market factors")
            .with_version("1.0.0"))
        
        # Load all data in parallel
        builder.add_task(
            task_id="load_price_data",
            task_type=TaskType.DATA_LOAD,
            function=self._load_price_data,
            params={},
            parallel_safe=True
        )
        
        builder.add_task(
            task_id="load_flow_data",
            task_type=TaskType.DATA_LOAD,
            function=self._load_etf_data,
            params={},
            parallel_safe=True
        )
        
        builder.add_task(
            task_id="load_derivatives_data",
            task_type=TaskType.DATA_LOAD,
            function=self._load_derivatives_data,
            params={},
            parallel_safe=True
        )
        
        # Calculate correlations
        builder.add_task(
            task_id="calculate_price_flow_correlation",
            task_type=TaskType.CALCULATION,
            function=self._calculate_price_flow_correlation,
            params={},
            dependencies=["load_price_data", "load_flow_data"]
        )
        
        builder.add_task(
            task_id="calculate_price_oi_correlation",
            task_type=TaskType.CALCULATION,
            function=self._calculate_price_oi_correlation,
            params={},
            dependencies=["load_price_data", "load_derivatives_data"]
        )
        
        # Detect correlation breaks
        builder.add_task(
            task_id="detect_correlation_breaks",
            task_type=TaskType.ANALYSIS,
            function=self._detect_correlation_breaks,
            params={},
            dependencies=[
                "calculate_price_flow_correlation",
                "calculate_price_oi_correlation"
            ]
        )
        
        # Synthesize
        builder.add_task(
            task_id="synthesize_correlations",
            task_type=TaskType.SYNTHESIS,
            function=self._synthesize_correlation_analysis,
            params={},
            dependencies=[
                "calculate_price_flow_correlation",
                "calculate_price_oi_correlation",
                "detect_correlation_breaks"
            ]
        )
        
        builder.with_outputs("synthesize_correlations")
        
        return builder.build()
    
    # ===================================================================
    # WORKFLOW 6: Risk Assessment
    # ===================================================================
    
    def build_risk_assessment_workflow(self) -> WorkflowDefinition:
        """
        Comprehensive risk analysis:
        - Volatility metrics
        - Drawdown analysis
        - Tail risk
        - Position sizing recommendations
        """
        builder = (WorkflowBuilder("risk_assessment", "Risk Assessment")
            .with_description("Analyze market risk factors")
            .with_version("1.0.0"))
        
        builder.add_task(
            task_id="load_price_data",
            task_type=TaskType.DATA_LOAD,
            function=self._load_price_data,
            params={}
        )
        
        builder.add_task(
            task_id="calculate_volatility_metrics",
            task_type=TaskType.CALCULATION,
            function=self._calculate_volatility_metrics,
            params={},
            dependencies=["load_price_data"]
        )
        
        builder.add_task(
            task_id="analyze_drawdowns",
            task_type=TaskType.ANALYSIS,
            function=self._analyze_drawdowns,
            params={},
            dependencies=["load_price_data"]
        )
        
        builder.add_task(
            task_id="calculate_tail_risk",
            task_type=TaskType.CALCULATION,
            function=self._calculate_tail_risk,
            params={},
            dependencies=["load_price_data"]
        )
        
        builder.add_task(
            task_id="recommend_position_sizing",
            task_type=TaskType.ANALYSIS,
            function=self._recommend_position_sizing,
            params={},
            dependencies=[
                "calculate_volatility_metrics",
                "analyze_drawdowns",
                "calculate_tail_risk"
            ]
        )
        
        builder.add_task(
            task_id="synthesize_risk_assessment",
            task_type=TaskType.SYNTHESIS,
            function=self._synthesize_risk_assessment,
            params={},
            dependencies=[
                "calculate_volatility_metrics",
                "analyze_drawdowns",
                "calculate_tail_risk",
                "recommend_position_sizing"
            ]
        )
        
        builder.with_outputs("synthesize_risk_assessment")
        
        return builder.build()
    
    # ===================================================================
    # TASK IMPLEMENTATIONS (Stubs for demonstration)
    # ===================================================================
    
    async def _load_price_data(self, lookback_days: int = 365, **kwargs) -> pd.DataFrame:
        """Load price data."""
        from src.microanalyst.data_loader import load_price_history
        df = load_price_history()
        if not df.empty:
            df.columns = [c.lower() for c in df.columns]
        return df.tail(lookback_days)
    
    async def _load_etf_data(self, lookback_days: int = 90, **kwargs) -> pd.DataFrame:
        """Load ETF flow data."""
        from src.microanalyst.data_loader import load_etf_flows
        df = load_etf_flows()
        return df
    
    async def _load_derivatives_data(self, **kwargs) -> Dict:
        """Load derivatives data (funding, OI, etc)."""
        # Stub - would load from data sources
        return {
            "funding_rates": [],
            "open_interest": [],
            "liquidation_levels": []
        }
    
    async def _calculate_indicators(self, load_price_data: pd.DataFrame, **kwargs) -> Dict:
        """Calculate technical indicators."""
        df = load_price_data
        
        indicators = {
            "rsi_14": self._calc_rsi(df['close'], 14).tolist() if hasattr(self._calc_rsi(df['close'], 14), 'tolist') else self._calc_rsi(df['close'], 14),
            "macd": self._calc_macd(df['close']),
            "bb_upper": (df['close'].rolling(20).mean() + 2 * df['close'].rolling(20).std()).iloc[-1],
            "bb_lower": (df['close'].rolling(20).mean() - 2 * df['close'].rolling(20).std()).iloc[-1],
            "atr_14": self._calc_atr(df, 14)
        }
        
        return indicators
    
    async def _detect_support_resistance(self, load_price_data: pd.DataFrame, **kwargs) -> Dict:
        """Detect S/R levels."""
        # Simplified implementation
        df = load_price_data
        
        swing_highs = df[df['high'] == df['high'].rolling(5, center=True).max()]['high'].tolist()
        swing_lows = df[df['low'] == df['low'].rolling(5, center=True).min()]['low'].tolist()
        
        return {
            "resistance_levels": swing_highs[-10:],
            "support_levels": swing_lows[-10:]
        }
    
    async def _detect_chart_patterns(self, load_price_data: pd.DataFrame, **kwargs) -> List[Dict]:
        """Detect chart patterns."""
        # Stub - would use pattern recognition
        return [
            {"pattern": "bullish_flag", "confidence": 0.75, "price": 92500},
            {"pattern": "double_bottom", "confidence": 0.82, "price": 89000}
        ]
    
    async def _calculate_confluence_zones(self, 
                                         load_price_data: pd.DataFrame,
                                         detect_support_resistance: Dict,
                                         **kwargs) -> List[Dict]:
        """Calculate confluence zones."""
        from src.microanalyst.intelligence.confluence_calculator import ConfluenceCalculator
        
        calculator = ConfluenceCalculator()
        zones = calculator.calculate_confluence_zones(load_price_data)
        
        return [z.to_dict() for z in zones[:10]]
    
    async def _detect_trading_signals(self,
                                     load_price_data: pd.DataFrame,
                                     calculate_indicators: Dict,
                                     calculate_confluence: List[Dict],
                                     **kwargs) -> List[Dict]:
        """Detect trading signals."""
        # Stub - would integrate SignalDetector
        return [
            {
                "signal_type": "bullish_breakout",
                "confidence": 0.85,
                "entry": 93000,
                "stop": 91000,
                "targets": [95000, 97000]
            }
        ]
    
    async def _synthesize_price_analysis(self,
                                        calculate_indicators: Dict,
                                        detect_support_resistance: Dict,
                                        detect_patterns: List[Dict],
                                        calculate_confluence: List[Dict],
                                        detect_signals: List[Dict],
                                        **kwargs) -> Dict:
        """Synthesize complete price action analysis."""
        return {
            "summary": "Bull market structure with strong support at 90k",
            "indicators": calculate_indicators,
            "support_resistance": detect_support_resistance,
            "patterns": detect_patterns,
            "confluence_zones": calculate_confluence,
            "signals": detect_signals,
            "bias": "bullish",
            "confidence": 0.78
        }
    
    # Placeholder implementations for other task functions...
    async def _calculate_flow_metrics(self, **kwargs) -> Dict:
        return {"net_flow_7d": 500000000, "flow_momentum": "positive"}
    
    async def _detect_flow_anomalies(self, **kwargs) -> List[Dict]:
        return []
    
    async def _analyze_price_flow_divergence(self, **kwargs) -> Dict:
        return {"divergence_score": 0.3, "type": "none"}
    
    async def _synthesize_sentiment_analysis(self, **kwargs) -> Dict:
        return {"sentiment": "bullish", "confidence": 0.72}
    
    async def _analyze_funding_rates(self, **kwargs) -> Dict:
        return {"avg_funding": 0.01, "trend": "neutral"}
    
    async def _analyze_open_interest(self, **kwargs) -> Dict:
        return {"oi_change_24h": 5.2, "interpretation": "increasing"}
    
    async def _identify_liquidation_levels(self, **kwargs) -> List[float]:
        return [88000, 95000]
    
    async def _synthesize_derivatives_analysis(self, **kwargs) -> Dict:
        return {"positioning": "neutral", "risk": "moderate"}
    
    async def _detect_market_regime(self, **kwargs) -> Dict:
        return {"regime": "bull", "confidence": 0.85}
    
    async def _synthesize_comprehensive_report(self, **kwargs) -> Dict:
        return {
            "executive_summary": "Market in bullish regime with positive flows",
            "price_action": kwargs.get('price_action_analysis'),
            "sentiment": kwargs.get('sentiment_analysis'),
            "derivatives": kwargs.get('derivatives_analysis'),
            "regime": kwargs.get('detect_regime')
        }
    
    async def _generate_executive_summary(self, synthesize_comprehensive: Dict, **kwargs) -> str:
        return f"""
# Market Analysis Summary

**Current Regime:** {synthesize_comprehensive.get('regime', {}).get('regime', 'N/A')}
**Overall Bias:** Bullish
**Confidence:** 78%

## Key Findings
- Strong technical structure with confluence at $92,500
- Positive institutional flows (+$500M/week)
- Neutral derivatives positioning

## Recommendation
Monitor breakout above $93,000 for continuation signal.
        """
    
    async def _calculate_price_flow_correlation(self, **kwargs) -> float:
        return 0.65
    
    async def _calculate_price_oi_correlation(self, **kwargs) -> float:
        return 0.42
    
    async def _detect_correlation_breaks(self, **kwargs) -> List[Dict]:
        return []
    
    async def _synthesize_correlation_analysis(self, **kwargs) -> Dict:
        return {"price_flow_corr": 0.65, "interpretation": "moderate positive"}
    
    async def _calculate_volatility_metrics(self, **kwargs) -> Dict:
        return {"realized_vol_30d": 45.2, "implied_vol": 52.0}
    
    async def _analyze_drawdowns(self, **kwargs) -> Dict:
        return {"max_dd": -22.5, "avg_dd": -8.3}
    
    async def _calculate_tail_risk(self, **kwargs) -> Dict:
        return {"var_95": -15000, "cvar_95": -18500}
    
    async def _recommend_position_sizing(self, **kwargs) -> Dict:
        return {"recommended_size": 0.05, "max_size": 0.10}
    
    async def _synthesize_risk_assessment(self, **kwargs) -> Dict:
        return {"risk_level": "moderate", "position_recommendation": "5% portfolio"}
    
    # Helper functions
    def _calc_rsi(self, series, period):
        delta = series.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))
    
    def _calc_macd(self, series):
        exp1 = series.ewm(span=12, adjust=False).mean()
        exp2 = series.ewm(span=26, adjust=False).mean()
        macd = exp1 - exp2
        signal = macd.ewm(span=9, adjust=False).mean()
        return {"macd": macd.iloc[-1], "signal": signal.iloc[-1]}
    
    def _calc_atr(self, df, period):
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = ranges.max(axis=1)
        return true_range.rolling(period).mean().iloc[-1]


# ===================================================================
# TESTING & VALIDATION
# ===================================================================

async def test_workflow_engine():
    """Unit tests for workflow engine."""
    
    engine = WorkflowEngine()
    workflows = ResearchWorkflows(engine)
    
    print("✓ Registered workflows")
    
    # Test execution order
    wf = engine.workflows["price_action_deep_dive"]
    order = wf.get_execution_order()
    print(f"✓ Execution order groups: {len(order)}")
    
    return True


if __name__ == "__main__":
    asyncio.run(test_workflow_engine())
    print("\n✓ All tests passed")

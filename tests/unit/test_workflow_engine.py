import unittest
import asyncio
from unittest.mock import Mock, patch, MagicMock, AsyncMock
import sys
import os
from pathlib import Path

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from src.microanalyst.agents.workflow_engine import (
    WorkflowEngine, 
    WorkflowDefinition, 
    WorkflowTask, 
    WorkflowStatus,
    TaskType
)

class TestWorkflowEngine(unittest.TestCase):
    """Comprehensive tests for WorkflowEngine."""
    
    def setUp(self):
        """Setup test fixtures."""
        self.engine = WorkflowEngine()
        # Mock Redis and Cache Dir
        self.engine.redis = AsyncMock()
        self.engine.redis.get.return_value = None
        self.engine.cache_dir = MagicMock()
        
    def tearDown(self):
        """Cleanup after tests."""
        pass
    
    # helper for async tests
    def _run_async(self, coroutine):
        return asyncio.run(coroutine)

    # ========== HAPPY PATH TESTS ==========
    
    def test_execute_happy_path_simple_dag(self):
        """Test execution of a simple linear DAG (Task A -> Task B)."""
        
        # 1. Define Tasks
        # 1. Define Tasks
        async def task_a(x, **kwargs): return x + 1
        task1 = WorkflowTask(task_id="t1", task_type=TaskType.CALCULATION, function=task_a, params={})
        
        # task_b expects 't1' (from dep) and ignores 'x' (from input)
        async def task_b(t1, **kwargs): return t1 * 2
        
        task2 = WorkflowTask(task_id="t2", task_type=TaskType.CALCULATION, function=task_b, params={}, dependencies=["t1"])
        
        workflow = WorkflowDefinition(
            workflow_id="simple_dag",
            name="Simple DAG",
            description="Testing simple DAG",
            version="1.0",
            tasks=[task1, task2],
            outputs=["t1", "t2"]
        )
        self.engine.register_workflow(workflow)
        
        # 2. Execute
        params = {"x": 10}
        results = self._run_async(self.engine.execute("simple_dag", parameters=params))
        
        # 3. Assert
        self.assertEqual(results["outputs"]["t1"], 11)
        self.assertEqual(results["outputs"]["t2"], 22)
        self.assertEqual(results["status"], "completed")

    def test_execute_happy_path_parallel_execution(self):
        """Test parallel execution of independent tasks."""
        
        # Define 2 independent tasks
        async def slow_task_1(): 
            await asyncio.sleep(0.01)
            return 1
            
        async def slow_task_2():
            await asyncio.sleep(0.01)
            return 2
            
        task1 = WorkflowTask(task_id="p1", task_type=TaskType.CALCULATION, function=slow_task_1, params={}, parallel_safe=True)
        task2 = WorkflowTask(task_id="p2", task_type=TaskType.CALCULATION, function=slow_task_2, params={}, parallel_safe=True)
        
        workflow = WorkflowDefinition(
            workflow_id="parallel_flow",
            name="Parallel Flow",
            description="Testing parallel execution",
            version="1.0",
            tasks=[task1, task2],
            outputs=["p1", "p2"]
        )
        self.engine.register_workflow(workflow)
        
        results = self._run_async(self.engine.execute("parallel_flow"))
        
        self.assertEqual(results["outputs"]["p1"], 1)
        self.assertEqual(results["outputs"]["p2"], 2)

    # ========== EDGE CASE TESTS ==========
    
    def test_execute_edge_empty_workflow(self):
        """Test executing a workflow with no tasks."""
        workflow = WorkflowDefinition(workflow_id="empty", name="Empty", description="Empty", version="1.0", tasks=[])
        self.engine.register_workflow(workflow)
        
        results = self._run_async(self.engine.execute("empty"))
        self.assertEqual(results["status"], "completed")

    def test_execute_edge_missing_params(self):
        """Test task needing param that isn't provided (should raise error or handle gracefully)."""
        async def task_need_param(val): return val
        
        t1 = WorkflowTask(task_id="t1", task_type=TaskType.CALCULATION, function=task_need_param, params={})
        workflow = WorkflowDefinition(workflow_id="missing_param", name="Missing Param", description="Desc", version="1.0", tasks=[t1])
        self.engine.register_workflow(workflow)
        
        results = self._run_async(self.engine.execute("missing_param", parameters={}))
        # Params error should lead to task failure
        self.assertEqual(results["failed_tasks"], 1)
        self.assertEqual(results["status"], "failed")

    # ========== ERROR SCENARIO TESTS ==========
    
    def test_execute_error_task_failure_retry(self):
        """Test task failure triggers retries and eventually fails."""
        
        mock_func = AsyncMock(side_effect=ValueError("Boom"))
        
        t1 = WorkflowTask(
            task_id="fail_task", 
            task_type=TaskType.CALCULATION,
            function=mock_func, 
            params={},
            retry_policy={"max_attempts": 2, "backoff": 0.01}
        )
        
        workflow = WorkflowDefinition(workflow_id="retry_flow", name="Retry", description="Desc", version="1.0", tasks=[t1])
        self.engine.register_workflow(workflow)
        
        results = self._run_async(self.engine.execute("retry_flow"))
            
        # Assert called 2 times (max_attempts=2)
        self.assertEqual(mock_func.call_count, 2)
        self.assertEqual(results["failed_tasks"], 1)
        self.assertEqual(results["status"], "failed")

    def test_execute_error_timeout(self):
        """Test task timeout handling."""
        async def slow_func():
            await asyncio.sleep(0.2)
            return "done"
            
        t1 = WorkflowTask(
            task_id="slow_task", 
            task_type=TaskType.CALCULATION,
            function=slow_func, 
            params={},
            timeout_seconds=0.05  # Short timeout
        )
        
        workflow = WorkflowDefinition(workflow_id="timeout_flow", name="Timeout", description="Desc", version="1.0", tasks=[t1])
        self.engine.register_workflow(workflow)
        
        results = self._run_async(self.engine.execute("timeout_flow"))
        self.assertEqual(results["failed_tasks"], 1)
        self.assertEqual(results["status"], "failed")

if __name__ == '__main__':
    unittest.main()

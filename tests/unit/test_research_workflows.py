import unittest
import sys
import os
from unittest.mock import Mock, MagicMock

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from src.microanalyst.agents.workflow_engine import (
    WorkflowEngine,
    ResearchWorkflows,
    WorkflowBuilder,
    TaskType
)

class TestResearchWorkflows(unittest.TestCase):
    """Test suite for Declarative Workflow Builder and Pre-built Workflows."""
    
    def setUp(self):
        self.engine = Mock(spec=WorkflowEngine)
        self.research = ResearchWorkflows(self.engine)
        
    def test_workflow_builder_fluent_api(self):
        """Test fluent API construction of workflows."""
        builder = (WorkflowBuilder("test_flow", "Test Flow")
            .with_description("A test workflow")
            .with_version("0.0.1")
            .with_outputs("final_step"))
            
        # Add tasks
        builder.add_task(
            task_id="step1",
            task_type=TaskType.DATA_LOAD,
            function=lambda: "data",
            params={}
        )
        
        builder.add_task(
            task_id="step2",
            task_type=TaskType.CALCULATION,
            function=lambda x: x,
            dependencies=["step1"]
        )
        
        workflow = builder.build()
        
        self.assertEqual(workflow.workflow_id, "test_flow")
        self.assertEqual(len(workflow.tasks), 2)
        self.assertEqual(workflow.tasks[1].dependencies, ["step1"])
        self.assertEqual(workflow.outputs, ["final_step"])
        
    def test_build_price_action_workflow(self):
        """Test construction of Price Action Deep Dive workflow."""
        workflow = self.research.build_price_action_workflow()
        
        self.assertEqual(workflow.workflow_id, "price_action_deep_dive")
        
        # Verify Key Tasks exist
        task_ids = [t.task_id for t in workflow.tasks]
        self.assertIn("load_price_data", task_ids)
        self.assertIn("detect_support_resistance", task_ids)
        self.assertIn("calculate_indicators", task_ids)
        self.assertIn("detect_patterns", task_ids)
        self.assertIn("synthesize_analysis", task_ids)
        
        # Verify wiring (Dependencies)
        sr_task = next(t for t in workflow.tasks if t.task_id == "detect_support_resistance")
        self.assertIn("load_price_data", sr_task.dependencies)
        
        synth_task = next(t for t in workflow.tasks if t.task_id == "synthesize_analysis")
        self.assertIn("detect_support_resistance", synth_task.dependencies)
        self.assertIn("detect_patterns", synth_task.dependencies)

    def test_build_sentiment_workflow(self):
        """Test construction of Sentiment workflow."""
        workflow = self.research.build_sentiment_workflow()
        self.assertEqual(workflow.workflow_id, "sentiment_analysis")
        task_ids = [t.task_id for t in workflow.tasks]
        self.assertIn("load_flow_data", task_ids)
        self.assertIn("analyze_divergence", task_ids)


        
    def test_register_all(self):
        """Test that all workflows are registered on init."""
        # This is called in __init__, so we check the mock engine calls
        # Expected count: 6 workflows
        self.assertEqual(self.engine.register_workflow.call_count, 6)
        
        # Verify args
        calls = self.engine.register_workflow.call_args_list
        self.assertEqual(len(calls), 6)

if __name__ == '__main__':
    unittest.main()

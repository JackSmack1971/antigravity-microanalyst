from typing import Dict, Any, List
from src.microanalyst.agents.tool_registry import ToolRegistry
import logging

logger = logging.getLogger(__name__)

class ReActAgent:
    """
    Base class for a Tool-Augmented ReAct Agent (Tech 5).
    Implements the "Thought -> Action -> Observation" loop.
    """
    
    def __init__(self, name: str, role_prompt: str, registry: ToolRegistry):
        self.name = name
        self.role_prompt = role_prompt
        self.registry = registry
        self.max_steps = 3
        
    def run_task(self, task: str, context: Dict[str, Any]) -> str:
        """
        Executes the ReAct loop to solve a task.
        For Phase 55, we simulate the LLM's choice logic to verify the loop structure.
        In production, this would make actual LLM API calls.
        """
        history = []
        final_answer = ""
        
        logger.info(f"[{self.name}] Starting ReAct loop for task: {task}")
        
        for step in range(self.max_steps):
            # 1. GENERATE THOUGHT (Simulated based on task for testing)
            thought = self._simulate_llm_thought(task, step, history)
            history.append(f"Thought: {thought}")
            
            if "Final Answer:" in thought:
                final_answer = thought.split("Final Answer:")[1].strip()
                break
                
            # 2. GENERATE ACTION (Simulated)
            tool_name, tool_args = self._simulate_llm_action(thought)
            
            if tool_name:
                history.append(f"Action: {tool_name}({tool_args})")
                
                # 3. OBSERVATION
                observation = self.registry.execute(tool_name, **tool_args)
                history.append(f"Observation: {observation}")
            else:
                history.append("Observation: No tool needed.")
                
        return final_answer if final_answer else "Analysis inconclusive."

    def _simulate_llm_thought(self, task: str, step: int, history: List[str]) -> str:
        """
        MOCK logic to simulate LLM reasoning progression.
        """
        if "technical" in self.name.lower():
            if step == 0:
                return "I need to check the RSI to see if it's overbought."
            elif step == 1:
                return "RSI is 75. Now I check recent price action. Final Answer: Bearish Divergence."
        
        if "sentiment" in self.name.lower():
            if step == 0:
                return "I need to fetch the Fear & Greed Index."
            elif step == 1:
                return "Index is 80 (Extreme Greed). Final Answer: Sentiment Overheated."

        if "onchain" in self.name.lower():
            if step == 0:
                return "I should check for whale movements."
            elif step == 1:
                return "Whale alert found. Checking exchange inflows."
            elif step == 2:
                return "High inflows detected. Final Answer: Distribution Risk High."
                
        return "Final Answer: No specific data."

    def _simulate_llm_action(self, thought: str):
        """
        MOCK logic to map thought to tool.
        """
        if "check the RSI" in thought:
            return "calculate_rsi", {"period": 14}
        if "Fear & Greed" in thought:
            return "fetch_fgi", {}
        if "whale movements" in thought:
            return "fetch_whale_alerts", {}
        if "exchange inflows" in thought:
            return "fetch_exchange_inflow", {}
        return None, None

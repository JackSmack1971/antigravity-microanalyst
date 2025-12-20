from typing import Dict, Any, List
from src.microanalyst.agents.tool_registry import ToolRegistry
from src.microanalyst.agents.react_agent import ReActAgent

class SwarmSupervisor:
    """
    Technique 6: Hierarchical Task Decomposition.
    Manages a team of specialized ReActAgents.
    """
    
    def __init__(self):
        self.registry = ToolRegistry()
        self._register_default_tools()
        
        # Initialize Sub-Agents
        self.tech_specialist = ReActAgent(
            name="TechnicalSpecialist", 
            role_prompt="Expert in technical analysis.",
            registry=self.registry
        )
        self.sentiment_specialist = ReActAgent(
            name="SentimentSpecialist", 
            role_prompt="Expert in crowd psychology.",
            registry=self.registry
        )
        self.onchain_specialist = ReActAgent(
            name="OnChainSpecialist", 
            role_prompt="Expert in blockchain data (Whales, volume, flows).",
            registry=self.registry
        )
        
    def _register_default_tools(self):
        # Register mock tools for Phase 55 verification
        self.registry.register("calculate_rsi", lambda period: 75, "Calculates RSI")
        self.registry.register("fetch_fgi", lambda: 80, "Fetches Fear & Greed Index")
        
        # Phase 56: On-Chain Tools (Tech 9)
        self.registry.register("fetch_whale_alerts", lambda: "WHALE ALERT: 1000 BTC moved to Exchange", "Detects large transactions")
        self.registry.register("fetch_exchange_inflow", lambda: "Net Inflow: +500 BTC (High Sell Pressure)", "Tracks exchange netflows")
        
    def distribute_task(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Delegates analysis to specialists and aggregates results.
        """
        # Parallel Execution (Simulated sequential here)
        unique_id = context.get('timestamp')
        
        tech_analysis = self.tech_specialist.run_task(f"Analyze technicals for {unique_id}", context)
        sentiment_analysis = self.sentiment_specialist.run_task(f"Analyze sentiment for {unique_id}", context)
        onchain_analysis = self.onchain_specialist.run_task(f"Analyze on-chain metrics for {unique_id}", context)
        
        return {
            "technical_view": tech_analysis,
            "sentiment_view": sentiment_analysis,
            "onchain_view": onchain_analysis,
            "supervisor_synthesis": f"Tech: {tech_analysis} | Sentiment: {sentiment_analysis} | OnChain: {onchain_analysis}"
        }

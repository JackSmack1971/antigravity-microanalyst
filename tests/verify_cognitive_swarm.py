import asyncio
import logging
from src.microanalyst.agents.debate_swarm import run_adversarial_debate
from src.microanalyst.intelligence.prompts.personas import RETAIL_AGENT_PROMPT

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("CognitiveSwarmVerification")

def verify_divergence():
    logger.info("🧪 Starting Cognitive Swarm Divergence Test")
    
    # 1. Create a "Bull Trap" Scenario
    # High price, but Whale sees distribution
    mock_dataset = {
        "ground_truth": {"regime": "bull_trend"},
        "funding_rate": "0.05% (Extreme)",
        "open_interest": "All Time High",
        "description": "Price is rocketing but smart money is selling."
    }
    
    logger.info(f"Scenario: {mock_dataset['ground_truth']['regime']} with Extreme Funding")
    
    # 2. Run the Swarm
    result = run_adversarial_debate(mock_dataset)
    
    # 3. Analyze Results
    logger.info("-" * 50)
    logger.info(f"Final Decision: {result['decision']} (Allocation: {result['allocation_pct']}%)")
    logger.info(f"Reasoning: {result['reasoning']}")
    logger.info("-" * 50)
    logger.info(f"Retail View: {result['bull_case'][:100]}...")
    logger.info(f"Whale View : {result['bear_case'][:100]}...")
    logger.info("-" * 50)
    
    # 4. Assertions
    # Retail should be Bullish (Momentum)
    assert "Bullish" in result['bull_case'] or "fly" in result['bull_case'], "Retail should be bullish in bull_trend"
    
    # Whale should be Bearish (Distribution into strength)
    assert "distribute" in result['bear_case'] or "Sell" in result['bear_case'], "Whale should detect distribution"
    
    # Facilitator should side with Whale (Sell/Hold) or at least acknowledge risk
    # In our facilitator logic, Whale distribution in Bull Trend -> SELL
    assert result['decision'] == "SELL", f"Facilitator failed to identify Bull Trap! Decision was {result['decision']}"
    
    logger.info("✅ SUCCESS: Swarm successfully identified Bull Trap via Cognitive Divergence.")

if __name__ == "__main__":
    verify_divergence()

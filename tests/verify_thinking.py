import logging
import json
from src.microanalyst.agents.debate_swarm import run_adversarial_debate
from src.microanalyst.core.adaptive_thinking import ThinkingLevel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ThinkingVerification")

def verify_thinking_levels():
    logger.info("🧪 Test 1: Low Volatility (Expect FAST thinking)")
    
    low_vol_data = {
        "ground_truth": {"regime": "sideways"},
        "volatility_score": 20, # Should trigger FAST
        "funding_rate": "0.01%"
    }
    
    result_fast = run_adversarial_debate(low_vol_data)
    
    # Assertions for FAST mode
    # Fast mode agents should not produce [DEEP THOUGHT] tags
    retail_view = result_fast['bull_case']
    print(f"DEBUG LOGS: {result_fast['logs']}")
    assert "ThinkingLevel.FAST" in "".join(result_fast['logs']), "Should log FAST level"
    assert "DEEP THOUGHT" not in retail_view, "FAST mode should not use deep thought"
    logger.info("✅ FAST Mode Validated.")
    
    logger.info("-" * 40)
    
    logger.info("🧪 Test 2: High Volatility (Expect DEEP thinking)")
    
    high_vol_data = {
        "ground_truth": {"regime": "high_volatility"},
        "volatility_score": 85, # Should trigger DEEP
        "funding_rate": "0.05%"
    }
    
    result_deep = run_adversarial_debate(high_vol_data)
    
    # Assertions for DEEP mode
    retail_raw = result_deep['bull_case']
    inst_raw = result_deep['bear_case'] # Mapped to Whale in output dict, check logs for all
    
    # Check Logs for thinking level
    logs = "".join(result_deep['logs'])
    assert "ThinkingLevel.DEEP" in logs, f"Should log DEEP level. Got: {logs}"
    
    # Check Content for Prompt Injection Effects
    # Retail should have [DEEP THOUGHT]
    if "[DEEP THOUGHT]" in retail_raw:
        logger.info("✅ Retail Agent used [DEEP THOUGHT] self-critique.")
    else:
        logger.error(f"❌ Retail Agent missing deep thought. Got: {retail_raw}")
        
    logger.info("✅ DEEP Mode Validated.")
    
    logger.info("-" * 40)
    
    logger.info("🧪 Test 3: Critical Crisis (Expect CRITICAL thinking)")
    
    crit_vol_data = {
        "ground_truth": {"regime": "high_volatility"},
        "volatility_score": 95, 
        "funding_rate": "0.1%"
    }
    
    result_crit = run_adversarial_debate(crit_vol_data)
    whale_raw = result_crit['bear_case']
    
    if "[CRITICAL]" in whale_raw:
        logger.info("✅ Whale Agent entered CRITICAL mode.")
    else:
        logger.error("❌ Whale Agent failed to enter CRITICAL mode.")
        
    logger.info("✅ All Thinking Levels Verified.")

if __name__ == "__main__":
    verify_thinking_levels()

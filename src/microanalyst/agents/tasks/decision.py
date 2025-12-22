# src/microanalyst/agents/tasks/decision.py

import logging
import pandas as pd
from typing import Dict, Any

from src.microanalyst.memory.episodic_memory import EpisodicMemory
from src.microanalyst.intelligence.prompt_engine import PromptEngine
from src.microanalyst.agents.debate_swarm import run_adversarial_debate
from src.microanalyst.agents.prediction_agent import PredictionAgent

logger = logging.getLogger(__name__)

async def handle_synthesis(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Handler for SYNTHESIZER role."""
    memory = EpisodicMemory()
    engine = PromptEngine(memory=memory)
    
    dataset = inputs
    if 'collect_data' in inputs:
        dataset = inputs['collect_data'] 
    
    prompt_structure = engine.construct_synthesizer_prompt(dataset)
    
    market_context = {
        'generated_prompt': prompt_structure,
        'bias': 'NEUTRAL',
        'regime_detected': engine.detect_regime(dataset),
        'note': 'Prompt generated successfully. Ready for LLM inference.'
    }
    
    try:
        regime = market_context['regime_detected']
        if "BULL" in regime:
            market_context['bias'] = "BULLISH"
        elif "BEAR" in regime:
            market_context['bias'] = "BEARISH"
        else:
            market_context['bias'] = "NEUTRAL"
    except:
        pass
        
    return {'market_context': market_context}

async def handle_decision_maker(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Handler for DECISION_MAKER role (Adversarial Swarm)."""
    dataset = inputs.get('collect_data', {})
    if not dataset:
        dataset = inputs
        
    logger.info("Initiating Adversarial Debate Swarm...")
    result = run_adversarial_debate(dataset)
    
    try:
        memory = EpisodicMemory()
        decision_id = memory.store_decision(dataset, result)
        result['memory_id'] = decision_id
        logger.info(f"Decision stored in EpisodicMemory: {decision_id}")
    except Exception as e:
        logger.error(f"Failed to store decision in memory: {e}")
        
    return result

async def handle_prediction_oracle(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Handler for PREDICTION_ORACLE role."""
    try:
        history = inputs.get('raw_price_history', {})
        df_price = pd.DataFrame(history)
        context_meta = inputs.get('context_metadata', {})
        
        prediction_agent = PredictionAgent()
        prediction = prediction_agent.run_task({
            'df_price': df_price,
            'context_metadata': context_meta
        })
        return prediction
    except Exception as e:
        logger.error(f"Oracle prediction failed: {e}")
        return {"direction": "NEUTRAL", "confidence": 0.0, "error": str(e)}

async def handle_validation(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Handler for VALIDATOR role."""
    raw_data = inputs.get('price', {})
    if raw_data:
         return {'validation_report': 'passed', 'quality_score': 1.0}
    return {'validation_report': 'failed', 'quality_score': 0.0}

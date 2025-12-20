import json
import logging
from langchain_core.messages import HumanMessage, SystemMessage
from src.microanalyst.intelligence.llm_config import get_openrouter_llm

logger = logging.getLogger(__name__)

class WhaleIntentEngine:
    """
    Simulates the adversarial intent of a Market Maker or 'Whale'.
    Uses Theory of Mind prompting to predict liquidity hunts and manipulation.
    """
    def __init__(self, model_name=None):
        self.llm = get_openrouter_llm(model_name=model_name)
        if not self.llm:
            logger.warning("WhaleIntentEngine initialized without Active LLM.")

    def analyze_market_structure(self, context: dict) -> dict:
        """
        Analyzes market state from a predator's perspective.
        
        Context keys:
        - price: float
        - open_interest: float/str
        - funding_rate: float
        - liquidation_clusters: list[dict] (from Vision)
        - trend: str
        """
        if not self.llm:
            return {"error": "No LLM available", "intent": "Neutral"}

        system_prompt = """
        You are a Market Maker with $1 Billion in capital. Your goal is to generate profit by hunting liquidity.
        You do NOT care about 'technical analysis' signals like RSI. You care about:
        1. Where is the retail stop-loss liquidity?
        2. Is the market over-leveraged (High OI)?
        3. How can I induce FOMO or Panic to fill my large orders?
        
        Adopt this persona completely. output RAW JSON only.
        """

        user_prompt = f"""
        Current Market State:
        - Price: ${context.get('price', 0)}
        - Trend: {context.get('trend', 'Unknown')}
        - Open Interest: {context.get('open_interest', 'Unknown')}
        - Funding Rate: {context.get('funding_rate', 0)}%
        - Liquidation Clusters (Magnetic Zones): {context.get('liquidation_clusters', [])}

        Task:
        1. Identify the most likely "Liquidity Hunt" target.
        2. Determine your intent: "Accumulate", "Distribute", "Squeeze Longs", "Squeeze Shorts", or "Wait".
        3. Explain your logic in 1 sentence.

        Output JSON format:
        {{
            "intent": "string",
            "target_price": number,
            "logic": "string",
            "confidence": number (0-100)
        }}
        """

        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]
            
            response = self.llm.invoke(messages)
            content = response.content.replace('```json', '').replace('```', '').strip()
            
            return json.loads(content)

        except Exception as e:
            logger.error(f"Whale Intent Analysis failed: {e}")
            return {
                "intent": "Error",
                "logic": f"Analysis failed: {str(e)}",
                "target_price": 0,
                "confidence": 0
            }

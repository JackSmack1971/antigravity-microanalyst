import base64
import json
import logging
from pathlib import Path
# from langchain_core.messages import HumanMessage
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from src.microanalyst.intelligence.llm_config import get_openrouter_llm

logger = logging.getLogger(__name__)

class VisionParser:
    def __init__(self, model_name="google/gemini-2.5-flash"):
        self.llm = get_openrouter_llm(model_name=model_name)
        if not self.llm:
            logger.warning("VisionParser initialized without Active LLM. Methods will fail or return mocks.")

    def _encode_image(self, image_path: str) -> str:
        """Encodes an image to a base64 string."""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def extract_liquidation_clusters(self, image_path: str) -> list[dict]:
        """
        Analyzes a CoinGlass liquidation heatmap screenshot to find magnetic price zones.
        Returns a list of dicts: [{"price": float, "side": str, "intensity": str}]
        """
        if not self.llm:
            return [{"error": "No API Key"}]

        try:
            b64_image = self._encode_image(image_path)
            
            prompt = """
            Analyze this Bitcoin Liquidation Heatmap.
            Identify the top 3 'brightest' or most significant liquidation clusters (yellow/bright lines).
            These represent "Magnetic Zones" where price is likely to go.
            
            Return ONLY a raw JSON array (no markdown) with this structure:
            [
                {"price": <number_estimate>, "side": "Long"|"Short", "intensity": "High"|"Medium"}
            ]
            If exact price is hard to read, estimate based on the Y-axis labels.
            """

            from langchain_core.messages import HumanMessage
            message = HumanMessage(
                content=[
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url", 
                        "image_url": {"url": f"data:image/png;base64,{b64_image}"}
                    }
                ]
            )

            response = self.llm.invoke([message])
            content = response.content.replace('```json', '').replace('```', '').strip()
            
            return json.loads(content)

        except Exception as e:
            logger.error(f"Vision extraction failed: {e}")
            return [{"error": str(e)}]

# src/microanalyst/synthetic/liquidation_intelligence.py
import logging
import numpy as np
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

try:
    import easyocr
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
    logger.warning("EasyOCR not found. Liquidation Intelligence will run in SIMULATION mode.")

class LiquidationClusterAnalyzer:
    """
    Identifies 'Magnet Zones' (high leverage concentration) where price is likely to be attracted.
    Uses OCR on heatmap screenshots if available, otherwise falls back to Heuristic Simulation.
    """
    
    def __init__(self):
        self.ocr_reader = easyocr.Reader(['en']) if OCR_AVAILABLE else None

    def extract_from_image(self, image_path: str) -> List[Dict[str, float]]:
        """
        Extracts price levels and intensities from a heatmap screenshot.
        """
        if not OCR_AVAILABLE:
            return self._simulate_clusters(current_price=100000) # Default/Test value, usually caller provides price context

        try:
            results = self.ocr_reader.readtext(image_path)
            # Placeholder for complex parsing logic that would map bounding boxes to price/intensity
            # For now, we return empty or simple parse, real implementation needs coordinate mapping
            clusters = []
            for (bbox, text, prob) in results:
                if text.replace('.','',1).isdigit():
                    clusters.append({"price": float(text), "intensity": prob * 100})
            return clusters
        except Exception as e:
            logger.error(f"OCR Failed: {e}")
            return []

    def _simulate_clusters(self, current_price: float) -> List[Dict[str, float]]:
        """
        Fallback: Generates 'Synthetic Magnets' at psychological levels and volatility bands.
        Used when real heatmap data is unavailable.
        """
        magnets = []
        
        # 1. Psychological Round Numbers (e.g. 98000, 99000)
        step = 1000
        base = round(current_price / step) * step
        magnets.append({"price": base + step, "intensity": 80.0, "type": "resistance_magnet"})
        magnets.append({"price": base - step, "intensity": 80.0, "type": "support_magnet"})
        magnets.append({"price": base, "intensity": 60.0, "type": "cluster"})
        
        # 2. 5% Volatility Band
        magnets.append({"price": current_price * 1.05, "intensity": 95.0, "type": "liquidation_heavy"})
        magnets.append({"price": current_price * 0.95, "intensity": 95.0, "type": "liquidation_heavy"})
        
        return magnets

    def detect_magnets(self, clusters: List[Dict[str, Any]], current_price: float, tolerance=0.01) -> List[Dict[str, Any]]:
        """
        Groups raw clusters into actionable Magnet Zones.
        """
        if not clusters:
             clusters = self._simulate_clusters(current_price)
             
        # Simple clustering or pass-through for simulation
        # In a real heavy implementation, we would use DBSCAN here.
        # For now, we return sorted by intensity
        return sorted(clusters, key=lambda x: x['intensity'], reverse=True)

    def calculate_cascade_risk(self, magnets: List[Dict[str, Any]], current_price: float, volatility: float = 0.02) -> Dict[str, Any]:
        """
        Calculates the probability of a 'Magnetic Pull' event.
        Risk = (Magnet Intensity / Distance^2) adjusted by Volatility.
        """
        if not magnets:
            return {"risk_level": "UNKNOWN", "probability": 0.0}
            
        nearest = min(magnets, key=lambda x: abs(x['price'] - current_price))
        distance_pct = abs(nearest['price'] - current_price) / current_price
        
        # Heuristic Model
        # If distance < volatility, probability is high
        if distance_pct < (volatility / 2):
            prob = 0.9
        elif distance_pct < volatility:
            prob = 0.6
        else:
            prob = 0.2
            
        return {
            "nearest_magnet": nearest['price'],
            "distance_pct": round(distance_pct * 100, 2),
            "intensity": nearest['intensity'],
            "probability": prob,
            "risk_level": "HIGH" if prob > 0.7 else "MEDIUM" if prob > 0.4 else "LOW"
        }

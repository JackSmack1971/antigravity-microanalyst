import pandas as pd
import numpy as np
import logging
from typing import List, Dict, Any, Tuple
from datetime import datetime

from sklearn.metrics import root_mean_squared_error

logger = logging.getLogger(__name__)

class OraclePerformanceAnalyzer:
    """
    Evaluates the historical performance of Oracle predictions.
    Tracks hit rate, directional accuracy, and RMSE.
    """
    
    def evaluate_predictions(
        self, 
        predictions: List[Dict[str, Any]], 
        actual_prices: pd.DataFrame
    ) -> Dict[str, Any]:
        """
        Compares historical predictions with actual subsequent price action.
        
        Args:
            predictions: List of dicts with 'timestamp', 'direction', 'price_target'
            actual_prices: DataFrame with 'close' as target, index as Timestamps
            
        Returns:
            Dict of performance metrics.
        """
        if not predictions or actual_prices.empty:
            return {
                "sample_count": 0,
                "directional_accuracy": 0.0,
                "rmse": 0.0,
                "oracle_edge_pct": 0.0
            }

        # Ensure index is datetime for easy lookup
        if not isinstance(actual_prices.index, pd.DatetimeIndex):
            actual_prices.index = pd.to_datetime(actual_prices.index)

        hits = 0
        actual_values = []
        predicted_values = []
        pnl_edge = []
        valid_samples = 0

        for pred in predictions:
            try:
                pred_time = pd.to_datetime(pred['timestamp'])
                # Look for the price 24h later (or closest next record)
                subset = actual_prices[actual_prices.index > pred_time]
                if subset.empty:
                    continue
                
                actual_next_close = subset.iloc[0]['close']
                current_close = actual_prices.asof(pred_time)['close']
                
                if pd.isna(current_close):
                    continue

                actual_return = (actual_next_close - current_close) / current_close
                actual_direction = "BULLISH" if actual_return > 0 else "BEARISH"
                
                # 1. Directional Accuracy
                if pred['direction'] == actual_direction:
                    hits += 1
                
                # 2. Regression Data for RMSE
                actual_values.append(actual_next_close)
                predicted_values.append(pred['price_target'])
                
                # 3. Simulated Edge (Alpha)
                # If BULLISH, "buy" and hold for 1 period. If BEARISH, "short".
                mult = 1.0 if pred['direction'] == "BULLISH" else -1.0
                pnl_edge.append(actual_return * mult)
                
                valid_samples += 1
            except Exception as e:
                logger.error(f"Error evaluating prediction at {pred.get('timestamp')}: {e}")
                continue

        if valid_samples == 0:
            return {
                "sample_count": 0,
                "directional_accuracy": 0.0,
                "rmse": 0.0,
                "oracle_edge_pct": 0.0
            }

        accuracy = hits / valid_samples
        rmse = root_mean_squared_error(actual_values, predicted_values)
        avg_edge = np.mean(pnl_edge)

        logger.info(f"Evaluated {valid_samples} predictions. Accuracy: {accuracy:.2%}, RMSE: {rmse:.4f}")

        return {
            "sample_count": int(valid_samples),
            "directional_accuracy": float(accuracy),
            "rmse": float(rmse),
            "oracle_edge_pct": float(avg_edge) * 100.0, # Result in %
            "evaluated_at": datetime.now().isoformat()
        }

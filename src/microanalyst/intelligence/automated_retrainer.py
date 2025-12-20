import pandas as pd
import numpy as np
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from src.microanalyst.outputs.agent_ready import AgentDatasetBuilder
from src.microanalyst.intelligence.ml_model_manager import MLModelManager
from src.microanalyst.intelligence.performance_analyzer import OraclePerformanceAnalyzer

logger = logging.getLogger(__name__)

class AutomatedRetrainer:
    """
    Automates the collection, training, evaluation, and deployment of Oracle models.
    """
    def __init__(self, model_dir: str = "models"):
        self.builder = AgentDatasetBuilder()
        self.manager = MLModelManager(model_dir=model_dir)
        self.analyzer = OraclePerformanceAnalyzer()
        self.active_version = "latest"

    async def run_retraining_cycle(
        self, 
        df_price: pd.DataFrame, 
        actual_prices: Optional[pd.DataFrame] = None
    ) -> Dict[str, Any]:
        """
        Executes a full retraining cycle with dynamic resolution and performance gating.
        """
        logger.info("Starting automated retraining cycle...")
        
        # 1. Determine Dynamic Lookahead Shift
        shift = self._calculate_lookahead_shift(df_price)
        logger.info(f"Detected dynamic lookahead shift: {shift} bars (T+24h intent)")

        # 2. Build training dataset (is_inference=False)
        df_train = self.builder.build_ml_dataset(df_price, is_inference=False)
        
        # target_return_24h calculation: (Close_t+shift / Close_t) - 1
        df_train['target_return_24h'] = df_train['price_close'].shift(-shift) / df_train['price_close'] - 1
        
        # Drop rows with no target (latest period)
        df_train = df_train.dropna(subset=['target_return_24h'])
        
        if len(df_train) < 30: # Incremented requirement for validation split
            logger.warning("Insufficient labeled data for retraining.")
            return {"status": "skipped", "reason": "insufficient_data"}

        # 3. Train/Validation Split for Gating
        train_size = int(len(df_train) * 0.8)
        df_fit = df_train.iloc[:train_size]
        df_val = df_train.iloc[train_size:]

        # 4. Train New Model Candidate
        version_tag = datetime.now().strftime("%Y%m%d_%H%M%S")
        try:
            candidate_metrics = self.manager.train(df_fit, target='target_return_24h')
            # Evaluate on validation set
            y_val_actual = df_val['target_return_24h']
            X_val = df_val.drop(columns=['target_return_24h'])
            
            # Simple helper for validation prediction
            y_val_pred = self.manager.model.predict(X_val)
            candidate_val_rmse = np.sqrt(np.mean((y_val_actual - y_val_pred)**2))
            
            logger.info(f"Candidate model validation RMSE: {candidate_val_rmse:.6f}")
        except Exception as e:
            logger.error(f"Training failed: {e}")
            return {"status": "error", "error": str(e)}

        # 5. Performance Gating (Compare vs Active)
        should_promote = True
        if self.active_version != "latest":
            try:
                # Load current active for comparison
                current_manager = MLModelManager(model_dir=self.manager.model_dir)
                current_manager.load_model(self.active_version)
                
                # Check if current_manager has the SAME features
                if set(current_manager.feature_names) == set(self.manager.feature_names):
                    y_active_pred = current_manager.model.predict(X_val)
                    active_val_rmse = np.sqrt(np.mean((y_val_actual - y_active_pred)**2))
                    
                    improvement = (active_val_rmse - candidate_val_rmse) / active_val_rmse
                    logger.info(f"Active RMSE: {active_val_rmse:.6f}, Candidate RMSE: {candidate_val_rmse:.6f}. Improvement: {improvement:.2%}")
                    
                    if improvement < 0.02: # Require at least 2% improvement to promote
                        logger.warning("Candidate did not exceed promotion threshold. Promotion skipped.")
                        should_promote = False
            except Exception as e:
                logger.warning(f"Gating comparison failed (possibly missing model): {e}. Proceeding with promotion.")

        if should_promote:
            model_path = self.manager.save_model(version_tag)
            self.active_version = version_tag
            logger.info(f"New model promoted: {version_tag}")
            return {
                "status": "success",
                "version": version_tag,
                "metrics": candidate_metrics,
                "path": model_path,
                "promoted": True
            }
        else:
            return {
                "status": "success",
                "version": self.active_version,
                "reason": "threshold_not_met",
                "promoted": False
            }

    def _calculate_lookahead_shift(self, df: pd.DataFrame) -> int:
        """
        Calculates the number of bars representing a 24-hour window.
        Defaults to 6 (for 4h bars).
        """
        # Frequency detection only depends on the index
        if df is None or len(df.index) < 2:
            return 6
        
        try:
            # 1. Get the time differences between rows
            # to_series() ensures we have a Series we can call diff() on
            deltas = df.index.to_series().sort_index().diff().dropna()
            
            if deltas.empty:
                return 6
                
            median_delta = deltas.median()
            
            # 2. Convert to seconds (handles Timedelta objects safely)
            if hasattr(median_delta, 'total_seconds'):
                delta_seconds = median_delta.total_seconds()
            else:
                # Fallback if it's already numeric (e.g. nanoseconds as int)
                delta_seconds = float(median_delta) / 1e9 if float(median_delta) > 1e6 else float(median_delta)

            if delta_seconds <= 0:
                return 6
                
            # 3. Calculate shift = 24h / delta
            seconds_in_24h = 86400
            shift = int(round(seconds_in_24h / delta_seconds))
            
            logger.info(f"Dynamic shift: 24h / {delta_seconds}s = {shift} bars")
            return max(1, shift)
            
        except Exception as e:
            # Crucial: print for verification scripts if logger is suppressed
            print(f"ERROR in _calculate_lookahead_shift: {e}")
            logger.warning(f"Failed to calculate dynamic shift: {e}. Using default 6.")
            return 6

if __name__ == "__main__":
    import asyncio
    logging.basicConfig(level=logging.INFO)
    
    # Mock run with random data
    dates = pd.date_range(end=datetime.now(), periods=100, freq='4h')
    prices = 100000 * (1 + (pd.Series(np.random.randn(100)).cumsum() * 0.01))
    df = pd.DataFrame({
        'open': prices,
        'high': prices * 1.01,
        'low': prices * 0.99,
        'close': prices,
        'volume': np.random.randint(100, 1000, 100)
    }, index=dates)
    
    retrainer = AutomatedRetrainer()
    asyncio.run(retrainer.run_retraining_cycle(df))

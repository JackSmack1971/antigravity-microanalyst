# src/microanalyst/validation/suite.py
import yaml
import logging
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class ValidationError(Exception):
    pass

class SchemaValidationException(ValidationError):
    pass

class DataFreshnessException(ValidationError):
    pass

class DataValidator:
    """
    Enforces data quality rules defined in config/validation_rules.yml.
    Prevents 'Garbage In, Garbage Out'.
    """
    
    def __init__(self, config_path="config/validation_rules.yml"):
        self.rules = self._load_config(config_path)

    def _load_config(self, path: str) -> Dict[str, Any]:
        try:
            # Handle absolute or relative paths
            if not os.path.exists(path):
                # Try finding it relative to project root if running from tests
                alt_path = os.path.join(os.getcwd(), path)
                if os.path.exists(alt_path):
                    path = alt_path
                else:
                    logger.warning(f"Validation config not found at {path}. Using defaults.")
                    return {}
            
            with open(path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load validation config: {e}")
            return {}

    def get_rule(self, key: str, rule_type: str) -> Any:
        # Try specific key, fallback to default
        specific = self.rules.get(key, {}).get(rule_type)
        if specific is not None:
            return specific
        return self.rules.get('default', {}).get(rule_type)

    def validate_schema(self, data: Dict[str, Any] | pd.DataFrame, rule_key: str) -> bool:
        """
        Check if data contains required fields.
        """
        required = self.get_rule(rule_key, 'required_fields')
        if not required:
            return True
        
        if isinstance(data, pd.DataFrame):
            missing = [f for f in required if f not in data.columns]
        else:
            missing = [f for f in required if f not in data]
            
        if missing:
            raise SchemaValidationException(f"Missing required fields for '{rule_key}': {missing}")
        return True

    def validate_freshness(self, timestamp: datetime | str, rule_key: str) -> bool:
        """
        Check if data is too old.
        """
        max_age_sec = self.get_rule(rule_key, 'freshness_max_seconds')
        if not max_age_sec:
            return True
        
        if isinstance(timestamp, str):
            try:
                # Handle ISO format
                timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            except ValueError:
                 # Try simple date if ISO fails
                 try:
                     timestamp = datetime.strptime(timestamp, "%Y-%m-%d")
                 except:
                     logger.warning(f"Could not parse timestamp {timestamp}")
                     return True # Skip check if parse fails
                     
        # Ensure timezone awareness compatibility
        now = datetime.now(timestamp.tzinfo) if timestamp.tzinfo else datetime.now()
        
        age = (now - timestamp).total_seconds()
        if age > max_age_sec:
            raise DataFreshnessException(f"Data for '{rule_key}' is stale. Age: {age:.1f}s, Max allowed: {max_age_sec}s")
            
        return True

    def detect_outliers(self, series: pd.Series, rule_key: str) -> pd.Series:
        """
        Return boolean series where True = Outlier.
        Uses Z-Score method.
        """
        threshold = self.get_rule(rule_key, 'outlier_threshold') or 3.0
        
        if series.empty:
            return pd.Series([], dtype=bool)
            
        mean = series.mean()
        std = series.std()
        
        if std == 0:
            return pd.Series([False] * len(series), index=series.index)
            
        z_scores = ((series - mean) / std).abs()
        outliers = z_scores > threshold
        
        if outliers.any():
            logger.warning(f"Detected {outliers.sum()} outliers in '{rule_key}' (Threshold: {threshold} sigma)")
            
        return outliers

    def validate_dataset(self, df: pd.DataFrame, rule_key: str, timestamp_col: str = None) -> Dict[str, Any]:
        """
        Comprehensive validation for a DataFrame.
        Returns report dict. Raises exceptions on hard failures.
        """
        report = {"status": "valid", "warnings": []}
        
        # 1. Schema
        self.validate_schema(df, rule_key)
        
        # 2. Freshness (if timestamp col provided and exists)
        if timestamp_col and timestamp_col in df.columns and not df.empty:
            last_ts = df[timestamp_col].iloc[-1]
            try:
                self.validate_freshness(last_ts, rule_key)
            except DataFreshnessException as e:
                report["status"] = "stale"
                report["warnings"].append(str(e))
                # We might not raise here if we just want to warn for historical datasets
                # But for 'live' data usage, this is bad.
                # Let's verify if user wants hard stop. The method implies validation. 
                # We will log warning and return report status, caller decides to block.
        
        # 3. Outliers (numeric cols only)
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
             # Basic check, maybe refine to specific columns if needed
             outliers = self.detect_outliers(df[col], rule_key)
             if outliers.any():
                 report["warnings"].append(f"Outliers detected in column '{col}': {outliers.sum()} rows")
                 
        return report

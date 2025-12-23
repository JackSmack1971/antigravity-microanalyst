from abc import ABC, abstractmethod
from typing import List, Optional
import pandas as pd
from ..schemas import ConfluenceFactor

class BaseFactorDetector(ABC):
    """
    Abstract base class for all factor detectors used by the ConfluenceCalculator.
    
    Any new technical indicator or data-driven factor detection logic should 
    inherit from this class and implement the `detect` method.
    """
    @abstractmethod
    def detect(self, df_price: pd.DataFrame, **kwargs) -> List[ConfluenceFactor]:
        """
        Detect technical or fundamental factors from price data.
        
        Args:
            df_price: DataFrame containing at least ['open', 'high', 'low', 'close'] columns.
            **kwargs: Additional context like 'df_flows' or 'df_oi' if needed.
            
        Returns:
            List[ConfluenceFactor]: A list of detected factors at specific price levels.
        """
        pass

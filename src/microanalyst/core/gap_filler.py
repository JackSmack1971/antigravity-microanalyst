from datetime import datetime, timedelta
import logging
from src.microanalyst.core.persistence import DatabaseManager

logger = logging.getLogger(__name__)

class GapFiller:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def check_gaps(self, lookback_days=30):
        """
        Identifies missing dates in the last N days.
        """
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=lookback_days)).strftime("%Y-%m-%d")
        
        missing = self.db.get_missing_dates(start_date, end_date)
        
        if missing:
            logger.warning(f"Data Gaps Detected ({len(missing)} days): {missing}")
            # In a future iteration, we would trigger specific adapters here.
            # For now, we just log it as the 'live_retrieval' only runs current state.
            return missing
        else:
            logger.info("No data gaps detected in price history.")
            return []

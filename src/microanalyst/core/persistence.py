import sqlite3
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class DatabaseManager:
    """
    Manages the local SQLite database for 'Golden Copy' data persistence.
    """
    def __init__(self, db_name="microanalyst.db"):
        self.project_root = Path(__file__).parent.parent.parent.parent
        self.db_path = self.project_root / db_name
        self._init_db()

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        """Create tables if they don't exist."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # BTC Price Daily
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS btc_price_daily (
                    date TEXT PRIMARY KEY,
                    open REAL,
                    high REAL,
                    low REAL,
                    close REAL
                )
            ''')
            
            # ETF Flows
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS etf_flows_daily (
                    date TEXT,
                    ticker TEXT,
                    flow_usd REAL,
                    flow_btc REAL,
                    PRIMARY KEY (date, ticker)
                )
            ''')
            
            # Commit changes
            conn.commit()

    def upsert_price(self, df: pd.DataFrame):
        """
        Upsert normalized price data into btc_price_daily.
        Expects DF with columns: date, open, high, low, close.
        """
        if df.empty:
            return

        with self._get_connection() as conn:
            cursor = conn.cursor()
            for _, row in df.iterrows():
                try:
                    date_str = row['date'] if isinstance(row['date'], str) else row['date'].strftime('%Y-%m-%d')
                    cursor.execute('''
                        INSERT INTO btc_price_daily (date, open, high, low, close)
                        VALUES (?, ?, ?, ?, ?)
                        ON CONFLICT(date) DO UPDATE SET
                            open=excluded.open,
                            high=excluded.high,
                            low=excluded.low,
                            close=excluded.close
                    ''', (date_str, row['open'], row['high'], row['low'], row['close']))
                except Exception as e:
                    logger.error(f"Failed to upsert price for {row.get('date')}: {e}")
            conn.commit()
            logger.info(f"Upserted {len(df)} price rows.")

    def upsert_flows(self, df: pd.DataFrame):
        """
        Upsert normalized flow data into etf_flows_daily.
        Expects DF with columns: date, ticker, flow_usd, flow_btc.
        """
        if df.empty:
            return

        with self._get_connection() as conn:
            cursor = conn.cursor()
            for _, row in df.iterrows():
                try:
                    date_str = row['date'] if isinstance(row['date'], str) else row['date'].strftime('%Y-%m-%d')
                    cursor.execute('''
                        INSERT INTO etf_flows_daily (date, ticker, flow_usd, flow_btc)
                        VALUES (?, ?, ?, ?)
                        ON CONFLICT(date, ticker) DO UPDATE SET
                            flow_usd=excluded.flow_usd,
                            flow_btc=excluded.flow_btc
                    ''', (date_str, row['ticker'], row['flow_usd'], row['flow_btc']))
                except Exception as e:
                    logger.error(f"Failed to upsert flow for {row.get('date')} {row.get('ticker')}: {e}")
            conn.commit()
            logger.info(f"Upserted {len(df)} flow rows.")

    def get_missing_dates(self, start_date: str, end_date: str) -> list[str]:
        """
        Returns a list of dates (YYYY-MM-DD) between start and end that are missing from btc_price_daily.
        """
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        
        # generating list of dates
        date_generated = [start + timedelta(days=x) for x in range(0, (end-start).days + 1)]
        expected_dates = {d.strftime("%Y-%m-%d") for d in date_generated}
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT date FROM btc_price_daily WHERE date BETWEEN ? AND ?", (start_date, end_date))
            existing_dates = {row[0] for row in cursor.fetchall()}
            
        missing = sorted(list(expected_dates - existing_dates))
        return missing

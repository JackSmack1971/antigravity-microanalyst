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

            # BTC Price Intraday
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS btc_price_intraday (
                    date TEXT,
                    interval TEXT,
                    open REAL,
                    high REAL,
                    low REAL,
                    close REAL,
                    PRIMARY KEY (date, interval)
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

    def upsert_price(self, df: pd.DataFrame, interval: str = "1d"):
        """
        Upsert normalized price data.
        df: [date, open, high, low, close]
        interval: "1d", "1h", "15m", etc.
        """
        if df.empty:
            return

        table = "btc_price_daily" if interval == "1d" else "btc_price_intraday"

        with self._get_connection() as conn:
            cursor = conn.cursor()
            for _, row in df.iterrows():
                try:
                    date_str = row['date'] if isinstance(row['date'], str) else row['date'].strftime('%Y-%m-%d %H:%M:%S')
                    
                    if interval == "1d":
                        # Legacy Daily Table
                        cursor.execute(f'''
                            INSERT INTO {table} (date, open, high, low, close)
                            VALUES (?, ?, ?, ?, ?)
                            ON CONFLICT(date) DO UPDATE SET
                                open=excluded.open,
                                high=excluded.high,
                                low=excluded.low,
                                close=excluded.close
                        ''', (date_str[:10], row['open'], row['high'], row['low'], row['close'])) # Truncate date for 1d
                    else:
                        # Intraday Table
                        cursor.execute(f'''
                            INSERT INTO {table} (date, interval, open, high, low, close)
                            VALUES (?, ?, ?, ?, ?, ?)
                            ON CONFLICT(date, interval) DO UPDATE SET
                                open=excluded.open,
                                high=excluded.high,
                                low=excluded.low,
                                close=excluded.close
                        ''', (date_str, interval, row['open'], row['high'], row['low'], row['close']))

                except Exception as e:
                    logger.error(f"Failed to upsert price for {row.get('date')} ({interval}): {e}")
            conn.commit()
            logger.info(f"Upserted {len(df)} price rows to {table}.")

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

    def get_price_history(self, limit: int = 1000, interval: str = "1d") -> pd.DataFrame:
        """
        Fetches price history as a DataFrame.
        """
        table = "btc_price_daily" if interval == "1d" else "btc_price_intraday"
        query = f"SELECT * FROM {table} ORDER BY date DESC LIMIT ?"
        
        with self._get_connection() as conn:
            # params must be tuple
            if interval == "1d":
                df = pd.read_sql_query(query, conn, params=(limit,))
            else:
                # For intraday, we filter by interval
                query = f"SELECT * FROM {table} WHERE interval=? ORDER BY date DESC LIMIT ?"
                df = pd.read_sql_query(query, conn, params=(interval, limit))
        
        if not df.empty:
            df["date"] = pd.to_datetime(df["date"])
            df = df.sort_values("date", ascending=True).reset_index(drop=True)
            
        return df

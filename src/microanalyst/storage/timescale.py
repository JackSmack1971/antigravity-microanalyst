from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import Column, DateTime, String, Float, text, BigInteger
import os
import asyncio
from datetime import datetime

Base = declarative_base()

class BTCPrice(Base):
    __tablename__ = 'btc_price'
    
    date = Column(DateTime(timezone=True), primary_key=True)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    volume = Column(BigInteger, nullable=True)

class ETFFlow(Base):
    __tablename__ = 'etf_flows'
    
    date = Column(DateTime(timezone=True), primary_key=True)
    ticker = Column(String(20), primary_key=True)
    flow_usd = Column(Float) # Using Float for simplicity, Decimal better for finance
    
class DataStorage:
    def __init__(self, connection_string=None):
        self.connection_string = connection_string or os.getenv("DATABASE_URL")
        self.engine = None
        self.async_session = None
        self._connected = False

    async def connect(self):
        if not self.connection_string:
            print("WARNING: No DATABASE_URL provided. Storage disabled.")
            return False

        try:
            self.engine = create_async_engine(
                self.connection_string,
                echo=False,
                pool_pre_ping=True
            )
            
            # Create tables
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
                
            self.async_session = sessionmaker(
                self.engine, class_=AsyncSession, expire_on_commit=False
            )
            self._connected = True
            return True
        except Exception as e:
            print(f"ERROR: Failed to connect to database: {e}")
            return False

    async def save_price_data(self, df):
        if not self._connected or df.empty: return
        
        async with self.async_session() as session:
            try:
                # Naive Loop insert for MVP - Bulk insert preferred for production
                for _, row in df.iterrows():
                    # Upsert logic (SQLAlchemy < 2.0 specific upsert needs dialect)
                    # For MVP we will just try insert and ignore dupes or do merge
                    # Ideally use postgresql.insert().on_conflict_do_update()
                    
                    obj = await session.get(BTCPrice, row['date'])
                    if not obj:
                        obj = BTCPrice(
                            date=row['date'],
                            open=row.get('open'),
                            high=row.get('high'),
                            low=row.get('low'),
                            close=row['close']
                        )
                        session.add(obj)
                    else:
                        obj.close = row['close']
                        
                await session.commit()
            except Exception as e:
                print(f"DB Error: {e}")
                await session.rollback()

    async def save_etf_flows(self, df):
        if not self._connected or df.empty: return
        
        async with self.async_session() as session:
            try:
                for _, row in df.iterrows():
                    obj = await session.get(ETFFlow, (row['date'], row['ticker']))
                    if not obj:
                        session.add(ETFFlow(
                            date=row['date'],
                            ticker=row['ticker'],
                            flow_usd=row['flow_usd']
                        ))
                await session.commit()
            except Exception as e:
                 print(f"DB Error: {e}")
                 await session.rollback()

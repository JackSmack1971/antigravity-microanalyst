import asyncio
import logging
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
import pandas as pd
from jinja2 import Environment, FileSystemLoader

from src.microanalyst.data_loader import (
    load_price_history,
    load_etf_flows,
    load_btcetffundflow_json,
    load_coinalyze_oi,
    load_coinalyze_funding,
    load_coingecko_volume
)

logger = logging.getLogger(__name__)

class MarketIntelligenceOrchestrator:
    """
    Unified daily market report generator following a research-validated cognitive architecture.
    Sources: TwelveData (Spot), Bitbo (ETF), Coinalyze (OI/Funding), CoinGecko (Volume), btcetffundflow (Holdings).
    """

    def __init__(self, template_dir: str = "src/microanalyst/intelligence/templates"):
        self.project_root = Path(__file__).parent.parent.parent.parent
        self.template_dir = self.project_root / template_dir
        self.data_dir = self.project_root / "data_exports"
        self.screenshot_dir = self.project_root / "screenshots"
        self.report_dir = self.project_root / "reports"
        
        self.report_dir.mkdir(parents=True, exist_ok=True)
        
        self.jinja_env = Environment(loader=FileSystemLoader(str(self.template_dir)))
        logger.info(f"MarketIntelligenceOrchestrator initialized with template dir: {self.template_dir}")

    async def generate_daily_report(self) -> str:
        """Fetch all data points, perform CoT reasoning, and generate the final report."""
        logger.info("Generating unified daily market report...")
        
        # 1. Data Acquisition
        data = self._gather_all_data()
        
        # 1b. Recursive Recovery: Check for critical missing data
        needs_retry = False
        if data.get("spot_turnover", 0) == 0: needs_retry = True
        if data.get("derivatives_oi", {}).get("all", 0) == 0: needs_retry = True
        
        if needs_retry:
            logger.warning("Critical metrics (Volume/OI) missing. Triggering recursive recovery...")
            from src.microanalyst.core.async_retrieval import AsyncRetrievalEngine
            engine = AsyncRetrievalEngine()
            await engine.execute_pipeline()
            # Gathers data again after re-fetch
            data = self._gather_all_data()

        # 2. Cognitive Processing (CoT + Cross-Consistency)
        reasoning = self._perform_reasoning(data)
        
        # 3. Build Template Context
        context = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "data": data,
            "reasoning": reasoning,
            "screenshots": self._get_relevant_screenshots()
        }
        
        # 4. Render Report
        try:
            template = self.jinja_env.get_template("daily_intel.j2")
            report = template.render(**context)
            
            # Save to file
            report_path = self.report_dir / f"Daily_Intelligence_Report_{datetime.now().strftime('%Y%m%d')}.md"
            with open(report_path, "w", encoding="utf-8") as f:
                f.write(report)
            
            # Also save as latest
            latest_path = self.project_root / "Daily_Intelligence_Report_Latest.md"
            with open(latest_path, "w", encoding="utf-8") as f:
                f.write(report)
                
            logger.info(f"Report generated: {latest_path}")
            return report
            
        except Exception as e:
            logger.error(f"Failed to render report: {e}")
            raise

    def _gather_all_data(self) -> Dict[str, Any]:
        """Gather all 7 required data points from parsers."""
        data = {}
        
        # 1. Spot OHLC (TwelveData)
        price_df = load_price_history()
        if not price_df.empty:
            latest = price_df.iloc[-1]
            data["spot"] = {
                "date": latest["Date"].strftime("%Y-%m-%d"),
                "open": latest["Open"],
                "high": latest["High"],
                "low": latest["Low"],
                "close": latest["Close"]
            }
        else:
            data["spot"] = {"status": "error", "message": "No price data found"}
            
        # 2. US ETF Flows (Bitbo)
        etf_df = load_etf_flows()
        if not etf_df.empty:
            latest_flow = etf_df.iloc[-1]
            data["etf_flows"] = {
                "date": latest_flow["Date"].strftime("%Y-%m-%d"),
                "net_flow": latest_flow["Net_Flow"]
            }
        else:
            data["etf_flows"] = {"status": "error", "message": "No ETF flow data found"}

        # 3. Derivatives OI (Coinalyze)
        data["derivatives_oi"] = load_coinalyze_oi()

        # 4. Funding Rates (Coinalyze)
        data["funding_rates"] = load_coinalyze_funding()

        # 5. Spot Turnover (CoinGecko) - Try API first, then HTML
        from src.microanalyst.data_loader import load_coingecko_api
        api_data = load_coingecko_api()
        if api_data["volume"] > 0:
            data["spot_turnover"] = api_data["volume"]
            # If price is missing from TwelveData, use CG API price
            if data["spot"].get("status") == "error":
                 data["spot"] = {
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "open": api_data["price"],
                    "high": api_data["price"],
                    "low": api_data["price"],
                    "close": api_data["price"],
                    "source": "CoinGecko API"
                }
        else:
            data["spot_turnover"] = load_coingecko_volume()

        # 6. Holdings-Derived ETF Flows (btcetffundflow)
        holdings_file = self.data_dir / "btcetffundflow_holdings_derived.html"
        holdings_df = load_btcetffundflow_json(str(holdings_file))
        if holdings_df is not None and not holdings_df.empty:
            # Aggregate per date
            latest_date = holdings_df["Date"].max()
            # Net Flow is already calculated as 'Value' in Delta Algorithm v2
            daily_total = holdings_df[holdings_df["Date"] == latest_date]["Value"].sum()
            data["holdings_flows"] = {
                "date": latest_date.strftime("%Y-%m-%d"),
                "total_value": daily_total
            }
        else:
            data["holdings_flows"] = {"status": "error", "message": "No holdings data found"}
            
        return data

    def _perform_reasoning(self, data: Dict[str, Any]) -> Dict[str, List[str]]:
        """Implementation of cognitive architecture reasoning blocks."""
        reasoning = {
            "chain_of_thought": [],
            "consistency_validation": []
        }
        
        # CoT: Price and Volume
        spot = data.get("spot", {})
        vol = data.get("spot_turnover", 0)
        if isinstance(spot, dict) and "close" in spot:
            if spot["close"] > spot["open"]:
                reasoning["chain_of_thought"].append(
                    f"Price closed UP at ${spot['close']:,.2f}. High volume proxy (${vol/1e9:.1f}B) suggests sustained accumulation." 
                    if vol > 10e9 else f"Price closed UP but low volume (${vol/1e9:.1f}B) indicates potential exhaustion."
                )
            else:
                reasoning["chain_of_thought"].append(
                    f"Price closed DOWN at ${spot['close']:,.2f}. High volume (${vol/1e9:.1f}B) indicates aggressive selling pressure."
                )

        # CoT: Derivatives
        oi = data.get("derivatives_oi", {}).get("all", 0)
        if oi > 0:
            reasoning["chain_of_thought"].append(
                f"Open Interest at ${oi/1e9:.1f}B. High OI with positive funding suggests heavy long positioning."
            )

        # 3. Consensus Engine (Truth Resolver)
        etf = data.get("etf_flows", {}).get("net_flow", 0)
        h_flow = data.get("holdings_flows", {}).get("total_value", 0) / 1e6 # holdings_df Value is raw USD if > 1M, or BTC. 
        # Note: holdings_df is now delta-based in data_loader.
        
        diff_pct = 100.0
        if abs(etf) > 0:
            diff_pct = abs(etf - h_flow) / abs(etf)
        
        confidence = 0
        if diff_pct < 0.05: confidence = 100
        elif diff_pct < 0.15: confidence = 85
        elif diff_pct < 0.50: confidence = 50
        else: confidence = 20
        
        data["consensus"] = {
            "confidence_score": confidence,
            "primary_source": "Bitbo",
            "secondary_source": "btcetffundflow",
            "status": "Verified" if confidence > 70 else "Caution"
        }

        # Update reasoning
        reasoning["consistency_validation"].append(
            f"CONSENSUS [{data['consensus']['status']}]: {confidence}% confidence. "
            f"Bitbo (${etf:.1f}M) vs Holdings-Derived (${h_flow:.1f}M). "
            + ("High reliability." if confidence > 70 else "Discrepancy exceeds tolerance; prioritizing primary source.")
        )
            
        return reasoning

    def _get_relevant_screenshots(self) -> Dict[str, str]:
        """Collect and return absolute paths for CoinGlass screenshots."""
        screens = {}
        target_files = {
            "spot_flows": "coinglass_spot_inflow_outflow_screenshot_only_visible.png",
            "funding_heatmap": "coinglass_funding_heatmap_screenshot_only_visible.png",
            "liquidation_heatmap": "coinglass_liquidation_heatmap_screenshot_only_visible.png"
        }
        
        for key, filename in target_files.items():
            path = self.screenshot_dir / filename
            if path.exists():
                screens[key] = f"file:///{str(path).replace('\\', '/')}"
                
        return screens

if __name__ == "__main__":
    import asyncio
    logging.basicConfig(level=logging.INFO)
    orchestrator = MarketIntelligenceOrchestrator()
    asyncio.run(orchestrator.generate_daily_report())

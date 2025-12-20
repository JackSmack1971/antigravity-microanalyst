import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
from jinja2 import Environment, FileSystemLoader

class ReportGenerator:
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent.parent
        self.data_dir = self.project_root / "data_clean"
        self.template_dir = Path(__file__).parent / "templates"
        self.env = Environment(loader=FileSystemLoader(self.template_dir))
        
    def _load_data(self):
        price_path = self.data_dir / "btc_price_normalized.csv"
        etf_path = self.data_dir / "etf_flows_normalized.csv"
        
        df_price = pd.read_csv(price_path) if price_path.exists() else pd.DataFrame()
        df_etf = pd.read_csv(etf_path) if etf_path.exists() else pd.DataFrame()
        
        if not df_price.empty:
            df_price['date'] = pd.to_datetime(df_price['date'])
        if not df_etf.empty:
            df_etf['date'] = pd.to_datetime(df_etf['date'])
            
        return df_price, df_etf

    def generate_daily_market_summary(self, target_date=None):
        if target_date is None:
            target_date = datetime.now()
        
        df_price, df_etf = self._load_data()
        
        if df_price.empty:
            return {"error": "No price data available"}
            
        # Price Metrics
        # Filter up to target date
        mask_price = df_price['date'] <= target_date
        df_p = df_price[mask_price].sort_values('date')
        
        if df_p.empty:
             return {"error": f"No data before {target_date}"}

        current_price = df_p.iloc[-1]['close']
        
        def pct_change(df, days):
            if len(df) < days: return 0.0
            old = df.iloc[-days]['close']
            return ((current_price - old) / old) * 100

        price_metrics = {
            "current": current_price,
            "change_1d": pct_change(df_p, 2), # approx rows for daily
            "change_7d": pct_change(df_p, 7),
            "volatility_7d": df_p['close'].tail(7).std()
        }
        
        # ETF Metrics
        # Filter last 7 days
        start_date = target_date - timedelta(days=7)
        mask_etf = (df_etf['date'] >= start_date) & (df_etf['date'] <= target_date)
        df_e = df_etf[mask_etf]
        
        etf_metrics = {
            "net_flow_7d": df_e['flow_usd'].sum() / 1e6 if not df_e.empty else 0,
            "top_inflows": df_e.groupby('ticker')['flow_usd'].sum().nlargest(3).to_dict() if not df_e.empty else {},
            "top_outflows": df_e.groupby('ticker')['flow_usd'].sum().nsmallest(3).to_dict() if not df_e.empty else {}
        }
        
        # Quality
        last_date = df_p.iloc[-1]['date']
        freshness = (target_date - last_date).total_seconds() / 3600
        
        return {
            "date": target_date.strftime("%Y-%m-%d"),
            "price_metrics": price_metrics,
            "etf_metrics": etf_metrics,
            "data_quality": {"freshness_hours": freshness}
        }

    def generate_markdown_report(self, summary):
        template = self.env.get_template("daily_summary.md")
        return template.render(**summary)

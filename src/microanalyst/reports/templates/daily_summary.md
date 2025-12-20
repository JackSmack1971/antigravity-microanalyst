# Daily Market Summary: {{ date }}

## 📊 Market Overview
- **BTC Price**: ${{ "{:,.2f}".format(price_metrics.current) }}
- **24h Change**: {{ "{:+.2f}%".format(price_metrics.change_1d) }}
- **7d Change**: {{ "{:+.2f}%".format(price_metrics.change_7d) }}
- **Volatility (7d)**: {{ "{:,.2f}".format(price_metrics.volatility_7d) }}

## 🏦 ETF Flows (Last 7 Days)
- **Net Flow**: ${{ "{:,.2f}M".format(etf_metrics.net_flow_7d) }}

### Top Inflows
{% for ticker, flow in etf_metrics.top_inflows.items() %}
- **{{ ticker }}**: +${{ "{:,.2f}M".format(flow/1000000) }}
{% endfor %}

### Top Outflows
{% for ticker, flow in etf_metrics.top_outflows.items() %}
- **{{ ticker }}**: ${{ "{:,.2f}M".format(flow/1000000) }}
{% endfor %}

## 🛠 Data Quality
- **Freshness**: {{ "{:.1f}".format(data_quality.freshness_hours) }} hours ago
- **Status**: {{ "✅ Nominal" if data_quality.freshness_hours < 24 else "⚠️ Stale" }}

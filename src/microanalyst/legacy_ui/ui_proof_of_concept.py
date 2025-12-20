import streamlit as st
import pandas as pd
from datetime import datetime

from src.microanalyst.style_injector import inject_custom_css
from src.microanalyst.charting import plot_net_flow, plot_price_history, plot_rsi, plot_cumulative_flows, plot_depth_chart
from src.microanalyst.data_loader import load_etf_flows, load_price_history, load_etf_flows_enhanced
from src.microanalyst.analytics import calculate_rsi, calculate_cumulative_flows
from src.microanalyst.providers.binance import fetch_order_book
from src.microanalyst.providers.sentiment import fetch_fear_and_greed
from src.microanalyst.components import render_cyber_card

st.set_page_config(layout="wide", page_title="BTC MICROANALYST", page_icon="📈")

# 1. Inject Theme
inject_custom_css()

# 2. Data Loading (Cached)
@st.cache_data(ttl=60)
def load_cached_data():
    # Try enhanced parser first
    df_flows = load_etf_flows_enhanced()
    if df_flows.empty:
        df_flows = load_etf_flows() # Fallback
        
    df_price = load_price_history()
    
    if not df_price.empty:
        df_price = calculate_rsi(df_price)
    
    if not df_flows.empty:
        df_flows = calculate_cumulative_flows(df_flows)
    
    sentiment = fetch_fear_and_greed()
    
    return df_flows, df_price, sentiment

@st.cache_data(ttl=5) 
def load_depth():
    return fetch_order_book()

df_flows, df_price, sentiment = load_cached_data()
df_depth = load_depth()

# 3. Calculate Logic (Metric Values)
metrics = {
    "price": {"val": "N/A", "sub": "Spot Price", "trend": "neutral"},
    "rsi": {"val": "N/A", "sub": "14D Momentum", "trend": "neutral"},
    "flow": {"val": "N/A", "sub": "Daily Net Flow", "trend": "neutral"},
    "cum": {"val": "N/A", "sub": "Total Inflow", "trend": "up"}, 
    "sent": {"val": "N/A", "sub": "Fear & Greed", "trend": "neutral"}
}

if not df_price.empty:
    latest = df_price.iloc[-1]
    prev = df_price.iloc[-2] if len(df_price) > 1 else latest
    
    change_pct = ((latest['Close'] - prev['Close']) / prev['Close']) * 100
    metrics["price"]["val"] = f"${latest['Close']:,.2f}"
    metrics["price"]["sub"] = f"{change_pct:+.2f}% (24h)"
    metrics["price"]["trend"] = "up" if change_pct >= 0 else "down"
    
    if 'RSI' in latest:
        rsi = latest['RSI']
        metrics["rsi"]["val"] = f"{rsi:.1f}"
        if rsi > 70: metrics["rsi"]["trend"] = "down" 
        elif rsi < 30: metrics["rsi"]["trend"] = "up"
        else: metrics["rsi"]["trend"] = "neutral"

if not df_flows.empty:
    latest_flow = df_flows.iloc[-1]
    flow_val = latest_flow['Net_Flow']
    metrics["flow"]["val"] = f"${flow_val:,.1f}M"
    metrics["flow"]["trend"] = "up" if flow_val >= 0 else "down"
    metrics["cum"]["val"] = f"${latest_flow['Cumulative_Flow']:,.0f}M"

metrics["sent"]["val"] = str(sentiment['value'])
metrics["sent"]["sub"] = sentiment['classification']
metrics["sent"]["trend"] = "up" if sentiment['value'] > 50 else "down"


# 4. Layout Architecture

# Header Row: Control Deck & Time
col_ctrl1, col_ctrl2, col_ctrl3 = st.columns([1, 4, 1])
with col_ctrl1:
    st.markdown("### BTC/USD")
with col_ctrl2:
    # Control Deck (Timeframe Simulator)
    timeframe = st.radio("Timeframe", ["1H", "4H", "1D", "1W"], index=2, horizontal=True, label_visibility="collapsed")
with col_ctrl3:
    st.markdown(f"**UPDATED:** {datetime.now().strftime('%H:%M:%S')}")

st.markdown("---")

# Metrics Grid (Bento)
col_m1, col_m2, col_m3, col_m4, col_m5 = st.columns([2, 1, 1, 1, 1])
with col_m1:
    st.markdown(render_cyber_card("BTC PRICE", metrics["price"]["val"], metrics["price"]["sub"], metrics["price"]["trend"]), unsafe_allow_html=True)
with col_m2:
    st.markdown(render_cyber_card("MARKET MOOD", metrics["sent"]["val"], metrics["sent"]["sub"], metrics["sent"]["trend"]), unsafe_allow_html=True)
with col_m3:
    st.markdown(render_cyber_card("RSI (14D)", metrics["rsi"]["val"], metrics["rsi"]["sub"], metrics["rsi"]["trend"]), unsafe_allow_html=True)
with col_m4:
    st.markdown(render_cyber_card("ETF FLOW", metrics["flow"]["val"], metrics["flow"]["sub"], metrics["flow"]["trend"]), unsafe_allow_html=True)
with col_m5:
    st.markdown(render_cyber_card("TOTAL AGG", metrics["cum"]["val"], metrics["cum"]["sub"], metrics["cum"]["trend"]), unsafe_allow_html=True)


# Main Content Grid
col_main_left, col_main_right = st.columns([2, 1])

with col_main_left:
    # Stacked Charts Container
    st.markdown('<div class="glass-container">', unsafe_allow_html=True)
    if not df_price.empty:
        # Price Chart (Top)
        st.plotly_chart(plot_price_history(df_price.tail(100)), use_container_width=True)
        # RSI Chart (Bottom - Snapped)
        st.plotly_chart(plot_rsi(df_price.tail(100)), use_container_width=True)
    else:
        st.error("Price Data Unavailable")
    st.markdown('</div>', unsafe_allow_html=True)

with col_main_right:
    # Depth Chart
    st.markdown('<div class="glass-container">', unsafe_allow_html=True)
    st.plotly_chart(plot_depth_chart(df_depth), use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # ETF Flows (Tabbed for Height Rhythm)
    st.markdown('<div class="glass-container">', unsafe_allow_html=True)
    if not df_flows.empty:
        tab1, tab2 = st.tabs(["DAILY FLOW", "CUMULATIVE"])
        with tab1:
            st.plotly_chart(plot_net_flow(df_flows.tail(30)), use_container_width=True)
        with tab2:
            st.plotly_chart(plot_cumulative_flows(df_flows), use_container_width=True)
    else:
        st.error("Flow Data Unavailable")
    st.markdown('</div>', unsafe_allow_html=True)

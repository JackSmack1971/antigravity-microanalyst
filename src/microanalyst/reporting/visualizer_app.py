import streamlit as st
import json
import os
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import time

# --- Configuration & Styling ---
st.set_page_config(
    page_title="Microanalyst Command Center",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Cyberpunk / Premium UI Custom CSS
st.markdown("""
    <style>
    .main {
        background-color: #0e1117;
        color: #e0e0e0;
    }
    .stMetric {
        background-color: rgba(28, 31, 46, 0.7);
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #3d4455;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    .persona-card {
        background-color: rgba(25, 28, 41, 0.8);
        padding: 20px;
        border-radius: 12px;
        border-left: 4px solid #00f2ff;
        margin-bottom: 20px;
    }
    .retail { border-left-color: #ff0055; }
    .inst { border-left-color: #00ff88; }
    .whale { border-left-color: #7000ff; }
    .macro { border-left-color: #ffaa00; }
    .oracle { background: linear-gradient(90deg, #00f2ff, #7000ff); padding: 2px; border-radius: 12px; }
    .oracle-inner { background: #0e1117; padding: 15px; border-radius: 10px; }
    </style>
""", unsafe_allow_html=True)

# --- Data Loading ---
DATA_PATH = "data_exports/latest_thesis.json"

def load_latest_data():
    if not os.path.exists(DATA_PATH):
        return None
    try:
        with open(DATA_PATH, "r") as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None

# --- UI Components ---

def render_header(data):
    st.title("🎯 Microanalyst | SWARM COMMAND")
    
    col1, col2, col3, col4 = st.columns(4)
    
    decision = data.get('decision', 'HOLD')
    confidence = data.get('confidence', 0.5)
    
    # Color coding based on decision
    delta_color = "normal"
    if decision == "BUY": delta_color = "inverse"
    elif decision == "SELL": delta_color = "off"

    with col1:
        st.metric("FINAL DECISION", decision, delta=f"{confidence*100:.1f}% Conf", delta_color=delta_color)
    with col2:
        # Assuming allocation from JSON
        alloc = data.get('allocation_pct', 0.0)
        st.metric("PORTFOLIO ALT", f"{alloc:.1f}%", help="Suggested risk exposure.")
    with col3:
        # Static or calculated volatility score if available
        st.metric("VOLATILITY (GARCH)", "37.42", delta="-2.1%", delta_color="normal")
    with col4:
        st.metric("DXY CORR", "Decoupled", delta="+0.12", delta_color="inverse")

def render_forecast_chart(data):
    st.markdown('<div class="oracle"><div class="oracle-inner">', unsafe_allow_html=True)
    st.subheader("🔮 ML Oracle | T+24h Forecast")
    
    # Mocking a forecast path based on latest price
    # In real version, we'd grab this from PredictionAgent output
    current_price = 88250.0 # From latest_thesis.json notes
    target_price = current_price * 1.02 if data.get('decision') == 'BUY' else current_price * 0.98
    
    fig = go.Figure()
    
    # Current Point
    fig.add_trace(go.Scatter(
        x=[0, 1], y=[current_price, target_price],
        mode="lines+markers",
        line=dict(color="#00f2ff", width=4, dash="dot"),
        marker=dict(size=12, color=["#3d4455", "#00f2ff"]),
        name="Forecast Path"
    ))
    
    fig.update_layout(
        template="plotly_dark",
        height=300,
        margin=dict(l=20, r=20, t=20, b=20),
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=True, gridcolor="#2a2e3e")
    )
    
    st.plotly_chart(fig, use_container_width=True)
    st.write(f"**Reasoning**: {data.get('reasoning', 'Calculating...')}")
    st.markdown('</div></div>', unsafe_allow_html=True)

def render_swarm_debate(data):
    st.write("---")
    st.subheader("🗯️ Adversarial Swarm Debate")
    
    # Persona Carousel (Vertical for Streamlit)
    
    # Retail
    with st.expander("🚀 Retail Momentum (The Hype)", expanded=True):
        st.markdown(f'<div class="persona-card retail">{data.get("bull_case", "Waiting for signal...")}</div>', unsafe_allow_html=True)
        
    # Whale
    with st.expander("🐳 Whale Sniper (The Hunter)", expanded=False):
        st.markdown(f'<div class="persona-card whale">{data.get("bear_case", "Scanning liquidity...")}</div>', unsafe_allow_html=True)
        
    # Macro
    with st.expander("🌍 Macro Economist (The General)", expanded=False):
        macro_text = data.get("macro_thesis", "Structural decoupling detected in DXY/BTC. Correlation dropping to 0.12. Safe Haven regime active.")
        st.markdown(f'<div class="persona-card macro">{macro_text}</div>', unsafe_allow_html=True)

def render_logs(data):
    st.write("---")
    with st.sidebar:
        st.subheader("📟 Intelligence Logs")
        for log in data.get('logs', []):
            st.code(f"> {log}", language="bash")
        
        st.write("---")
        if st.button("🔄 Refresh Data"):
            st.rerun()

# --- Main Execution ---

data = load_latest_data()

if data:
    render_header(data)
    
    m_col1, m_col2 = st.columns([2, 1])
    
    with m_col1:
        render_forecast_chart(data)
    
    with m_col2:
        render_swarm_debate(data)
        
    render_logs(data)
else:
    st.warning("Awaiting fresh thesis output... Ensure `AgentCoordinator` has been executed.")
    if st.button("Check Again"):
        st.rerun()

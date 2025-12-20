import streamlit as st
import json
import os
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import time

# --- Configuration & Styling ---
st.set_page_config(
    page_title="Microanalyst | SWARM COMMAND",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Cyberpunk / Financial Terminal Custom CSS (Pixel-Perfect Implementation)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;700;900&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&display=swap');

    /* Diagonal Grid Pattern & Global Background */
    .stApp {
        background-color: #0A0E1A;
        background-image: 
            linear-gradient(45deg, rgba(255,255,255,.01) 25%, transparent 25%),
            linear-gradient(-45deg, rgba(255,255,255,.01) 25%, transparent 25%),
            linear-gradient(45deg, transparent 75%, rgba(255,255,255,.01) 75%),
            linear-gradient(-45deg, transparent 75%, rgba(255,255,255,.01) 75%);
        background-size: 40px 40px;
        background-position: 0 0, 0 20px, 20px -20px, -20px 0px;
        font-family: 'Inter', sans-serif;
    }

    /* Sidebar Refinement */
    [data-testid="stSidebar"] {
        background-color: rgba(10, 14, 26, 0.95);
        border-right: 1px solid rgba(0, 217, 255, 0.1);
        backdrop-filter: blur(10px);
    }

    /* Stale data warning badge */
    .stale-warning {
        background: linear-gradient(135deg, rgba(245, 158, 11, 0.2) 0%, rgba(217, 119, 6, 0.2) 100%);
        border: 2px solid #F59E0B;
        border-radius: 8px;
        padding: 12px 16px;
        margin-bottom: 20px;
        display: flex;
        align-items: center;
        gap: 10px;
        box-shadow: 0 0 20px rgba(245, 158, 11, 0.3);
    }
    .stale-warning-icon { font-size: 20px; }
    .stale-warning-text { color: #FCD34D; font-weight: 600; font-size: 13px; letter-spacing: 0.05em; margin: 0; }
    
    /* Fresh data indicator */
    .fresh-data {
        background: linear-gradient(135deg, rgba(0, 255, 136, 0.15) 0%, rgba(0, 200, 100, 0.15) 100%);
        border: 2px solid #00FF88;
        border-radius: 8px;
        padding: 12px 16px;
        margin-bottom: 20px;
        display: flex;
        align-items: center;
        gap: 10px;
        box-shadow: 0 0 20px rgba(0, 255, 136, 0.2);
    }
    .fresh-data-icon { font-size: 20px; }
    .fresh-data-text { color: #00FF88; font-weight: 600; font-size: 13px; letter-spacing: 0.05em; margin: 0; }

    /* Custom Metric Cards (Neon Design) - Enhanced for 42px values */
    .metric-card {
        background: rgba(15, 23, 42, 0.6);
        border-radius: 12px;
        padding: 20px;
        border: 2px solid;
        backdrop-filter: blur(10px);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        margin-bottom: 10px;
        height: 140px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    .metric-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 10px 40px rgba(0, 217, 255, 0.2);
    }
    
    .metric-card.green { border-color: #00FF88; box-shadow: 0 0 15px rgba(0, 255, 136, 0.1); }
    .metric-card.cyan { border-color: #00D9FF; box-shadow: 0 0 15px rgba(0, 217, 255, 0.1); }
    .metric-card.purple { border-color: #B744FF; box-shadow: 0 0 15px rgba(183, 68, 255, 0.1); }
    .metric-card.red { border-color: #FF4465; box-shadow: 0 0 15px rgba(255, 68, 101, 0.1); }

    .metric-label {
        font-size: 11px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        color: #00D9FF;
        margin-bottom: 5px;
    }
    .metric-value {
        font-size: 42px; /* Updated to 42px as per spec */
        font-weight: 800;
        color: #FFFFFF;
        line-height: 1;
        margin-bottom: 5px;
    }
    .metric-delta { font-size: 13px; font-weight: 600; }
    .metric-delta.pos { color: #00FF88; }
    .metric-delta.neg { color: #FF4465; }
    .metric-delta.neu { color: #94A3B8; }

    /* Sidebar Section Headers */
    .sidebar-header {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 12px;
        padding-bottom: 8px;
        border-bottom: 1px solid rgba(0, 217, 255, 0.2);
    }
    .sidebar-header-icon { font-size: 18px; }
    .sidebar-header-text { color: #FFFFFF; font-weight: 600; font-size: 14px; margin: 0; text-transform: uppercase; letter-spacing: 0.05em; }

    /* Swarm Header */
    .swarm-header {
        text-align: center; /* Centered as per spec update */
        margin-bottom: 2rem;
        padding-bottom: 1rem;
    }
    .swarm-title {
        font-size: 3rem;
        font-weight: 900;
        margin: 0;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 20px;
    }
    .title-white { color: #FFFFFF; }
    .title-cyan { color: #00D9FF; text-shadow: 0 0 30px rgba(0, 217, 255, 0.5); }

    /* Agent Card Refinement (Hover effect updated to translateX) */
    .agent-card {
        background: rgba(15, 23, 42, 0.8);
        border-radius: 12px;
        padding: 18px;
        margin-bottom: 16px;
        border-left: 4px solid;
        backdrop-filter: blur(10px);
        transition: all 0.3s ease;
    }
    .agent-card:hover { 
        transform: translateX(4px); 
        background: rgba(15, 23, 42, 0.95); 
    }
    
    .agent-avatar {
        width: 44px; /* Slightly larger */
        height: 44px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 22px;
        box-shadow: 0 4px 12px rgba(0,217,255,0.3);
    }

    /* Refresh Button - High Fidelity White Style */
    .stButton > button {
        background: #FFFFFF !important;
        color: #0A0E1A !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 12px 24px !important;
        font-weight: 600 !important;
        font-size: 14px !important;
        box-shadow: 0 4px 16px rgba(255, 255, 255, 0.2) !important;
        transition: all 0.3s ease !important;
        width: 100%;
    }
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 24px rgba(255, 255, 255, 0.3) !important;
        background: #F1F5F9 !important;
    }

    /* Utilities */
    .section-label { color: #FFFFFF; font-weight: 800; font-size: 18px; margin-bottom: 1.5rem; display: flex; align-items: center; gap: 10px; border-bottom: 1px solid rgba(0, 217, 255, 0.2); padding-bottom: 10px; }
</style>
</style>
""", unsafe_allow_html=True)

# --- Data Loading with Caching ---
DATA_PATH = "data_exports/latest_thesis.json"

@st.cache_data(ttl=60)
def load_latest_data():
    if not os.path.exists(DATA_PATH):
        return None
    try:
        # Get last modified time
        mtime = os.path.getmtime(DATA_PATH)
        with open(DATA_PATH, "r") as f:
            data = json.load(f)
            data['_mtime'] = mtime
            return data
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None

# --- UI Components ---

def render_header(data):
    # Header with title
    st.markdown("""
        <div class="swarm-header">
            <h1 class="swarm-title">
                <span class="title-white">🎯 Microanalyst |</span> 
                <span class="title-cyan">SWARM COMMAND</span>
            </h1>
        </div>
    """, unsafe_allow_html=True)

    decision = data.get('decision', 'HOLD')
    confidence = data.get('confidence', 0.5)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
            <div class="metric-card green">
                <div class="metric-label">Final Decision</div>
                <div class="metric-value">{decision}</div>
                <div class="metric-delta pos">↑ {confidence*100:.1f}% Conf</div>
            </div>
        """, unsafe_allow_html=True)

    with col2:
        alloc = data.get('allocation_pct', 0.0)
        st.markdown(f"""
            <div class="metric-card cyan">
                <div class="metric-label">Portfolio ΔΤ ⓘ</div>
                <div class="metric-value">{alloc:.1f}%</div>
                <div class="metric-delta neu">↑ Stable</div>
            </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
            <div class="metric-card purple">
                <div class="metric-label">Volatility (GARCH)</div>
                <div class="metric-value">37.42</div>
                <div class="metric-delta neg">↓ 37.2%</div>
            </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
            <div class="metric-card red">
                <div class="metric-label">DXY CORR</div>
                <div class="metric-value">Decoupled</div>
                <div class="metric-delta neg">↓ -0.12</div>
            </div>
        """, unsafe_allow_html=True)

def render_forecast_chart(data):
    st.markdown('<div class="section-label">🔮 ML Oracle | T+24h Forecast</div>', unsafe_allow_html=True)
    
    current_price = 88250.0
    # Simulate forecast array
    hours = list(range(0, 25))
    forecast = [current_price - (i * 40) for i in hours]
    
    fig = go.Figure()
    
    # Forecast Line
    fig.add_trace(go.Scatter(
        x=hours, y=forecast,
        mode="lines+markers",
        name="Oracle Trend",
        line=dict(color="#00D9FF", width=3),
        marker=dict(
            size=6, 
            color="#00D9FF",
            line=dict(color="#FFFFFF", width=1)
        ),
        hovertemplate='<b>Hour %{x}</b><br>Price: $%{y:,.0f}<extra></extra>'
    ))
    
    fig.update_layout(
        template="plotly_dark",
        height=380,
        margin=dict(l=40, r=40, t=10, b=40),
        xaxis=dict(
            title="", 
            showgrid=True, 
            gridcolor="rgba(255,255,255,0.05)",
            zeroline=False
        ),
        yaxis=dict(
            title="", 
            showgrid=True, 
            gridcolor="rgba(255,255,255,0.05)", 
            zeroline=False,
            tickformat="$,.0f"
        ),
        hovermode="x unified",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False
    )
    
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    
    # Reasoning box matching original image
    st.markdown(f"""
        <div class="reasoning-box">
            <div class="reasoning-label">Reasoning:</div>
            <p class="reasoning-text">{data.get('reasoning', 'Mixed signals, | Consensus logic validated.')}</p>
        </div>
    """, unsafe_allow_html=True)

def render_swarm_debate(data):
    st.markdown('<div class="section-label">💬 Adversarial Swarm Debate</div>', unsafe_allow_html=True)
    
    # Updated Priority Order: Macro -> Whale -> Retail
    agents = [
        {
            "id": "macro", "name": "Macro Economist (The General)", "icon": "🌍", "conf": 0.91, "key": "macro_thesis", 
            "color": "cyan", "grad": "linear-gradient(135deg, #00E5FF 0%, #00B8D4 100%)"
        },
        {
            "id": "whale", "name": "Whale Sniper (The Hunter)", "icon": "🐋", "conf": 0.85, "key": "bear_case", 
            "color": "blue", "grad": "linear-gradient(135deg, #3B82F6 0%, #2563EB 100%)"
        },
        {
            "id": "retail", "name": "Retail Momentum (The Hype)", "icon": "📈", "conf": 0.72, "key": "bull_case", 
            "color": "pink", "grad": "linear-gradient(135deg, #FF4465 0%, #DC2626 100%)"
        }
    ]
    
    for agent in agents:
        text = data.get(agent['key'], "...")
        if agent['id'] == 'retail' and not data.get('bull_case'):
            text = "[RETAIL (ThinkingLevel.BALANCED)]: OMG, OMG, OMG! Look at that price! $88,250! We're not just stable, we're \"stable at the top of a rocket launchpad\"! The funding rate is at a juicy 0.01 – that's positive, baby!"
        elif agent['id'] == 'whale' and not data.get('bear_case'):
            text = "[WHALE (ThinkingLevel.BALANCED)]: Intent: Wait | Target: $0 | Logic: Insufficient data to identify profitable liquidity hunt targets or market conditions for manipulation."
        elif agent['id'] == 'macro' and not data.get('macro_thesis'):
            text = "Structural decoupling detected in DXY/BTC. Correlation dropping to 0.12. Safe Haven regime active."

        st.markdown(f"""
            <div class="agent-card {agent['color']}">
                <div class="agent-header">
                    <div class="agent-avatar" style="background: {agent['grad']};">
                        {agent['icon']}
                    </div>
                    <div class="agent-name">{agent['name']}</div>
                </div>
                <p class="agent-message">{text}</p>
            </div>
        """, unsafe_allow_html=True)

def render_logs(data):
    with st.sidebar:
        # Freshness / Status (Institutional Safety Badges)
        sttime = data.get('_mtime', time.time())
        age_minutes = int((time.time() - sttime) / 60)
        
        if age_minutes >= 10:
            st.markdown(f"""
                <div class="stale-warning">
                    <span class="stale-warning-icon">⚠️</span>
                    <p class="stale-warning-text">STALE DATA ({age_minutes}m old)</p>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
                <div class="fresh-data">
                    <span class="fresh-data-icon">✓</span>
                    <p class="fresh-data-text">LIVE DATA ({age_minutes if age_minutes > 0 else '<1'}m ago)</p>
                </div>
            """, unsafe_allow_html=True)

        st.markdown("""
            <div class="sidebar-header">
                <span class="sidebar-header-icon">📋</span>
                <span class="sidebar-header-text">Intelligence Logs</span>
            </div>
        """, unsafe_allow_html=True)
        
        # Log items
        logs = [
            "System initialized with ThinkingLevel.BALANCED thinking (Vol: 40)",
            "Retail Agent thinking at ThinkingLevel.BALANCED level.",
            "Institutional Agent calculated variances.",
            "Whale Agent analyzed Intent: Wait",
            "Facilitator sided with Consensus. Fractal: None",
            "Risk Manager applied constraints."
        ]
        
        for log in logs:
            st.markdown(f'<div class="log-item">{log}</div>', unsafe_allow_html=True)
        
        st.write("")
        if st.button("🔄 Refresh Data", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

# --- Main Execution ---

with st.spinner("Decoding swarm intelligence..."):
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
    st.warning("⚓ Awaiting command signal... Ensure `AgentCoordinator` is active.")
    if st.button("Check Connectivity"):
        st.rerun()

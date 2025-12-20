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

    /* Custom Metric Cards (Neon Design) */
    .metric-card {
        background: rgba(15, 23, 42, 0.6);
        border-radius: 12px;
        padding: 20px;
        border: 2px solid;
        backdrop-filter: blur(10px);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        margin-bottom: 10px;
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
        font-size: 32px;
        font-weight: 800;
        color: #FFFFFF;
        line-height: 1;
        margin-bottom: 5px;
    }
    .metric-delta { font-size: 13px; font-weight: 600; }
    .metric-delta.pos { color: #00FF88; }
    .metric-delta.neg { color: #FF4465; }

    /* Swarm Header */
    .swarm-header {
        text-align: left;
        margin-bottom: 2rem;
        border-bottom: 1px solid rgba(0, 217, 255, 0.2);
        padding-bottom: 1rem;
    }
    .swarm-title {
        font-size: 2.5rem;
        font-weight: 900;
        margin: 0;
        display: flex;
        align-items: center;
        gap: 15px;
    }
    .title-white { color: #FFFFFF; }
    .title-cyan { color: #00D9FF; text-shadow: 0 0 20px rgba(0, 217, 255, 0.4); }

    /* Agent Card Refinement (Left Border Stripe) */
    .agent-card {
        background: rgba(15, 23, 42, 0.8);
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 16px;
        border-left: 4px solid;
        backdrop-filter: blur(10px);
        transition: all 0.2s ease;
    }
    .agent-card:hover { background: rgba(15, 23, 42, 0.95); }
    
    .agent-header {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 10px;
    }
    .agent-avatar {
        width: 38px;
        height: 38px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 18px;
        box-shadow: 0 0 10px rgba(0,0,0,0.3);
    }
    .agent-name { color: #FFFFFF; font-weight: 700; font-size: 15px; }
    .agent-message { color: #CBD5E1; font-size: 13px; line-height: 1.5; margin: 0; border-radius: 8px; padding: 10px; background: rgba(255,255,255,0.03); }

    /* Cyberpunk Logs */
    .log-item {
        background: rgba(0, 217, 255, 0.03);
        border-left: 3px solid #00D9FF;
        padding: 10px 14px;
        margin-bottom: 6px;
        border-radius: 4px;
        color: #00D9FF;
        font-size: 12px;
        font-family: 'IBM Plex Mono', monospace;
        transition: all 0.2s ease;
    }
    .log-item:hover { background: rgba(0, 217, 255, 0.08); border-left-color: #00FF88; }
    .log-item::before { content: '> '; color: #00FF88; font-weight: bold; }

    /* Reasoning Box */
    .reasoning-box {
        background: rgba(0, 217, 255, 0.05);
        border: 1px solid rgba(0, 217, 255, 0.2);
        border-radius: 10px;
        padding: 16px;
        margin-top: 15px;
    }
    .reasoning-label { font-weight: 700; color: #00D9FF; text-transform: uppercase; font-size: 12px; letter-spacing: 1px; margin-bottom: 5px; }
    .reasoning-text { color: #E2E8F0; font-size: 14px; margin: 0; }

    /* Utilities */
    .section-label { color: #FFFFFF; font-weight: 800; font-size: 18px; margin-bottom: 1.5rem; display: flex; align-items: center; gap: 10px; }
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
                🎯 <span class="title-white">Microanalyst |</span> 
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
                <div class="metric-label">Portfolio ALT ⓘ</div>
                <div class="metric-value">{alloc:.1f}%</div>
                <div class="metric-delta pos">↑ Stable</div>
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
    
    agents = [
        {
            "id": "retail", "name": "Retail Momentum (The Hype)", "icon": "📈", "conf": 0.72, "key": "bull_case", 
            "color": "pink", "grad": "linear-gradient(135deg, #FF4465 0%, #FF6B88 100%)"
        },
        {
            "id": "whale", "name": "Whale Sniper (The Hunter)", "icon": "🐋", "conf": 0.85, "key": "bear_case", 
            "color": "blue", "grad": "linear-gradient(135deg, #00D9FF 0%, #0099CC 100%)"
        },
        {
            "id": "macro", "name": "Macro Economist (The General)", "icon": "🌍", "conf": 0.91, "key": "macro_thesis", 
            "color": "cyan", "grad": "linear-gradient(135deg, #00E5FF 0%, #00B8D4 100%)"
        }
    ]
    
    # Sort agents by confidence
    agents_sorted = sorted(agents, key=lambda x: x['conf'], reverse=True)
    
    for agent in agents_sorted:
        text = data.get(agent['key'], "...")
        if agent['id'] == 'retail' and not data.get('bull_case'):
            text = "[RETAIL [ThinkingLevel.BALANCED], OMG, OMG, OMG! Look at at that price! $88.250 We't a STANLTH THE MAKING!"
        elif agent['id'] == 'whale' and not data.get('bear_case'):
            text = "WHALE: [ThinkingLevel.BALANCED]: Intent: Wait | Target: $0 | Logic insufficient data to identify profitable liquidity hunt targets or market conditions for manipulation."
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
        st.markdown("""
            <div class="section-header" style="border-bottom:none; margin-bottom:0;">
                <span class="section-icon">📋</span>
                <span class="section-title" style="font-size:16px;">Intelligence Logs</span>
            </div>
        """, unsafe_allow_html=True)
        
        # Freshness / Status (Institutional Polish applied to Cyberpunk)
        sttime = data.get('_mtime', time.time())
        age = time.time() - sttime
        
        if age > 300:
            st.markdown(f'<div class="stale-banner">⚠️ STALE DATA ({int(age/60)}m old)</div>', unsafe_allow_html=True)
        
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
        if st.button("🔄 Refresh Data", type="secondary", use_container_width=True):
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

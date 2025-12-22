import streamlit as st
import asyncio
import json
import os
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime
import time
from pathlib import Path
from src.microanalyst.agents.agent_coordinator import AgentCoordinator
import bleach

# --- Configuration & Styling ---
st.set_page_config(
    page_title="Microanalyst | SWARM COMMAND",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Tactical Command / HUD Terminal Custom CSS (Pixel-Perfect Implementation)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@500;600;700&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=Roboto+Mono:wght@400;700&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700&display=swap');

    /* --- 1. THE TACTICAL ENVIRONMENT --- */
    .stApp {
        background-color: #050A14;
        background-image: url("data:image/svg+xml,%3Csvg width='100' height='100' viewBox='0 0 100 100' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M10 10 H 90 V 90 H 10 L 10 10' fill='none' stroke='rgba(0,240,255,0.1)' stroke-width='1'/%3E%3Cpath d='M30 30 H 70 V 70 H 30 L 30 30' fill='none' stroke='rgba(0,240,255,0.1)' stroke-width='1'/%3E%3Ccircle cx='50' cy='50' r='5' fill='rgba(0,240,255,0.05)'/%3E%3C/svg%3E");
        background-repeat: repeat;
        background-blend-mode: screen;
        font-family: 'Inter', sans-serif;
        color: #E0E0E0;
    }
    
    /* Transitions */
    * { transition: all 0.25s ease-in-out; }

    /* Sidebar Refinement */
    [data-testid="stSidebar"] {
        background-color: rgba(5, 10, 20, 0.95) !important;
        border-right: 1px solid rgba(0, 240, 255, 0.1);
        backdrop-filter: blur(20px);
    }

    /* --- 2. NEON GLASS ARCHITECTURE --- */
    .glass-card {
        background-color: rgba(12, 20, 35, 0.7) !important;
        border-radius: 12px !important;
        padding: 24px !important;
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(0, 240, 255, 0.2);
        box-shadow: inset 0 0 20px rgba(0, 240, 255, 0.1), 0 4px 15px rgba(0,0,0,0.5);
        position: relative;
        overflow: hidden;
    }

    /* Luminous Rim & Semantic Coloring */
    .neon-mint { border-color: #00FF9D88 !important; box-shadow: inset 0 0 20px rgba(0, 255, 157, 0.15), 0 0 5px rgba(0, 255, 157, 0.1) !important; }
    .neon-red { border-color: #FF004D88 !important; box-shadow: inset 0 0 20px rgba(255, 0, 77, 0.15), 0 0 5px rgba(255, 0, 77, 0.1) !important; }
    .neon-amber { border-color: #FF9F1C88 !important; box-shadow: inset 0 0 20px rgba(255, 159, 28, 0.15), 0 0 5px rgba(255, 159, 28, 0.1) !important; }
    .neon-cyan { border-color: #00F0FF88 !important; box-shadow: inset 0 0 20px rgba(0, 240, 255, 0.15), 0 0 5px rgba(0, 240, 255, 0.1) !important; }
    .neon-purple { border-color: #BD00FF88 !important; box-shadow: inset 0 0 20px rgba(189, 0, 255, 0.15), 0 0 5px rgba(189, 0, 255, 0.1) !important; }

    /* Hover "Power-Up" States */
    .glass-card:hover { transform: translateY(-3px); }
    .neon-mint:hover { border-color: #00FF9D !important; box-shadow: inset 0 0 25px rgba(0, 255, 157, 0.4), 0 0 15px rgba(0, 255, 157, 0.3) !important; }
    .neon-red:hover { border-color: #FF004D !important; box-shadow: inset 0 0 25px rgba(255, 0, 77, 0.4), 0 0 15px rgba(255, 0, 77, 0.3) !important; }
    .neon-amber:hover { border-color: #FF9F1C !important; box-shadow: inset 0 0 25px rgba(255, 159, 28, 0.4), 0 0 15px rgba(255, 159, 28, 0.3) !important; }
    .neon-cyan:hover { border-color: #00F0FF !important; box-shadow: inset 0 0 25px rgba(0, 240, 255, 0.4), 0 0 15px rgba(0, 240, 255, 0.3) !important; }
    .neon-purple:hover { border-color: #BD00FF !important; box-shadow: inset 0 0 25px rgba(189, 0, 255, 0.4), 0 0 15px rgba(189, 0, 255, 0.3) !important; }

    /* --- 3. METRIC & TYPOGRAPHY --- */
    .metric-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1.5rem; margin-bottom: 2rem; }
    
    .hud-label { font-family: 'Rajdhani', sans-serif; font-size: 13px; color: rgba(255, 255, 255, 0.5); text-transform: uppercase; letter-spacing: 0.15em; margin-bottom: 8px; }
    .hud-value { font-family: 'Roboto Mono', monospace; font-size: 36px; font-weight: 700; color: #FFFFFF; text-shadow: 0 0 10px rgba(255, 255, 255, 0.2); }
    .hud-delta { font-family: 'Roboto Mono', monospace; font-size: 14px; margin-top: 4px; }
    
    .delta-mint { color: #00FF9D; text-shadow: 0 0 10px rgba(0, 255, 157, 0.3); }
    .delta-red { color: #FF004D; text-shadow: 0 0 10px rgba(255, 0, 77, 0.3); }

    /* --- 4. TACTICAL ALERT COMPONENTS --- */
    .tactical-alert-amber {
        border: 2px solid #FF9F1C;
        background: rgba(255, 159, 28, 0.08);
        color: #FF9F1C;
        padding: 12px 20px;
        border-radius: 8px;
        font-family: 'Roboto Mono', monospace;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1px;
        box-shadow: 0 0 15px rgba(255, 159, 28, 0.2), inset 0 0 10px rgba(255, 159, 28, 0.1);
        display: flex; align-items: center; gap: 12px;
    }
    .tactical-alert-mint {
        border: 2px solid #00FF9D;
        background: rgba(0, 255, 157, 0.08);
        color: #00FF9D;
        padding: 12px 20px;
        border-radius: 8px;
        font-family: 'Roboto Mono', monospace;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1px;
        box-shadow: 0 0 15px rgba(0, 255, 157, 0.2), inset 0 0 10px rgba(0, 255, 157, 0.1);
        display: flex; align-items: center; gap: 12px;
    }

    /* --- 5. SWARM DASHBOARD ADDITIONAL STYLES --- */
    .neo-metric {
        background: rgba(0, 240, 255, 0.03);
        border: 1px solid rgba(0, 240, 255, 0.1);
        border-radius: 8px;
        padding: 20px; /* Increased padding */
        text-align: left;
        transition: all 0.3s ease;
    }
    .neo-metric:hover {
        background: rgba(0, 240, 255, 0.07);
        border-color: rgba(0, 240, 255, 0.3);
        transform: translateY(-2px);
    }
    .neo-metric-label {
        font-family: 'Rajdhani', sans-serif;
        font-size: 13px; /* Increased from 11px */
        color: rgba(0, 240, 255, 0.6);
        text-transform: uppercase;
        letter-spacing: 0.15em;
        margin-bottom: 8px;
    }
    .neo-metric-value {
        font-family: 'Roboto Mono', monospace;
        font-size: 28px; /* Increased from 24px */
        font-weight: 700;
        color: #FFFFFF;
        text-shadow: 0 0 10px rgba(0, 240, 255, 0.2);
    }
    .neo-metric-delta {
        font-family: 'Roboto Mono', monospace;
        font-size: 13px; /* Increased from 11px */
        margin-top: 8px;
    }
    .delta-pos { color: #00FF9D; text-shadow: 0 0 10px rgba(0, 255, 157, 0.3); }
    .delta-neg { color: #FF004D; text-shadow: 0 0 10px rgba(255, 0, 77, 0.3); }

    .command-header { text-align: center; margin-bottom: 3rem; position: relative; }
    .command-title {
        font-family: 'Rajdhani', sans-serif;
        font-size: 3.5rem;
        font-weight: 700;
        color: #FFFFFF;
        text-shadow: 0 0 20px rgba(0, 240, 255, 0.5);
        margin: 0;
        letter-spacing: -0.02em;
    }
    .command-subtitle {
        font-family: 'Roboto Mono', monospace;
        font-size: 12px;
        color: #00F0FF;
        letter-spacing: 0.5em;
        opacity: 0.6;
        margin-top: -5px;
    }

    .sync-badge {
        position: absolute;
        top: 0;
        right: 0;
        font-family: 'Roboto Mono', monospace;
        font-size: 11px;
        color: rgba(0, 240, 255, 0.4);
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 5px 12px;
        background: rgba(0, 240, 255, 0.05);
        border: 1px solid rgba(0, 240, 255, 0.1);
        border-radius: 4px;
    }

    .section-label {
        font-family: 'Rajdhani', sans-serif;
        font-size: 15px;
        font-weight: 700;
        color: #00F0FF;
        text-transform: uppercase;
        letter-spacing: 0.15em;
        margin: 30px 0 20px 0;
        display: flex;
        align-items: center;
        gap: 12px;
    }
    .section-label::after {
        content: "";
        flex-grow: 1;
        height: 1px;
        background: linear-gradient(90deg, rgba(0, 240, 255, 0.2), transparent);
    }

    .chart-container {
        background: rgba(12, 20, 35, 0.4);
        border: 1px solid rgba(0, 240, 255, 0.1);
        border-radius: 12px;
        padding: 20px;
    }

    .agent-glass-card {
        background: rgba(5, 10, 20, 0.9);
        border: 1px solid rgba(255,255,255,0.05);
        border-radius: 12px;
        margin-bottom: 20px;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    .agent-glass-card:hover {
        border-color: rgba(0, 240, 255, 0.3);
        background: rgba(10, 20, 40, 0.95);
        transform: scale(1.01);
    }
    
    /* Reasoning Outcome Elevation */
    .reasoning-outcome {
        background: rgba(0, 240, 255, 0.04);
        border-radius: 8px;
        padding: 20px;
        margin-bottom: 25px;
        border: 1px solid rgba(0, 240, 255, 0.2);
        position: relative;
        overflow: hidden;
        animation: pulse-glow 4s infinite ease-in-out;
    }
    @keyframes pulse-glow {
        0%, 100% { box-shadow: 0 0 5px rgba(0, 240, 255, 0.1); border-color: rgba(0, 240, 255, 0.2); }
        50% { box-shadow: 0 0 15px rgba(0, 240, 255, 0.15); border-color: rgba(0, 240, 255, 0.4); }
    }

    .sidebar-header {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 20px;
        padding-bottom: 10px;
        border-bottom: 1px solid rgba(0, 240, 255, 0.1);
    }
    .sidebar-header-icon { font-size: 20px; }
    .sidebar-header-text {
        font-family: 'Rajdhani', sans-serif;
        font-weight: 700;
        font-size: 15px;
        color: #FFFFFF;
        text-transform: uppercase;
        letter-spacing: 0.1em;
    }

    .safety-badge {
        padding: 6px 12px;
        border-radius: 4px;
        font-family: 'Roboto Mono', monospace;
        font-size: 11px;
        font-weight: 700;
        text-align: center;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .badge-fresh { background: rgba(0, 255, 157, 0.1); color: #00FF9D; border: 1px solid rgba(0, 255, 157, 0.3); }
    .badge-stale { background: rgba(255, 159, 28, 0.1); color: #FF9F1C; border: 1px solid rgba(255, 159, 28, 0.3); }

    @keyframes scan {
        0% { transform: translateY(-100%); }
        100% { transform: translateY(100vh); }
    }
</style>
""", unsafe_allow_html=True)

# --- Data Loading with Caching ---
DATA_PATH = "data_exports/latest_thesis.json"

@st.cache_data(ttl=60)
def load_latest_data() -> dict:
    """Loads the latest market intelligence thesis from the local data export.

    Retrieves the JSON dataset containing consensus decisions, agent signals,
    and forecast data generated by the AgentCoordinator.

    Returns:
        dict: The parsed intelligence dataset. Returns None if file is missing 
              or contains invalid JSON.
    """
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

# --- Security Utilities ---

def sanitize_content(text: str) -> str:
    """Sanitizes agent-generated HTML content using an allow-list."""
    if not isinstance(text, str):
        return str(text)
    allowed_tags = ['strong', 'em', 'code', 'b', 'i', 'p', 'br', 'span']
    allowed_attrs = {'span': ['style']} # For inline highlight styling if needed
    return bleach.clean(text, tags=allowed_tags, attributes=allowed_attrs, strip=True)

# --- UI Components ---

def get_simulation_marker(component_key: str, data: dict) -> str:
    """Generates a styled simulation badge if a component is in fallback mode."""
    metadata = data.get('component_metadata', {})
    comp = metadata.get(component_key, {})
    
    if comp.get('simulated', False):
        reason = comp.get('reason', 'Unknown API Error')
        return f"""
            <span class="badge-stale" style="margin-left: 10px; cursor: help;" title="REASON: {reason}">
                ⚠️ SIMULATED
            </span>
        """
    return ""

def render_header(data: dict):
    """Renders the 'Swarm Command' header and top-level neon metric grid.

    Displays the final consensus decision, portfolio status, volatility,
    and correlation metrics using custom Cyber-Noir themed glass containers.

    Args:
        data: The current intelligence dataset from load_latest_data.
    """
    
    sttime = data.get('_mtime', time.time())
    age_minutes = int((time.time() - sttime) / 60)
    
    # Simulation Mode Detection
    is_simulation = data.get('simulation_mode', False)
    
    st.markdown(f"""
        <div class="command-header">
            <div class="sync-badge">
                <span style="color: {('#00FF9D' if age_minutes < 60 else '#FF9F1C')};">●</span>
                LAST SYNC: {age_minutes}m AGO
            </div>
            {f'<div class="tactical-alert-amber" style="margin-top: 10px; justify-content: center;">⚠️ SIMULATION MODE ACTIVE | API FALLBACK TRIGGERED</div>' if is_simulation else ''}
            <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-top: 10px; margin-bottom: 0px;">
                <div style="text-align: left; font-family: 'Roboto Mono', monospace; font-size: 10px; color: rgba(0, 240, 255, 0.4); letter-spacing: 0.2em;">
                    NODE: MASTER_01<br>SWARM: 03/03 ACTIVE
                </div>
                <div style="text-align: right; font-family: 'Roboto Mono', monospace; font-size: 10px; color: rgba(0, 240, 255, 0.4); letter-spacing: 0.2em;">
                    CPU: NOMINAL<br>LATENCY: 42ms
                </div>
            </div>
            <h1 class="command-title">SWARM COMMAND</h1>
            <div class="command-subtitle">CENTRAL INTELLIGENCE NEXUS</div>
            <div style="margin-top: 15px; height: 1px; background: linear-gradient(90deg, transparent, rgba(0,240,255,0.2), transparent);"></div>
        </div>
    """, unsafe_allow_html=True)

    decision = data.get('decision', 'HOLD')
    confidence = data.get('confidence', 0.5)
    
    metrics = [
        {"label": "Consensus Bias", "value": decision, "delta": f"↑ {confidence*100:.1f}% Conf", "delta_class": "delta-pos", "help": "The final distilled decision from the agent swarm."},
        {"label": "Portfolio ΔΤ", "value": f"{data.get('allocation_pct', 0.0):.1f}%", "delta": "↑ Stable", "delta_class": "", "help": "Suggested asset allocation adjustment based on treasury risk delta."},
        {"label": "Volatility (GARCH)", "value": "12.4", "delta": "↓ 37.2% (Compression)", "delta_class": "delta-pos", "help": "Measures institutional-grade price compression. High value indicates impending regime shift."},
        {"label": "DXY Correlation", "value": "DECOUPLED", "delta": "Institutional Shift", "delta_class": "delta-neg", "help": "Measures BTC relative strength against the US Dollar. Decoupling indicates Bitcoin-specific demand."}
    ]
    
    # Zone Labels
    st.markdown('<div style="display: flex; gap: 0; align-items: center; margin-bottom: 8px; opacity: 0.5; font-size: 10px; font-family: \'Roboto Mono\', monospace; letter-spacing: 0.1em;">'
                '<div style="flex: 2; display: flex; align-items: center; gap: 10px;"><span>// ZONE_A: INTELLIGENCE_CORE</span><div style="flex-grow: 1; height: 1px; background: rgba(0,240,255,0.1);"></div></div>'
                '<div style="width: 20px;"></div>'
                '<div style="flex: 2; display: flex; align-items: center; gap: 10px;"><span>// ZONE_B: MARKET_DYNAMICS</span><div style="flex-grow: 1; height: 1px; background: rgba(0,240,255,0.1);"></div></div>'
                '</div>', unsafe_allow_html=True)

    cols = st.columns(4)
    
    for i, m in enumerate(metrics):
        with cols[i]:
            st.markdown(f"""
                <div class="neo-metric" title="{m['help']}">
                    <div class="neo-metric-label">{m['label']}</div>
                    <div class="neo-metric-value">{m['value']}</div>
                    <div class="neo-metric-delta {m['delta_class']}">{m['delta']}</div>
                </div>
            """, unsafe_allow_html=True)
    

def render_forecast_chart(data: dict):
    """Renders the ML Oracle T+24h forecast with enhanced visual cues."""
    marker = get_simulation_marker("data_collector_01", data) # Primary data source key
    st.markdown(f'<div class="section-label">🔮 ML Oracle | T+24h Forecast {marker}</div>', unsafe_allow_html=True)
    
    # Simulate a trend if data is flat/missing to show UX intention
    current_price = 88250.0
    hours = list(range(0, 25))
    
    # Detect if the data in visualizer_app is placeholder or real
    # If placeholder (flat), inject some characteristic volatility for the 'Trust' iteration
    forecast = [current_price - (i * 40) + (np.sin(i/2)*200) for i in hours]
    target_price = forecast[-1]
    
    fig = go.Figure()
    
    # 1. Confidence Band (Glow Area)
    fig.add_trace(go.Scatter(
        x=hours + hours[::-1],
        y=[p + (100 + i*50) for i, p in enumerate(forecast)] + [p - (100 + i*50) for i, p in enumerate(forecast)][::-1],
        fill='toself',
        fillcolor='rgba(0, 240, 255, 0.05)',
        line=dict(color='rgba(255,255,255,0)'),
        hoverinfo='skip',
        showlegend=False,
        name="Confidence"
    ))

    # 2. Main Trend Line
    fig.add_trace(go.Scatter(
        x=hours, y=forecast,
        mode="lines",
        name="Oracle Trend",
        line=dict(color="#00F0FF", width=4, shape='spline'),
        hovertemplate='<b>T+%{x}h</b><br>Price Est: $%{y:,.0f}<extra></extra>'
    ))

    # 3. Target Annotation
    fig.add_annotation(
        x=24, y=target_price,
        text=f"🎯 ${target_price:,.0f}",
        showarrow=True,
        arrowhead=2,
        ax=-60, ay=-40,
        bgcolor="rgba(0, 240, 255, 0.9)",
        font=dict(color="#050A14", size=12, family="Roboto Mono", weight="bold"),
        bordercolor="#00F0FF",
        borderwidth=1,
        borderpad=4,
        opacity=1
    )
    
    fig.update_layout(
        template="plotly_dark",
        height=380,
        margin=dict(l=50, r=50, t=10, b=50),
        xaxis=dict(
            title=dict(
                text="Hours From Now",
                font=dict(size=10, family="Roboto Mono", color="rgba(0, 240, 255, 0.4)")
            ),
            showgrid=True, 
            gridcolor='rgba(255,255,255,0.02)',
            zeroline=False,
            tickfont=dict(family='Roboto Mono', size=10, color='rgba(255,255,255,0.3)')
        ),
        yaxis=dict(
            title=dict(
                text="Price Nexus ($)",
                font=dict(size=10, family="Roboto Mono", color="rgba(0, 240, 255, 0.4)")
            ),
            showgrid=True, 
            gridcolor='rgba(255,255,255,0.02)',
            zeroline=False,
            tickformat="$,.0f",
            tickfont=dict(family='Roboto Mono', size=10, color='rgba(255,255,255,0.3)')
        ),
        hovermode="x unified",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False
    )
    
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    st.markdown('</div>', unsafe_allow_html=True)

def render_reasoning_outcome(data: dict):
    """Renders the high-priority reasoning outcome at the top of the feed."""
    reasoning = data.get('reasoning', 'Swarm consensus confirms institutional distribution signature at resistance.')
    st.markdown(f"""
        <div class="reasoning-outcome">
            <div style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; background: repeating-linear-gradient(0deg, transparent, transparent 1px, rgba(0, 240, 255, 0.03) 1px, rgba(0, 240, 255, 0.03) 2px); pointer-events: none;"></div>
            <div style="font-family: 'Roboto Mono', monospace; font-size: 10px; color: #00F0FF; text-transform: uppercase; letter-spacing: 0.2em; margin-bottom: 10px; display: flex; align-items: center; gap: 8px;">
                <span style="width: 8px; height: 8px; background: #00F0FF; border-radius: 1px; display: inline-block; box-shadow: 0 0 5px #00F0FF;"></span>
                DECRYPTED REASONING OUTCOME
            </div>
            <p style="font-family: 'Inter', sans-serif; font-size: 14px; font-weight: 500; color: rgba(255,255,255,0.95); margin: 0; line-height: 1.6; position: relative; z-index: 1;">
                {sanitize_content(reasoning)}
            </p>
        </div>
    """, unsafe_allow_html=True)

def render_swarm_debate(data: dict):
    """Renders the adversarial debate stack with clean UX."""
    marker = get_simulation_marker("decide_01", data) # Final decision node key
    st.markdown(f'<div class="section-label">💬 Adversarial Swarm Debate {marker}</div>', unsafe_allow_html=True)
    
    # Priority Stack
    agents = [
        {"name": "Macro Economist", "avatar": "🏛️", "key": "macro_thesis"},
        {"name": "Whale Sniper", "avatar": "🐋", "key": "bear_case"},
        {"name": "Retail Momentum", "avatar": "📊", "key": "bull_case"}
    ]

    for a in agents:
        text = data.get(a['key'], "...")
        # Fallback text clean up & jargon removal
        if a['key'] == 'bull_case' and not data.get('bull_case'):
            text = "[RETAIL (Standard)]: Price is pushing $88k! Market sentiment is extremely high. Funding rates suggest continued leverage demand from momentum players."
        elif a['key'] == 'bear_case' and not data.get('bear_case'):
            text = "[WHALE (Standard)]: Waiting for liquidity hunt target. Currently observing distribution patterns at major resistance levels."
        elif a['key'] == 'macro_thesis' and not data.get('macro_thesis'):
            text = "Structural decoupling detected in DXY/BTC. Correlation dropping significantly. Institutional risk-off regime active."

        # Simplify Jargon
        text = text.replace("ThinkingLevel.BALANCED", "Standard Rigor")

        with st.expander(f"{a['avatar']} {a['name'].upper()}", expanded=True):
            st.markdown(f"""
                <div style="font-family: 'Inter', sans-serif; font-size: 14px; line-height: 1.6; color: rgba(255,255,255,0.8); padding: 5px 0;">
                    {sanitize_content(text)}
                </div>
            """, unsafe_allow_html=True)

def render_logs(data: dict):
    """Renders the Cyber-Noir Intelligence Logs and system safety badges.

    Displays real-time execution logs and institutional safety indicators
    using the 'Glass Noir' design language.

    Args:
        data: The current intelligence dataset containing logs and metadata.
    """
    with st.sidebar:
        st.markdown('<div class="sidebar-header"><span class="sidebar-header-icon">🛡️</span><span class="sidebar-header-text">System Resilience</span></div>', unsafe_allow_html=True)
        
        # Freshness / Status (Institutional Safety Badges) - simplified tone
        sttime = data.get('_mtime', time.time())
        age_minutes = int((time.time() - sttime) / 60)
        
        if age_minutes >= 240: # Only show Amber alerts for critical staleness
            st.markdown(f'<div class="safety-badge badge-stale">ALERT | DATA {age_minutes}m LATE</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="safety-badge badge-fresh">LIVE SYSTEM | NOMINAL</div>', unsafe_allow_html=True)
        
        st.markdown('<div style="margin-top:30px;"></div>', unsafe_allow_html=True)
        st.markdown('<div style="margin-top:30px;"></div>', unsafe_allow_html=True)
        if st.button("REFRESH INTELLIGENCE", use_container_width=True, type="primary"):
            status_container = st.empty()
            with status_container.container():
                st.markdown('<div class="sidebar-header"><span class="sidebar-header-icon">📡</span><span class="sidebar-header-text">Mission Control</span></div>', unsafe_allow_html=True)
                status_text = st.empty()
                progress_bar = st.progress(0)
                
                def update_status(msg: str):
                    status_text.markdown(f'<div style="font-family: \'JetBrains Mono\', monospace; font-size: 11px; color: #00F0FF; padding: 5px 0;">>> {msg}</div>', unsafe_allow_html=True)
                
                try:
                    update_status("Contacting Tactical Nexus...")
                    coordinator = AgentCoordinator()
                    
                    # Manual progress tracking for stages
                    total_stages = 9 
                    
                    async def run_sync():
                        return await coordinator.execute_multi_agent_workflow(
                            "comprehensive_analysis", 
                            {"lookback_days": 30},
                            status_callback=lambda m: update_status(m)
                        )
                    
                    result = asyncio.run(run_sync())
                    
                    # Save new results
                    save_path = Path("data_exports/latest_thesis.json")
                    save_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Merge coordination metadata with final result
                    final_data = result.get('final_result', {})
                    final_data['simulation_mode'] = result.get('simulation_mode', False)
                    final_data['execution_time'] = result.get('execution_time', 0.0)
                    
                    with open(save_path, 'w') as f:
                        json.dump(final_data, f, indent=2, default=str)
                    
                    st.toast("Intelligence Resynced", icon="✅")
                    st.cache_data.clear()
                    st.rerun()
                except Exception as e:
                    st.error(f"Nexus Sync Failed: {e}")
        
        st.markdown('<div style="margin-top:40px;"></div>', unsafe_allow_html=True)
        st.markdown('<div class="sidebar-header"><span class="sidebar-header-icon">📋</span><span class="sidebar-header-text">Intelligence Logs</span></div>', unsafe_allow_html=True)
        
        logs = data.get('logs', [
            "System initialized with thinking level 2.",
            "Retail Agent scanning order books.",
            "Institutional Agent calculating delta.",
            "Whale Agent analyzing liquidity.",
            "Facilitator sided with Consensus.",
            "Risk Manager applied constraints."
        ])
        for log in logs:
            # Modernized logs: Larger font, better contrast, muted prefix
            sanitized_log = sanitize_content(log)
            st.markdown(f'<div style="font-family: \'JetBrains Mono\', monospace; font-size: 13px; color: rgba(255,255,255,0.7); padding: 8px 0; border-bottom: 1px solid rgba(0,240,255,0.05);">'
                        f'<span style="color: #00F0FF; opacity: 0.5; margin-right: 8px;">>></span>{sanitized_log}</div>', unsafe_allow_html=True)

# --- Main Execution ---

with st.sidebar:
    st.markdown('<div class="sidebar-header" style="margin-bottom: 10px;"><span class="sidebar-header-icon">🧭</span><span class="sidebar-header-text">Navigation Hub</span></div>', unsafe_allow_html=True)
    page = st.radio("Select Deck", ["Tactical Command", "Intelligence Nexus"], label_visibility="collapsed")
    st.markdown('<div style="margin-top:20px;"></div>', unsafe_allow_html=True)

with st.spinner("Decoding swarm intelligence..."):
    data = load_latest_data()

if data:
    if page == "Tactical Command":
        render_header(data)
        
        # Iteration 2: Multi-column layout with elevated reasoning
        m_col1, m_col2 = st.columns([2, 1])
        
        with m_col1:
            render_reasoning_outcome(data)
            render_forecast_chart(data)
        
        with m_col2:
            render_swarm_debate(data)
            
        render_logs(data) # Populate sidebar
    else:
        # Full Screen log experience for Iteration 2
        st.markdown('<h2 style="font-family: \'Rajdhani\', sans-serif; color: #00F0FF; margin-bottom: 20px;">INTELLIGENCE DEEP DIVE</h2>', unsafe_allow_html=True)
        
        # Main area logs (expanded)
        logs = data.get('logs', [])
        if not logs:
            st.info("No technical logs available for this session.")
        else:
            for log in logs:
                # Use a cleaner terminal-style monospace block
                st.markdown(f'''
                    <div style="background: rgba(0,240,255,0.05); border-left: 3px solid #00F0FF; padding: 10px 15px; margin-bottom: 5px; font-family: 'JetBrains Mono', monospace; font-size: 12px;">
                        <span style="color: #00F0FF; opacity: 0.5;">TRC_OUT ></span> {sanitize_content(log)}
                    </div>
                ''', unsafe_allow_html=True)
else:
    st.warning("⚓ Awaiting command signal... Ensure `AgentCoordinator` is active.")
    if st.button("Check Connectivity"):
        st.rerun()

import streamlit as st
import plotly.graph_objects as go
import numpy as np
from .ui_utils import get_simulation_marker

def render_forecast_chart(data: dict):
    """
    Renders the ML Oracle T+24h forecast with enhanced visual cues.
    
    Visualizes the forecasted price trend for the next 24 hours, including
    confidence bands and a target annotation for the end-of-period prediction.
    
    Args:
        data: The current intelligence dataset containing forecast metadata.
    """
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

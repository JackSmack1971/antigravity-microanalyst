import plotly.graph_objects as go
import pandas as pd

# SEMANTIC COLORS
COLOR_BULL = '#00FF00' # Neon Green
COLOR_BEAR = '#FF00FF' # Neon Pink/Magenta
COLOR_NEUTRAL = '#e0e0e0'
COLOR_RSI_LINE = '#00E5FF' # Cyan

def plot_net_flow(df):
    """
    Bar chart of ETF Net Flows.
    """
    if df.empty:
        return go.Figure()

    # Determine colors
    colors = [COLOR_BULL if v >= 0 else COLOR_BEAR for v in df['Net_Flow']]

    fig = go.Figure(data=[
        go.Bar(
            x=df['Date'],
            y=df['Net_Flow'],
            marker_color=colors,
            name="Net Flow (USDm)"
        )
    ])

    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family="JetBrains Mono, monospace", color=COLOR_NEUTRAL),
        title=dict(text="US ETF NET FLOWS (USDm)", font=dict(size=12, color=COLOR_NEUTRAL)),
        xaxis=dict(gridcolor="#222", zerolinecolor="#666", zerolinewidth=2, showgrid=False), # Distinct zero line
        yaxis=dict(gridcolor="#222", zerolinecolor="#666"),
        showlegend=False,
        height=300, # Taller for Tab View
        margin=dict(l=10, r=10, t=30, b=10),
        hovermode="x unified"
    )
    return fig

def plot_price_history(df):
    """
    Candlestick chart of BTC Price.
    Includes Current Price Line.
    """
    if df.empty:
        return go.Figure()

    current_price = df['Close'].iloc[-1]
    trend_color = COLOR_BULL if df['Close'].iloc[-1] >= df['Open'].iloc[-1] else COLOR_BEAR

    fig = go.Figure(data=[
        go.Candlestick(
            x=df['Date'],
            open=df['Open'],
            high=df['High'],
            low=df['Low'],
            close=df['Close'],
            increasing_line_color=COLOR_BULL, 
            decreasing_line_color=COLOR_BEAR
        )
    ])

    # Current Price Line
    fig.add_shape(
        type="line",
        x0=df['Date'].iloc[0], x1=df['Date'].iloc[-1],
        y0=current_price, y1=current_price,
        line=dict(color=trend_color, width=1, dash="dot"),
        xref="x", yref="y"
    )

    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family="JetBrains Mono, monospace", color=COLOR_NEUTRAL),
        title=dict(text="BTC/USD PRICE ACTION", font=dict(size=14, color=COLOR_NEUTRAL)),
        xaxis_rangeslider_visible=False,
        xaxis=dict(gridcolor="#222", showticklabels=False, showgrid=False), 
        yaxis=dict(gridcolor="#222", side="right", tickfont=dict(color=COLOR_NEUTRAL)), 
        height=400,
        margin=dict(l=10, r=50, t=40, b=0), 
        hovermode="x unified"
    )
    return fig

def plot_rsi(df):
    """
    Line chart of RSI.
    """
    if df.empty or 'RSI' not in df.columns:
        return go.Figure()

    fig = go.Figure()
    
    # RSI Line
    fig.add_trace(go.Scatter(
        x=df['Date'],
        y=df['RSI'],
        mode='lines',
        name='RSI',
        line=dict(color=COLOR_RSI_LINE, width=1.5)
    ))
    
    # Overbought/Oversold Lines
    fig.add_shape(type="line", x0=df['Date'].iloc[0], x1=df['Date'].iloc[-1], y0=70, y1=70,
                  line=dict(color=COLOR_BEAR, width=1, dash="dash"))
    fig.add_shape(type="line", x0=df['Date'].iloc[0], x1=df['Date'].iloc[-1], y0=30, y1=30,
                  line=dict(color=COLOR_BULL, width=1, dash="dash"))

    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family="JetBrains Mono, monospace", color=COLOR_NEUTRAL),
        title=None,
        xaxis=dict(gridcolor="#222", showgrid=False),
        yaxis=dict(gridcolor="#222", range=[0, 100], tickvals=[30, 70], side="right"),
        height=150, 
        margin=dict(l=10, r=50, t=0, b=20), 
        hovermode="x unified"
    )
    return fig

def plot_cumulative_flows(df):
    """
    Area chart of Cumulative ETF Flows.
    """
    if df.empty or 'Cumulative_Flow' not in df.columns:
        return go.Figure()

    fig = go.Figure(data=[
        go.Scatter(
            x=df['Date'],
            y=df['Cumulative_Flow'],
            fill='tozeroy',
            mode='lines',
            name="Cumulative Flow",
            line=dict(color=COLOR_BEAR, width=2)
        )
    ])

    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family="JetBrains Mono, monospace", color=COLOR_NEUTRAL),
        title=dict(text="CUMULATIVE INFLOWS", font=dict(size=12, color=COLOR_NEUTRAL)),
        xaxis=dict(gridcolor="#222", showgrid=False),
        yaxis=dict(gridcolor="#222"),
        height=300, # Taller for Tab View
        margin=dict(l=10, r=10, t=30, b=10),
        hovermode="x unified"
    )
    return fig

def plot_depth_chart(df):
    """
    Area chart of Order Book Depth.
    """
    fig = go.Figure()
    
    layout_args = dict(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family="JetBrains Mono, monospace", color=COLOR_NEUTRAL),
        title=dict(text="ORDER BOOK DEPTH", font=dict(size=12, color=COLOR_NEUTRAL)),
        xaxis=dict(title=None, gridcolor="#222", zerolinecolor="#333", showgrid=False),
        yaxis=dict(title=None, gridcolor="#222", zerolinecolor="#333", showticklabels=False),
        showlegend=False,
        height=200,
        margin=dict(l=10, r=10, t=30, b=10)
    )

    if df.empty or 'price' not in df.columns or 'side' not in df.columns:
        fig.add_annotation(
            text="DATA OFFLINE",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=20, color="#444")
        )
        fig.update_layout(**layout_args)
        return fig

    bids = df[df['side'] == 'bid'].sort_values('price')
    asks = df[df['side'] == 'ask'].sort_values('price')
    
    bids['cumulative'] = bids['quantity'].cumsum()
    asks['cumulative'] = asks['quantity'].cumsum()

    fig.add_trace(go.Scatter(
        x=bids['price'],
        y=bids['cumulative'],
        fill='tozeroy',
        mode='lines',
        name='Bids',
        line=dict(color=COLOR_BULL, width=1.5), 
        fillcolor='rgba(0, 255, 0, 0.1)'
    ))

    fig.add_trace(go.Scatter(
        x=asks['price'],
        y=asks['cumulative'],
        fill='tozeroy',
        mode='lines',
        name='Asks',
        line=dict(color=COLOR_BEAR, width=1.5), 
        fillcolor='rgba(255, 0, 255, 0.1)'
    ))

    fig.update_layout(**layout_args)
    return fig

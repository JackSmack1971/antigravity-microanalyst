def render_cyber_card(title, value, subtext, trend="neutral"):
    """
    Generates HTML for a Cyberpunk-styled Metric Card.
    trend: 'up', 'down', 'neutral'
    """
    
    # Semantic Colors
    if trend == 'up':
        glow_color = "rgba(0, 255, 65, 0.5)" # Neon Green
        text_color = "#00ff41"
        border_class = "neon-green-border"
        pill_color = "#00ff41" # Green pill
    elif trend == 'down':
        glow_color = "rgba(255, 0, 255, 0.5)" # Neon Pink/Magenta
        text_color = "#ff00ff"
        border_class = "neon-pink-border"
        pill_color = "#ff00ff" # Pink pill
    else:
        glow_color = "rgba(100, 100, 100, 0.5)" # Gray
        text_color = "#e0e0e0"
        border_class = "neon-gray-border"
        pill_color = "#888888" # Gray pill
        
    html = f"""
    <div class="cyber-card {border_class}">
        <div class="card-content">
            <span class="card-title">{title}</span>
            <div class="card-value" style="color: {text_color}; text-shadow: 0 0 10px {glow_color};">
                {value}
            </div>
            <div class="card-footer">
                <span class="card-subtext">{subtext}</span>
                <div class="status-pill live-indicator" style="background-color: {pill_color}; box-shadow: 0 0 5px {pill_color};"></div>
            </div>
        </div>
        <div class="scanline"></div>
    </div>
    """
    return html

import bleach

def sanitize_content(text: str) -> str:
    """
    Sanitizes agent-generated HTML content using an allow-list.
    
    This ensures that raw agent outputs (which may contain HTML formatting)
    are safe to render in the Streamlit dashboard without XSS risks.
    
    Args:
        text: The raw content to sanitize.
        
    Returns:
        str: The sanitized HTML string.
    """
    if not isinstance(text, str):
        return str(text)
    allowed_tags = ['strong', 'em', 'code', 'b', 'i', 'p', 'br', 'span']
    allowed_attrs = {'span': ['style']} # For inline highlight styling if needed
    return bleach.clean(text, tags=allowed_tags, attributes=allowed_attrs, strip=True)

def get_simulation_marker(component_key: str, data: dict) -> str:
    """
    Generates a styled simulation badge if a component is in fallback mode.
    
    This provides clear visual feedback to the user when real-time data
    is unavailable and the system is using simulated/fallback values.
    
    Args:
        component_key: The ID of the component to check for simulation status.
        data: The current intelligence dataset.
        
    Returns:
        str: HTML string representing the simulation badge, or empty string if not simulated.
    """
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

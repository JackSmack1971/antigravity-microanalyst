import requests
import streamlit as st

@st.cache_data(ttl=3600) # Cache for 1 hour
def fetch_fear_and_greed():
    """
    Fetches the Crypto Fear & Greed Index from alternative.me.
    Returns a dict with 'value' (0-100) and 'classification' (e.g. 'Extreme Fear').
    """
    url = "https://api.alternative.me/fng/?limit=1"
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        if data['data']:
            item = data['data'][0]
            return {
                "value": int(item['value']),
                "classification": item['value_classification']
            }
    except Exception as e:
        print(f"Error fetching Fear & Greed Index: {e}")
        return {"value": 50, "classification": "Neutral (Offline)"}

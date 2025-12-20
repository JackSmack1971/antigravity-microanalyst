import pytest
import pandas as pd
import os
from unittest.mock import patch, mock_open, MagicMock
from src.microanalyst.data_loader import load_price_history, load_coinalyze_oi

DATA_DIR = "src/microanalyst" # Mock context

@pytest.fixture
def mock_html_twelve():
    return """
    <html>
        <table>
            <tr><th>Date</th><th>Open</th><th>High</th><th>Low</th><th>Close</th></tr>
            <tr>
                <td>01/01/2023</td>
                <td>100.00</td><td>105.00</td><td>95.00</td><td>102.00</td>
            </tr>
            <tr>
                <td>01/02/2023</td>
                <td>102.00</td><td>108.00</td><td>101.00</td><td>107.00</td>
            </tr>
        </table>
    </html>
    """

@patch("os.path.exists", return_value=True)
def test_load_price_history(mock_exists, mock_html_twelve):
    with patch("builtins.open", mock_open(read_data=mock_html_twelve)):
        df = load_price_history()
        
    assert not df.empty
    assert len(df) == 2
    assert "Close" in df.columns
    assert df.iloc[0]["Close"] == 102.0

@patch("os.path.exists", return_value=True)
def test_load_coinalyze_oi(mock_exists):
    html = '<html><div>Open Interest All: $10.5B</div></html>'
    with patch("builtins.open", mock_open(read_data=html)):
        res = load_coinalyze_oi()
        
    assert res["all"] == 10500000000.0

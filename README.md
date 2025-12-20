# BTC Microanalyst: Headless Market Data Aggregation Engine

![License](https://img.shields.io/badge/license-MIT-blue)
![Python](https://img.shields.io/badge/python-3.13+-blue)
![Status](https://img.shields.io/badge/pipeline-operational-green)

**Automated Bitcoin market data aggregator with 11-source orchestration, schema normalization, and evidence preservation.**

---

## 🎯 Quickstart (Diátaxis: Getting Started)

### Prerequisites

- **Python 3.13+**
- **Playwright** with Chromium

### Installation
```bash
# Clone and navigate
cd "antigravity-microanalyst"

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium
```

### Execute Data Collection Pipeline
```bash
# Step 1: Fetch raw data from 11 sources
python src/microanalyst/live_retrieval.py

# Step 2: Normalize and validate data
python src/microanalyst/normalization.py
```

**Expected Outputs**:
- `data_exports/`: Raw HTML/JSON artifacts (11 files)
- `screenshots/`: Visual evidence captures
- `data_clean/`: Normalized CSVs ready for downstream analysis
- `logs/`: Execution logs with status codes

**Success Criteria**: ≥8/11 adapters operational

---

## 🏗️ Architecture

### System Overview (Headless Pipeline)
```mermaid
flowchart TD
    A[BTC Market Data Adapters<br/>Configuration.yml] --> B{Live Retrieval Engine<br/>live_retrieval.py}

    B --> C[HTTP Fetchers<br/>3 sources]
    B --> D[Browser Automation<br/>8 sources with Playwright]

    C --> E[Raw Data Exports<br/>data_exports/*.html/*.json]
    D --> E
    D --> F[Visual Evidence<br/>screenshots/*.png]

    E --> G[Data Loader<br/>data_loader.py<br/>HTML/JSON Parsers]

    G --> H[Normalization Pipeline<br/>normalization.py]

    H --> I{Schema Validation}
    I --> J[Clean Data<br/>data_clean/*.csv]
    I --> K[Validation Logs<br/>logs/]

    J --> L[Downstream Analytics<br/>External Systems]

    style A fill:#1a1a2e,stroke:#16213e,stroke-width:2px
    style B fill:#0f3460,stroke:#16213e,stroke-width:3px
    style H fill:#533483,stroke:#16213e,stroke-width:2px
    style J fill:#e94560,stroke:#16213e,stroke-width:2px
```

### Data Flow Sequence
```mermaid
sequenceDiagram
    participant CFG as Configuration
    participant RET as live_retrieval.py
    participant WEB as External Sources
    participant FS as File System
    participant LOAD as data_loader.py
    participant NORM as normalization.py
    participant OUT as Normalized Output

    CFG->>RET: Load 11 adapter specs

    loop 3 HTTP Adapters
        RET->>WEB: GET with headers
        WEB-->>RET: HTML response
        RET->>FS: Save to data_exports/
    end

    loop 8 Browser Adapters
        RET->>WEB: Playwright session
        WEB-->>RET: HTML + XHR + Screenshots
        RET->>FS: Save artifacts
    end

    RET->>FS: Write retrieval_log.txt

    NORM->>LOAD: Request raw data
    LOAD->>FS: Read HTML exports
    LOAD-->>NORM: Return DataFrames

    NORM->>NORM: Schema transformation
    NORM->>NORM: Type enforcement
    NORM->>NORM: Validation checks

    NORM->>OUT: Write normalized CSVs
    NORM->>FS: Write validation logs
```

### Core Components
```mermaid
classDiagram
    class LiveRetrievalEngine {
        +CONFIG_PATH: str
        +DATA_DIR: str
        +SCREENSHOT_DIR: str
        +LOG_DIR: str
        +load_config() dict
        +ensure_dirs() void
        +log(msg: str) void
        +fetch_http(adapter) str
        +fetch_browser(adapter, playwright) str
        +main() void
    }

    class DataLoader {
        +DATA_DIR: str
        +BITBO_FILE: str
        +TWELVE_FILE: str
        +BTCETFFO_FILE: str
        +load_etf_flows() DataFrame
        +load_price_history() DataFrame
        +load_btcetffundflow_json(path) DataFrame
    }

    class DataNormalizer {
        +clean_dir: str
        +run_pipeline() void
        +normalize_etf_flows(df) DataFrame
        +normalize_price_history(df) DataFrame
        +validate_schema(df, type) bool
        +cross_validate(df_flows, df_price) bool
        +save_csv(df, filename) void
    }

    class Analytics {
        +calculate_rsi(df, period) DataFrame
        +calculate_cumulative_flows(df) DataFrame
    }

    LiveRetrievalEngine --> DataLoader: produces raw exports
    DataLoader --> DataNormalizer: feeds raw data
    DataNormalizer --> Analytics: provides clean data

    note for LiveRetrievalEngine "Headless execution\nNo UI dependencies"
    note for DataNormalizer "Production-ready ETL\nSchema enforcement"
```

---

## 📊 Data Sources (Reference)

### Configured Adapters (11 Total)

| ID | Source | Data Type | Mode | Status |
|----|--------|-----------|------|--------|
| `twelvedata_btcusd_hist_html` | TwelveData | OHLC Daily | HTTP | ✅ |
| `bitbo_us_etf_flows_table` | Bitbo | ETF Net Flows | HTTP | ✅ |
| `btcetffundflow_holdings_derived` | BTCETFFundFlow | Holdings Flows | HTTP | ✅ |
| `coinalyze_btc_open_interest` | Coinalyze | Open Interest | Browser | ⚠️ Rate-Limited |
| `coinalyze_btc_funding` | Coinalyze | Funding Rates | Browser | ⚠️ Rate-Limited |
| `coingecko_btc_market_snapshot` | CoinGecko | Spot Volume | Browser | ⚠️ Timeout |
| `coinglass_spot_inflow_outflow_xhr` | CoinGlass | Exchange Flows | Browser+XHR | ✅ |
| `coinglass_spot_inflow_outflow_screenshot_only` | CoinGlass | Evidence | Browser | ✅ |
| `coinglass_funding_heatmap_screenshot_only` | CoinGlass | Funding Heat | Browser | ✅ |
| `coinglass_liquidation_heatmap_screenshot_only` | CoinGlass | Liquidation | Browser | ✅ |

### Output Schemas

**Normalized BTC Price** (`data_clean/btc_price_normalized.csv`):
```
date        | open    | high    | low     | close
2025-11-18  | 92100.0 | 93780.0 | 89180.0 | 92910.0
```

**Normalized ETF Flows** (`data_clean/etf_flows_normalized.csv`):
```
date        | ticker | flow_usd       | flow_btc
2025-11-20  | IBIT   | 28600000000.0  | -3753.5
```

---

## 🔧 How-To Guides (Diátaxis: Task-Oriented)

### Schedule Automated Data Collection

**Linux/macOS (cron)**:
```bash
# Run every 4 hours
0 */4 * * * cd /path/to/project && python src/microanalyst/live_retrieval.py && python src/microanalyst/normalization.py
```

**Windows (Task Scheduler)**:
```powershell
# Create scheduled task
schtasks /create /tn "BTCMicroanalyst" /tr "python C:\path\to\project\src\microanalyst\live_retrieval.py" /sc hourly /mo 4
```

### Add New Data Source

**1. Define adapter in configuration**:
```yaml
# BTC Market Data Adapters Configuration.yml
adapters:
  - id: my_custom_source
    url: "https://example.com/btc-metrics"
    retrieval_mode: http  # or browser
    role: custom_indicator
    expected_format: html_table
    extract:
      metric_value:
        strategy: label_regex
        label_contains: "Custom Metric"
        type: number
```

**2. Implement parser**:
```python
# src/microanalyst/data_loader.py
def load_custom_source():
    with open(f"{DATA_DIR}/my_custom_source.html", "r") as f:
        soup = BeautifulSoup(f.read(), "html.parser")
        # Parser implementation
    return df
```

**3. Add normalization**:
```python
# src/microanalyst/normalization.py
def normalize_custom_source(self, df):
    df["date"] = pd.to_datetime(df["Date"])
    df.rename(columns={"Value": "metric"}, inplace=True)
    return df
```

### Export Data for External Systems

**Direct CSV consumption**:
```python
import pandas as pd

# Load normalized data
df_price = pd.read_csv("data_clean/btc_price_normalized.csv")
df_flows = pd.read_csv("data_clean/etf_flows_normalized.csv")

# Your analysis logic here
```

**Database integration example**:
```python
from sqlalchemy import create_engine

engine = create_engine('postgresql://user:pass@localhost/btc')
df_price.to_sql('btc_prices', engine, if_exists='append', index=False)
```

### Validate Data Quality
```bash
# Run simulation (non-destructive adapter check)
python src/microanalyst/simulation.py

# Inspect logs
cat logs/simulation_log.txt

# Verify normalized schemas
python -c "
import pandas as pd
df = pd.read_csv('data_clean/btc_price_normalized.csv')
assert 'date' in df.columns
assert 'close' in df.columns
print('✅ Schema validated')
"
```

---

## 📖 Explanation (Diátaxis: Understanding-Oriented)

### Why Headless Architecture?

**Design Philosophy**: Decouple data acquisition from presentation layer.

**Advantages**:
1. **Modularity**: Analytics platforms consume normalized CSVs without pipeline coupling
2. **Reliability**: No UI framework dependencies reduce failure modes
3. **Automation**: Cron/scheduler integration for lights-out operation
4. **Scalability**: Pipeline can scale independently of visualization needs

**Trade-off**: Requires external tooling (Grafana, Jupyter, Tableau) for visualization.

### Data Normalization Philosophy

**Problem**: 11 sources with heterogeneous schemas, units, and timezones.

**Solution**: Three-stage ETL pipeline

1. **Extract**: Source-specific parsers handle HTML tables, JSON APIs, and XHR responses
2. **Transform**: Standardized column naming (`date`, `ticker`, `flow_usd`, `open`, `high`, `low`, `close`)
3. **Load**: Write to `data_clean/` with validation logs

**Validation Gates**:
- Schema enforcement (required columns)
- Type coercion# 🌌 Antigravity V2: Cognitive Micro-Analyst Swarm

**An advanced, self-correcting cryptocurrency analysis system powered by Agentic AI.**

## 🚀 Mission
To create a "Ground Truth" financial intelligence engine that eliminates hallucination through deterministic math, adversarial debate, and on-chain verification.

## 🧠 Core Intelligence Architecture (Tier 1-3 Complete)

The system operates as a hierarchical swarm of specialized agents, governed by a **Meta-Prompt Optimizer** that learns from mistakes.

### 1. Cognitive Framework (The "Brain")
- **Adversarial Debate Graph**: A `BullAgent` and `BearAgent` continuously debate market conditions. A `Facilitator` weighs their arguments based on valid evidence (RSI, Volume, On-Chain).
- **Reflexion Loop**: The system stores every decision. If a trade fails (e.g., "Bought the top"), the **Reflexion Engine** critiques it and injects a "LESSON LEARNED" block into future prompts (e.g., *"Warning: Don't chase pumps"*).
- **Meta-Prompt Optimizer**: Statistically analyzes error logs. If it detects systemic failures (e.g., 5x RSI errors), it **automatically proposes patches** to the system prompts.

### 2. Agent Swarm (The "Team")
Managed by a **SwarmSupervisor** using a **ReAct** (Thought-Action-Observation) framework:
- **TechnicalSpecialist**: Uses tools (`calc_rsi`, `detect_divergence`) to analyze chart structure.
- **SentimentSpecialist**: Analyzes "Crowd Psychology" (Fear & Greed, Social Volume).
- **OnChainSpecialist**: Monitors the blockchain truth (Whale Alerts, Exchange Inflows).

### 3. Layered Context
Information is strictly segmented to prevent context bleeding:
- **Immediate Layer**: Current Price, Volume, Order Flow (24h).
- **Tactical Layer**: 7-Day Trend, Regime Classification (Bull/Bear/Sideways).
- **Strategic Layer**: 30-Day Macro Thesis, Correlations (DXY, SPY).

## 🛠️ Tech Stack
- **Framework**: Python 3.12+, LangGraph (Orchestration).
- **Intelligence**: `PromptEngine` (Jinja2-style injection), `ConstraintEnforcer` (Hard guardrails).
- **Data**: Binance Spot/Derivatives (Price), Mock On-Chain/Sentiment (for now).
- **Testing**: `pytest` comprehensive suite (~85% coverage).

## ⚡ Quick Start

```bash
# 1. Install Dependencies
pip install -r requirements.txt

# 2. Run the Debate Swarm (Simulation)
python -m src.microanalyst.agents.debate_swarm

# 3. Run Verification Tests
pytest tests/
```

## 📂 Project Structure
```
src/microanalyst/
├── agents/             # The ReAct Swarm (Supervisor, Specialists)
│   ├── debate_swarm.py # Bull/Bear Logic
│   ├── react_agent.py  # Base Thought-Action Loop
│   └── meta_optimizer.py # Self-Correction Logic
├── intelligence/       # Core Logic (The "Cortex")
│   ├── prompt_engine.py # Layered Context Construction
│   ├── constraint_enforcer.py # Regime-based Guardrails
│   └── regime_detector.py # Market State Classification
└── memory/             # Episodic Memory (JSON-based)
```

## ✅ Recent Milestones (Phases 50-56)
- [x] **Adversarial Debate**: Implemented Bull/Bear contest.
- [x] **Reflexion Loop**: System learns from past PnL.
- [x] **Cognitive Refinement**: Layered Memory & Hard Constraint Injection.
- [x] **ReAct Upgrade**: Agents now use tools (`ToolRegistry`) actively.
- [x] **On-Chain Fusion**: Whale Alert integration.
- Future date detection
- Cross-dataset alignment

### Manual Verification Commands
```bash
# Check file counts
ls -la data_exports/ | wc -l  # Should show 11+ files
ls -la screenshots/ | wc -l   # Should show 8+ files

# Inspect normalized data
head data_clean/btc_price_normalized.csv
head data_clean/etf_flows_normalized.csv

# Review logs
tail -n 50 logs/retrieval_log.txt
```

---

## 🗂️ Directory Structure
```
.
├── BTC Market Data Adapters Configuration.yml  # 11 adapter definitions
├── requirements.txt                            # Python dependencies (no UI)
├── data_exports/                               # Raw HTML/JSON artifacts
│   ├── bitbo_us_etf_flows_table.html          # ETF flows table
│   ├── twelvedata_btcusd_hist_html.html       # OHLC price history
│   ├── coinglass_spot_inflow_outflow_xhr.json # Exchange flows (XHR capture)
│   └── [8 more adapter outputs]
├── data_clean/                                 # Normalized CSVs (production-ready)
│   ├── btc_price_normalized.csv               # [date, open, high, low, close]
│   └── etf_flows_normalized.csv               # [date, ticker, flow_usd, flow_btc]
├── screenshots/                                # Visual evidence (full-page captures)
│   ├── coinalyze_btc_funding_full.png
│   ├── coinglass_liquidation_heatmap_full.png
│   └── [15+ screenshots]
├── logs/                                       # Execution logs
│   ├── retrieval_log.txt                      # Live run status codes
│   └── simulation_log.txt                     # Dry-run results
└── src/microanalyst/
    ├── live_retrieval.py                       # Main orchestrator (HTTP + Browser)
    ├── simulation.py                           # Non-destructive adapter tester
    ├── data_loader.py                          # HTML/JSON parsers
    ├── normalization.py                        # ETL pipeline with validation
    ├── analytics.py                            # RSI, cumulative flow calculators
    ├── providers/
    │   ├── binance.py                          # Order book API (unused in headless)
    │   └── sentiment.py                        # Fear & Greed Index (unused in headless)
    └── legacy_ui/                              # Archived Streamlit dashboard
        ├── ui_proof_of_concept.py             # [ARCHIVED] Main dashboard
        ├── charting.py                         # [ARCHIVED] Plotly charts
        ├── components.py                       # [ARCHIVED] Cyber-card renderer
        └── style_injector.py                   # [ARCHIVED] CSS theme
```

---

## 📝 Configuration Reference

### Adapter Schema (YAML)
```yaml
adapters:
  - id: unique_adapter_id              # REQUIRED: String identifier
    url: "https://..."                 # REQUIRED: Data source URL
    retrieval_mode: http|browser       # REQUIRED: Fetch method
    role: semantic_purpose             # Descriptive label (e.g., ohlc_daily)

    # OPTIONAL: Browser-specific settings
    browser:
      engine: playwright
      actions:
        - {type: screenshot_only}
        - {type: set_timeframe, value: "24h"}
        - {type: capture_xhr, filter: json}

    # OPTIONAL: Artifact preservation
    artifacts:
      screenshot_fullpage: true
      screenshot_widgets: true
      xhr_bundle: true

    expected_format: html_table|html_stats|json

    # Field extraction rules
    extract:
      field_name:
        strategy: label_regex|table_by_headers|from_xhr_json
        label_contains: "Search Text"
        type: number|date|string|range
        parse: human_number|percent_number|datetime_text
        optional: true|false

    # Normalization metadata
    normalization:
      units: {price: "USD"}
      timezone_displayed: "UTC"

    # Immutable contract terms (detect drift)
    drift_locks:
      - instrument_id
      - timezone_displayed

    # Quality indicators
    quality:
      parse_confidence: high|medium|low
      is_interactive_only: true|false
```

### Environment Variables

**None required.** All configuration is file-based (YAML + file paths).

---

## 🚀 Production Deployment

### Scheduling Recommendations

**Frequency**: Every 4 hours (aligns with ETF reporting cycles and derivatives settlement)

**Staggered Execution**:
```bash
# Run retrieval first
0 */4 * * * cd /path/to/project && python src/microanalyst/live_retrieval.py

# Normalize 5 minutes later (ensures writes complete)
5 */4 * * * cd /path/to/project && python src/microanalyst/normalization.py
```

### Resource Requirements

- **CPU**: Single-core sufficient (sequential processing)
- **Memory**: ~500MB (Chromium headless + Pandas operations)
- **Disk**: ~50MB per daily cycle (artifacts accumulate)
- **Network**: ~10MB inbound per cycle

### Monitoring

**Success Indicators**:
- `logs/retrieval_log.txt` contains `Stats: {'success': 8, ...}` or higher
- `data_clean/*.csv` files have recent modification timestamps
- `data_clean/btc_price_normalized.csv` has today's date in last row

**Alerting Suggestions**:
```bash
# Cron-based alert on failure threshold
python src/microanalyst/live_retrieval.py
if [ $? -ne 0 ]; then
    echo "BTC Microanalyst failed" | mail -s "Pipeline Alert" admin@example.com
fi
```

### Data Retention Policy

**Recommendation**: Rotate artifacts weekly to prevent disk bloat.
```bash
# Delete exports older than 7 days
find data_exports/ -name "*.html" -mtime +7 -delete
find screenshots/ -name "*.png" -mtime +7 -delete

# Keep normalized CSVs indefinitely (small footprint)
```

---

## ⚠️ Known Issues

### Adapter Reliability

1. **Coinalyze Rate Limiting**: HTTP adapters return 403 after ~5 requests within 1 hour
   - **Mitigation**: Increase polling interval to 4+ hours

2. **CoinGecko Timeout**: Browser adapter frequently exceeds 60s networkidle wait
   - **Mitigation**: Site implements aggressive anti-bot; marked non-critical (skip in failure)

3. **CoinGlass Button Locator**: Timeframe selection fails when DOM structure changes
   - **Impact**: Falls back to default timeframe; screenshot still captured

### Pipeline Limitations

- **No Async Execution**: Sequential adapter processing
- **No Retry Logic**: Failed adapters require manual re-run
- **No Historical Backfill**: Only captures current state per run

---

## 🔗 Integration Examples

### Python Script Consumer
```python
import pandas as pd
from datetime import datetime

# Load normalized data
df_price = pd.read_csv('data_clean/btc_price_normalized.csv', parse_dates=['date'])
df_flows = pd.read_csv('data_clean/etf_flows_normalized.csv', parse_dates=['date'])

# Merge on date
df_merged = pd.merge(df_price, df_flows.groupby('date')['flow_usd'].sum(), on='date', how='left')

# Calculate correlation
correlation = df_merged['close'].corr(df_merged['flow_usd'])
print(f"BTC Price vs ETF Flows correlation: {correlation:.3f}")
```

### SQL Database Loading
```python
from sqlalchemy import create_engine
import pandas as pd

engine = create_engine('postgresql://user:pass@localhost:5432/market_data')

# Load and append normalized data
df_price = pd.read_csv('data_clean/btc_price_normalized.csv')
df_price.to_sql('btc_prices', engine, if_exists='append', index=False)

df_flows = pd.read_csv('data_clean/etf_flows_normalized.csv')
df_flows.to_sql('etf_flows', engine, if_exists='append', index=False)
```

### Jupyter Notebook Analysis
```python
# notebook.ipynb
import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv('data_clean/btc_price_normalized.csv', parse_dates=['date'])
df.set_index('date', inplace=True)

# Plot 30-day price chart
df['close'].tail(30).plot(figsize=(12, 6), title='BTC/USD 30-Day Price')
plt.show()
```

---

## 🤝 Contributing

### Adding Custom Analytics

Extend `src/microanalyst/analytics.py`:
```python
def calculate_bollinger_bands(df, period=20, std_dev=2):
    """
    Calculates Bollinger Bands.
    Expects 'Close' column, returns 'BB_Upper', 'BB_Middle', 'BB_Lower'.
    """
    df['BB_Middle'] = df['Close'].rolling(window=period).mean()
    df['BB_Std'] = df['Close'].rolling(window=period).std()
    df['BB_Upper'] = df['BB_Middle'] + (std_dev * df['BB_Std'])
    df['BB_Lower'] = df['BB_Middle'] - (std_dev * df['BB_Std'])
    return df
```

### Testing New Adapters

1. **Simulation First**: Verify HTTP accessibility
```bash
   python src/microanalyst/simulation.py
```

2. **Live Retrieval Test**: Execute single adapter
```python
   # Modify live_retrieval.py main() to filter:
   adapters = [a for a in all_adapters if a['id'] == 'my_new_adapter']
```

3. **Parser Validation**: Ensure `data_loader.py` extracts expected fields

4. **Normalization Check**: Run `normalization.py` and inspect CSV output

---

## 📚 Dependencies
```
pyyaml              # Configuration parsing
requests            # HTTP adapter engine
pandas              # Data manipulation & CSV I/O
plotly              # Chart generation (unused in headless, kept for analytics.py compatibility)
playwright          # Browser automation
playwright-stealth  # Anti-bot evasion
beautifulsoup4      # HTML parsing
```

**Installation Notes**:
- **Playwright**: Requires `playwright install chromium` post-installation
- **No UI frameworks**: Streamlit removed for headless operation

---

## 🧩 Legacy UI (Archived)

**Location**: `src/microanalyst/legacy_ui/`

The original Streamlit dashboard has been preserved for reference but is **not maintained** in headless deployments.

**Components**:
- `ui_proof_of_concept.py`: Real-time dashboard with cyber-aesthetic
- `charting.py`: Plotly chart generators (candlestick, RSI, depth)
- `components.py`: HTML cyber-card renderer
- `style_injector.py`: CSS theme injection

**To Reactivate** (not recommended for production):
```bash
pip install streamlit
streamlit run src/microanalyst/legacy_ui/ui_proof_of_concept.py
```

---

## 📄 License

**MIT License**. See [LICENSE](LICENSE) for details.

---

## 🛡️ Security Considerations

- **No Authentication**: All data sources use public endpoints
- **No API Keys**: Zero credential management required
- **Stealth Mode**: Playwright-stealth reduces scraping detection
- **Local Execution**: No cloud dependencies or telemetry
- **Data Privacy**: All artifacts stored locally

**OPSEC Note**: Browser fingerprinting may still occur. Rotate execution IP if running at scale.

---


# Antigravity V3: Cognitive Micro-Analyst Swarm

![License](https://img.shields.io/badge/license-MIT-blue)
![Python](https://img.shields.io/badge/python-3.13+-blue)
![Status](https://img.shields.io/badge/system-operational-green)
![Intelligence](https://img.shields.io/badge/AI-OpenRouter_Swarm-purple)

**A "Ground Truth" financial intelligence engine that eliminates hallucination through deterministic data collection, local persistence, and adversarial LLM debate.**

---

## 🚀 Mission
To build an autonomous analyst that doesn't just "read" the market, but **understands** it.
1.  **Observe**: Headless browser swarm aggregates data from 11+ sources (Order Flow, On-Chain, Sentiment).
2.  **Remember**: Normalized data is persisted to a local "Golden Copy" SQLite database.
3.  **Think**: An adversarial swarm of LLM agents (Bull vs. Bear) debates the data to form a synthesized thesis.

---

## ⚡ Quickstart

### Prerequisites
- **Python 3.13+**
- **Playwright** (Chromium)
- **OpenRouter API Key** (for Swarm Intelligence)

### Installation

1.  **Clone and Setup**:
    ```bash
    git clone https://github.com/JackSmack1971/antigravity-microanalyst.git
    cd antigravity-microanalyst
    pip install -r requirements.txt
    playwright install chromium
    ```

2.  **Configure Environment**:
    ```bash
    cp .env.example .env
    # Edit .env and add your OPENROUTER_API_KEY
    ```

### Execution

**1. Data Collection & Persistence**
```bash
# Fetch live data (Shared Browser Pool + Circuit Breakers)
python src/microanalyst/live_retrieval.py

# Normalize and Upsert to SQLite (microanalyst.db)
python src/microanalyst/normalization.py
```

**2. Verify Intelligence**
```bash
# Run the Swarm Debate (Check verify_swarm.py)
python verify_swarm.py
```

---

## 🏗️ V3 Architecture

### System Overview
```mermaid
flowchart TD
    A[Configuration.yml] --> B{Async Retrieval Engine}

    subgraph "Core Engine"
        B -->|Shared Browser Pool| C[Playwright Adapters]
        B -->|Circuit Breaker| D[HTTP Adapters]
    end

    C --> E[Raw Artifacts]
    D --> E

    E --> F[Normalization Pipeline]
    
    subgraph "Mempry & Persistence"
        F --> G[(microanalyst.db)]
        G --> H[Gap Filler]
    end

    subgraph "Cognitive Layer"
        G --> I[Context Window]
        I --> J{Debate Swarm}
        J -->|Bull Case| K[LLM (OpenRouter)]
        J -->|Bear Case| L[LLM (OpenRouter)]
        K & L --> M[Facilitator Synthesis]
    end

    M --> N[Final Thesis]
```

### Key Components

#### 1. Async Retrieval Engine (`src/microanalyst/core/async_retrieval.py`)
-   **Shared Browser Pool**: Launches a single Chromium instance for all browser tasks, reducing RAM usage by 80%.
-   **Smart Circuit Breakers**: Automatically pauses requests to rate-limited hosts (e.g., Coinalyze) to prevent bans.
-   **Parallel Execution**: Fetches 11+ sources concurrently using `asyncio`.

#### 2. Golden Copy Persistence (`src/microanalyst/core/persistence.py`)
-   **SQLite Backend**: Zero-conf local database (`microanalyst.db`).
-   **Auto-Upsert**: `normalization.py` automatically inserts/updates records.
-   **Gap Detection**: `gap_filler.py` identifies missing historical days.

#### 3. Cognitive Swarm (`src/microanalyst/agents/debate_swarm.py`)
-   **Real LLM Inference**: Uses `langchain` + `OpenRouter` to access models like Claude 3.5 Sonnet or Gemini Pro.
-   **Adversarial Logic**:
    -   **Retail Agent**: Momentum-focused, FOMO-prone.
    -   **Institutional Agent**: Risk-averse, flow-centric.
    -   **Whale Agent**: Liquidity-hunting, contrarian.
-   **Fallback Mode**: Gracefully degrades to simulation logic if API key is missing.

---

## 📊 Data & Schemas

### Microanalyst Database (`microanalyst.db`)
| Table | Description | Update Freq |
|-------|-------------|-------------|
| `btc_price_daily` | OHLC data from TwelveData | Daily |
| `etf_flows_daily` | Net Inflow/Outflow (USD/BTC) | Daily |

### Artifacts (`data_exports/`)
-   **JSON/HTML**: Raw responses from all adapters.
-   **Screenshots**: Visual evidence (Liquidation Heatmaps, Funding Rates).

---

## 🔧 Production Guide

### Scheduled Execution (Cron/Task Scheduler)
Recommended frequency: **Every 4 hours**.

```bash
cd /path/to/antigravity
python src/microanalyst/live_retrieval.py && python src/microanalyst/normalization.py
```

### Monitoring
-   **Logs**: Check `logs/retrieval_log.txt` for `Success Rate`.
-   **Database**: Run `python verify_db.py` to inspect recent writes.

---

## ⚠️ Known Issues
-   **CoinGecko Timeout**: The "Market Snapshot" adapter frequently times out due to heavy anti-bot protections. This is non-critical.
-   **Coinalyze 403s**: Aggressive IP blocking. Circuit breakers mitigate impact, but data may be stale if blocked.

---

## 📄 License
MIT License.

# Microanalyst API Documentation

This document describes the primary programmatic entry points and integrations for the Antigravity Microanalyst system.

## 1. Data Retrieval Pipeline

### Live Retrieval
**Module**: `src/microanalyst/live_retrieval.py`

Fetches data from all configured sources using the discovery engine.

- **Usage**:
  ```bash
  python src/microanalyst/live_retrieval.py
  ```
- **Outputs**:
  - Raw artifacts in `data_exports/`
  - Normalization ready datasets.

## 2. Agent Intelligence Swarm

### Agent Coordinator
**Module**: `src/microanalyst/agents/agent_coordinator.py`

Orchestrates specialized analyst roles into a synthesized market thesis.

- **Available Roles**:
  - `DATA_COLLECTOR`: Fetches raw data.
  - `ANALYST_TECHNICAL`: Performs statistical price analysis.
  - `ANALYST_SENTIMENT`: Aggregates cross-platform social sentiment.
  - `ANALYST_RISK`: Evaluates volatility and drawdown risks.
  - `PREDICTION_ORACLE`: Forecasts T+24h direction.
  - `SYNTHESIZER`: Combines all inputs into the final thesis.

## 3. Knowledge & ML Lifecycle

### Automated Retrainer
**Module**: `src/microanalyst/intelligence/automated_retrainer.py`

Handles the continuous training and evaluation of the Oracle models.

- **Workflow**:
  1. Detect frequency from data.
  2. Build labeled ML dataset.
  3. Train candidate model.
  4. Compare with active model.
  5. Promote if improvement > 2%.

## 4. WebSocket API (Experimental)

### Subscription Topics
The system supports real-time updates via WebSocket (see `src/microanalyst/mcp_server.py`).

- `market_data`: Raw OHLCV updates.
- `agent_thesis`: Live outputs from the Synthesizer agent.
- `oracle_signal`: T+24h price target forecasts.

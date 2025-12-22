# TECH DEBT REPORT: Antigravity Microanalyst

**Date:** 2025-12-21  
**Scan Depth:** Full Codebase (src/, frontend/)  
**Confidence Score:** 0.85

---

## 1. Complexity High-Scores (Refactoring Candidates)

Files exceeding 300 LOC or exhibiting high cyclomatic complexity.

| File Path | LOC (Approx) | Complexity Notes | Volatility |
| :--- | :--- | :--- | :--- |
| `src/microanalyst/agents/agent_coordinator.py` | 800+ | **Critical Hotspot**. Manages 18 tasks across 5 stages. High nesting in `asyncio` logic. | High |
| `src/microanalyst/intelligence/confluence_calculator.py` | 510+ | Heavy mathematical logic. Contains TODOs for data joining. | Medium |
| `src/microanalyst/agents/debate_swarm.py` | 470+ | Complex LangGraph state transitions. Recently repaired for logic leaks. | High |

> [!IMPORTANT]
> **Priority Recommendation**: Refactor `agent_coordinator.py` using the "Modular Registry" pattern (see [ADR 001](file:///c:/workspaces/antigravity-microanalyst/antigravity-microanalyst/docs/adr/001-hybrid-orchestration.md)) to reduce the monolithic complexity.

---

## 2. Comment Audit (Technical Red Flags)

Identified tags: `TODO`, `FIXME`, `HACK`.

| File | Line | Content | Risk Level |
| :--- | :--- | :--- | :--- |
| `portfolio_manager.py` | 46 | `TODO: Call db_manager.log_paper_portfolio(summary)` | Low (Feature Gap) |
| `confluence_calculator.py` | 505 | `TODO: Join with price data... Returning placeholders.` | **High** (Data Quality) |
| `metadata/cli.py` | 9 | `# Path hack for imports` | Medium (Environment) |
| `style_injector.py` | 65 | `specific class hacking` | Low (UI Polish) |

---

## 3. Dependency Inventory & Rot

| Ecosystem | Status | Observation |
| :--- | :--- | :--- |
| **Python** | **Stable** | Using modern `pydantic v2` and `numpy 2.2`. Missing pins for `requests` and `pytest`. |
| **Frontend** | **Bleeding Edge** | Using `Next.js 16.1.0`, `React 19`, and `Tailwind 4`. High risk of breaking changes from upstream beta releases. |

> [!WARNING]
> The project uses unpinned versions for critical server libraries (`uvicorn`, `requests`). This may lead to "Silent Build Failures" in future CI/CD runs.

---

## 4. Immediate Action Plan

1.  **Standardize Orchestration**: Migrate `agent_coordinator.py` logic to a modular registry to split the 800 LOC monolith.
2.  **Fix Placeholder Logic**: Address the placeholder return in `confluence_calculator.py:L505` to ensure data integrity during adversarial debates.
3.  **Dependency Pinning**: Run an audit to pin all loosely defined requirements in `requirements.txt`.

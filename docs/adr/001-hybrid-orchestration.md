# ADR 001: Hybrid Agent Orchestration Strategy

**Date:** 2025-12-21  
**Status:** Accepted  
**Deciders:** Antigravity (Agent), User

## Context

The Antigravity Microanalyst currently employs two distinct orchestration methods:
1.  **Custom `AgentCoordinator`**: A monolithic Python class managing high-level stages (Data Collection, Validation, Synthesis) using manual topological sorting and `asyncio.gather`.
2.  **LangGraph `debate_swarm`**: A graph-based multi-agent system managing adversarial discussion among specialized personas.

This hybrid model creates inconsistency in state management and observability, and the `AgentCoordinator` is approaching a complexity limit (~800 lines).

## Decision

We will adopt a **Modular Registry** approach for orchestration.

1.  **Registry (Management Layer)**: Retain a thin `AgentCoordinator` (or rename to `SwarmRegistry`) to handle system-level concerns:
    *   API Endpoint management.
    *   Local file I/O and caching.
    *   Data normalization (Agent Ready Dataset).
    *   Trace collection and telemetry.
2.  **Graphs (Intelligence Layer)**: Delegate all complex logical workflows to **LangGraph**.
    *   Sub-workflows (e.g., Risk Assessment, Sentiment Aggregation) should be formalized into specialized graphs.
    *   The Decision Maker already uses LangGraph.
3.  **Interface**: High-level stages will remain as structured "capabilities" in the registry, but their internal implementation will shift towards modular graphs or specialized agents.

## Consequences

### Positive
*   **Reduced Complexity**: Decouples data retrieval/plumbing from cognitive reasoning logic.
*   **Standardized State**: Moves towards the `AgentState` (TypedDict) pattern for all intelligence tasks.
*   **Observability**: Enables richer visualization of complex debate flows through LangGraph-compatible tooling.
*   **Parallelism**: Simplifies parallel execution of divergent analyst viewpoints.

### Negative
*   **Increased Dependencies**: Deeper reliance on `langgraph` and `langchain` ecosystems.
*   **Overhead**: Small performance overhead for graph state transitions (acceptable for asynchronous analytical tasks).

## Consequences of Failure to Implement
Continuing with the monolithic custom coordinator will lead to "spaghetti code" in dependency management and make the system harder to debug as new data sources and analyst roles are added.

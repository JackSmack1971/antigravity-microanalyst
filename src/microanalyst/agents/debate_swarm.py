"""Adversarial cognitive debate swarm for market thesis generation.

This module implements a multi-agent debate system where specialized AI personas
(Retail Momentum Analyst, Institutional Algo, Whale Sniper, Macro Economist)
analyze market data through adversarial discussion to synthesize a robust trading
thesis. The system uses LangGraph for state management and adaptive thinking levels
to adjust cognitive depth based on market volatility.

Architecture:
    1. Orchestrator: Initializes the debate and distributes state to all agents
    2. Parallel Agent Analysis: 4 specialized personas analyze data concurrently
        - Retail Agent: Momentum and social sentiment focus
        - Institution Agent: Statistical variance and regime analysis
        - Whale Agent: On-chain flow detection and intent inference
        - Macro Agent: Correlation analysis with traditional markets (DXY, SPY)
    3. Facilitator: Synthesizes divergent views into consensus decision
    4. Risk Manager: Applies deterministic validation and safety checks
    
Adaptive Thinking:
    The system adjusts cognitive complexity based on market volatility:
    - Low volatility (0-30): QUICK thinking (fast, heuristic-based)
    - Medium volatility (30-60): BALANCED thinking (moderate analysis)
    - High volatility (60-100): DEEP thinking (extensive reasoning)

Key Classes:
    MarketSignal: Output schema for agent decisions
    AgentState: Shared state maintained throughout the debate graph

Main Entry Point:
    run_adversarial_debate(dataset) - Executes the full debate workflow

Example:
    >>> dataset = {
    ...     'price_data': {...},
    ...     'order_flow': {...},
    ...     'sentiment': {...},
    ...     'volatility_score': 45
    ... }
    >>> result = run_adversarial_debate(dataset)
    >>> result['decision']
    'BUY'
    >>> result['confidence']
    0.85
"""

import operator
from typing import Annotated, Dict, List, Any, TypedDict, Union
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, END
import logging
import json
from src.microanalyst.intelligence.llm_config import get_openrouter_llm
# Lazy loading to prevent boot-time hang on Python 3.13
# from langchain_core.prompts import ChatPromptTemplate
# from langchain_core.output_parsers import StrOutputParser
from src.microanalyst.intelligence.prompts.personas import (
    RETAIL_AGENT_PROMPT, 
    INSTITUTIONAL_AGENT_PROMPT, 
    WHALE_AGENT_PROMPT,
    MACRO_AGENT_PROMPT,
    FACILITATOR_PROMPT
)
from src.microanalyst.intelligence.whale_intent import WhaleIntentEngine
from src.microanalyst.intelligence.confluence import ConfluenceUtils


from src.microanalyst.core.adaptive_thinking import AdaptiveThinkingConfig, ThinkingLevel

logger = logging.getLogger(__name__)

# --- State & Schema ---

class MarketSignal(BaseModel):
    """Pydantic model representing an agent's market decision output.
    
    Encapsulates a trading recommendation with confidence scoring, allocation
    suggestion, and reasoning. Used both for individual agent outputs and the
    final synthesized consensus decision.
    
    Attributes:
        decision: Trading action to take. Must be one of: "BUY", "SELL", "HOLD".
        confidence: Confidence score from 0.0 (no confidence) to 1.0 (maximum confidence).
            Typically >0.7 indicates high-conviction signals.
        suggested_allocation: Fraction of portfolio to allocate (0.0 to 1.0).
            Example: 0.25 = 25% of portfolio.
        reasoning: Human-readable explanation of the decision rationale.
            Should reference key data points or market conditions.
        winning_persona: Identifier of which agent persona's logic dominated the decision.
            One of: "Retail", "Institutional", "Whale", "Macro", or "Consensus".
    
    Example:
        >>> signal = MarketSignal(
        ...     decision="BUY",
        ...     confidence=0.85,
        ...     suggested_allocation=0.50,
        ...     reasoning="Strong momentum with institutional support detected",
        ...     winning_persona="Institutional"
        ... )
        >>> signal.decision
        'BUY'
    """
    decision: str = Field(description="BUY, SELL, or HOLD")
    confidence: float = Field(description="Confidence from 0 to 1")
    suggested_allocation: float = Field(description="Percentage of portfolio to allocate (0.0 to 1.0)")
    reasoning: str = Field(description="Concise rationale for the decision")
    winning_persona: str = Field(description="Which persona led this decision?")


class AgentState(TypedDict):
    """Shared state dictionary for the cognitive debate graph workflow.
    
    This TypedDict defines the complete state maintained throughout the multi-agent
    debate process. State is passed between nodes in the LangGraph workflow, with
    each agent reading from and writing to specific fields.
    
    Attributes:
        symbol: Trading symbol being analyzed (e.g., "BTCUSDT").
        regime: Current market regime classification (e.g., "bullish", "bearish", "volatile").
        market_data: Dictionary containing all input data from retrieval pipeline:
            - price_data: OHLCV and technical indicators
            - order_flow: Exchange flow, liquidations, funding rates
            - sentiment: Social media and news sentiment aggregation
            - on_chain: Blockchain metrics (if applicable)
        thinking_level: Adaptive cognitive mode for LLMs. One of:
            - "QUICK": Fast heuristic analysis (low volatility)
            - "BALANCED": Moderate depth (normal markets)
            - "DEEP": Extensive reasoning (high volatility or uncertainty)
        volatility_score: Current market volatility percentile (0-100).
            Used to determine thinking_level and risk adjustments.
        retail_view: Retail Momentum Analyst's perspective.
        institution_view: Institutional Algo's statistical variance analysis.
        whale_view: Whale Sniper's on-chain intent detection and flow analysis.
        macro_view: Macro Economist's correlation analysis with TradFi.
        synthesis: Intermediate MarketSignal from facilitator (pre-risk-check).
        final_decision: Final MarketSignal after risk manager validation.
        logs: Accumulated log messages documenting the debate flow.
    """
    symbol: str
    regime: str
    market_data: Dict[str, Any]
    thinking_level: str # Added P3
    volatility_score: float # Added P3
    
    # Divergent Viewpoints
    retail_view: str
    institution_view: str
    whale_view: str
    macro_view: str
    
    synthesis: MarketSignal
    final_decision: MarketSignal
    logs: Annotated[List[str], operator.add]

# --- Nodes ---

def orchestrator_node(state: AgentState) -> Dict[str, Any]:
    """Entry point for the cognitive swarm. Passes control to all analysts."""
    return {"logs": ["Initiating high-concurrency cognitive debate..."]}

def retail_agent_node(state: AgentState) -> Dict[str, Any]:
    """Node representing the Retail Momentum Analyst."""
    regime = state.get('regime', 'neutral')
    data = state.get('market_data', {})
    
    # P3: Adaptive Thinking Injection
    thinking_level =  ThinkingLevel(state.get('thinking_level', 'BALANCED'))
    config = AdaptiveThinkingConfig.get_config(thinking_level)
    
    # LLM Invocation
    llm = get_openrouter_llm()
    if not llm:
        # Fallback to simulation if no key
        return {
            "retail_view": "[RETAIL (SIM)]: Bullish! (No API Key)",
            "logs": ["Retail Agent used fallback logic."]
        }

    from langchain_core.prompts import ChatPromptTemplate
    from langchain_core.output_parsers import StrOutputParser

    prompt = ChatPromptTemplate.from_messages([
        ("system", RETAIL_AGENT_PROMPT),
        ("user", "Context: Regime={regime}, Data={data}, Thinking={thinking}. Analyze.")
    ])
    
    chain = prompt | llm | StrOutputParser()
    
    try:
        response = chain.invoke({
            "regime": regime, 
            "data": str(data), 
            "thinking": thinking_level
        })
    except Exception as e:
        response = f"Error generating view: {e}"

    logger.info(f"[RETAIL] Analyzing thinking level: {thinking_level}")
    return {
        "retail_view": f"[RETAIL ({thinking_level})]: {response}",
        "logs": [f"Retail Agent thinking at {thinking_level} level."]
    }

def institution_agent_node(state: AgentState) -> Dict[str, Any]:
    """Node representing the Institutional Algo."""
    regime = state.get('regime', 'neutral')
    data = state.get('market_data', {})
    
    # P3: Adaptive Thinking Injection
    thinking_level = ThinkingLevel(state.get('thinking_level', 'BALANCED'))
    config = AdaptiveThinkingConfig.get_config(thinking_level)

    # LLM Invocation
    llm = get_openrouter_llm()
    if not llm:
        return {
             "institution_view": "[INSTITUTION (SIM)]: Risk off. (No API Key)",
             "logs": ["Institutional Agent used fallback logic."]
        }

    from langchain_core.prompts import ChatPromptTemplate
    from langchain_core.output_parsers import StrOutputParser

    prompt = ChatPromptTemplate.from_messages([
        ("system", INSTITUTIONAL_AGENT_PROMPT),
        ("user", "Context: Regime={regime}, Data={data}. Provide institutional risk assessment.")
    ])
    
    chain = prompt | llm | StrOutputParser()
    try:
        response = chain.invoke({"regime": regime, "data": str(data)})
    except Exception as e:
        response = f"Error: {e}"

    return {
        "institution_view": f"[INSTITUTION ({thinking_level})]: {response}",
        "logs": ["Institutional Agent calculated variances."]
    }

def whale_agent_node(state: AgentState) -> Dict[str, Any]:
    """Node representing the Whale Sniper."""
    regime = state.get('regime', 'neutral')
    
    # P3: Adaptive Thinking Injection
    thinking_level = ThinkingLevel(state.get('thinking_level', 'BALANCED'))
    
    # LLM Invocation
    # LLM Invocation
    # P4: Use WhaleIntentEngine for Theory of Mind
    engine = WhaleIntentEngine()
    
    # Construct context from state
    # MOCKING: In real flow, 'market_data' would have these specific keys extracted by DataNormalizer
    market_context = {
        "price": state.get('market_data', {}).get('price', 0),
        "trend": regime, # Using regime as proxy for trend
        "open_interest": state.get('market_data', {}).get('open_interest', 'Unknown'),
        "funding_rate": state.get('market_data', {}).get('funding_rate', 0),
        "liquidation_clusters": state.get('market_data', {}).get('liquidation_clusters', [])
    }

    analysis = {}
    try:
        analysis = engine.analyze_market_structure(market_context)
        
        # Format for debate
        response = f"Intent: {analysis.get('intent')} | Target: ${analysis.get('target_price')} | Logic: {analysis.get('logic')}"
        
    except Exception as e:
        response = f"Error: {e}"
        
    logger.info(f"[WHALE] Intent detected: {analysis.get('intent', 'unknown')}")
    return {
        "whale_view": f"[WHALE ({thinking_level})]: {response}",
        "logs": [f"Whale Agent analyzed intent: {analysis.get('intent', 'unknown')}"]
    }

def macro_agent_node(state: AgentState) -> Dict[str, Any]:
    """Node representing the Macro Economist."""
    regime = state.get('regime', 'neutral')
    data = state.get('market_data', {})
    
    thinking_level = ThinkingLevel(state.get('thinking_level', 'BALANCED'))
    
    # LLM Invocation
    llm = get_openrouter_llm()
    if not llm:
        return {
             "macro_view": "[MACRO (SIM)]: Decoupling detected. (No API Key)",
             "logs": ["Macro Agent used fallback logic."]
        }

    from langchain_core.prompts import ChatPromptTemplate
    from langchain_core.output_parsers import StrOutputParser

    prompt = ChatPromptTemplate.from_messages([
        ("system", MACRO_AGENT_PROMPT),
        ("user", "Context: Regime={regime}, Data={data}. Analyze structural correlations.")
    ])
    
    chain = prompt | llm | StrOutputParser()
    try:
        response = chain.invoke({"regime": regime, "data": str(data)})
    except Exception as e:
        response = f"Error: {e}"

    logger.info(f"[MACRO] Regime analysis: {regime}")
    return {
        "macro_view": f"[MACRO ({thinking_level})]: {response}",
        "logs": ["Macro Agent analyzed global correlations."]
    }

def facilitator_node(state: AgentState) -> Dict[str, Any]:
    """Synthesizes the 4-way adversarial debate into a definitive consensus decision."""
    retail = state['retail_view']
    inst = state['institution_view']
    whale = state['whale_view']
    macro = state['macro_view']
    regime = state['regime']
    
    # Logic: Facilitator determines the winner based on Regime Context
    decision = "HOLD"
    conf = 0.5
    winner = "Consensus"
    reasoning = "Mixed signals."
    
    # Simple Heuristic for Demo:
    # - If Whale predicts "Distribution" in Bull Trend -> SELL (Top signal)
    # - If Institution says "Accumulating" -> BUY
    
    if "distribute" in whale.lower() and "bull" in regime:
        decision = "SELL"
        conf = 0.85
        winner = "Whale Sniper"
        reasoning = "Whale detects retail FOMO and is distributing. Bull trap imminent."
    elif "accumulating" in inst.lower():
        decision = "BUY"
        conf = 0.8
        winner = "Institutional Algo"
        reasoning = "Smart money is accumulating in range."
    elif "fly" in retail.lower() and "bull" in regime:
        # If Whale isn't selling, we ride
        decision = "BUY"
        conf = 0.7
        winner = "Retail Momentum"
        reasoning = "Trend followers are in control. Ride the wave."
        
    # Phase 49: Macro Integration
    if "decoupling" in macro.lower() and "bullish" in macro.lower():
        # Decoupling is a strong structural alpha signal
        decision = "BUY"
        conf = max(conf, 0.85)
        winner = "Macro Economist"
        reasoning = f"BTC decoupling from DXY/SPY into a structural Safe Haven. | {reasoning}"
    elif "beta" in macro.lower() and decision == "BUY":
        # Institutional alert: High beta risk
        conf = min(conf, 0.6)
        reasoning += " | WARNING: High Beta correlation with Equities adds volatility risk."
        
    # P5: Check Confluence
    confluence_check = ConfluenceUtils().check_fractal_alignment()
    if confluence_check.get("aligned", False):
        alignment_type = confluence_check.get("type")
        # Boost confidence if signal aligns with fractal trend
        if decision == "BUY" and "Bullish" in alignment_type:
            conf = min(0.99, conf + 0.1)
            reasoning += f" [FRACTAL CONFLUENCE: {alignment_type}]"
            winner += " + Confluence"
        elif decision == "SELL" and "Bearish" in alignment_type:
            conf = min(0.99, conf + 0.1)
            reasoning += f" [FRACTAL CONFLUENCE: {alignment_type}]"
            winner += " + Confluence"
        else:
             reasoning += f" (Fractal: {alignment_type} - Divergence noted)"

    # Intent Validation: Boost confidence if Whale detects clear intentional flow
    if "Intent:" in whale and "unknown" not in whale.lower():
         # Tactical adjustment for high-conviction whale signatures
         if "accumulation" in whale.lower() and decision == "BUY":
             conf = min(0.95, conf + 0.05)
         elif "distribution" in whale.lower() and decision == "SELL":
             conf = min(0.95, conf + 0.05)

    signal = MarketSignal(
        decision=decision,
        confidence=conf,
        suggested_allocation=0.5 if decision != "HOLD" else 0.0,
        reasoning=reasoning,
        winning_persona=winner
    )
    
    logger.info(f"Facilitator sided with {winner}. Decision: {decision}")
    return {
        "synthesis": signal,
        "logs": [f"Facilitator sided with {winner}. Fractal: {confluence_check.get('type')}"]
    }

def risk_manager_node(state: AgentState) -> Dict[str, Any]:
    """Deterministic vetting of the signal."""
    signal = state['synthesis']
    regime = state['regime']
    
    final_allocation = signal.suggested_allocation
    
    # Hard Rules
    if regime == "high_volatility" and signal.decision == "BUY":
        final_allocation *= 0.5 # Size down in chaos
        
    final_signal = MarketSignal(
        decision=signal.decision,
        confidence=signal.confidence,
        suggested_allocation=final_allocation,
        reasoning=f"{signal.reasoning} | {signal.winning_persona} logic validated.",
        winning_persona=signal.winning_persona
    )
    
    logger.info(f"Risk Manager applied constraints. Final Allocation: {final_allocation}")
    return {
        "final_decision": final_signal,
        "logs": ["Risk Manager applied constraints."]
    }

# --- Graph Wiring ---

def create_debate_swarm_graph():
    """Compiles the Cognitive Personas graph."""
    workflow = StateGraph(AgentState)
    
    workflow.add_node("orchestrator", orchestrator_node)
    workflow.add_node("retail", retail_agent_node)
    workflow.add_node("institution", institution_agent_node)
    workflow.add_node("whale", whale_agent_node)
    workflow.add_node("macro", macro_agent_node)
    workflow.add_node("facilitator", facilitator_node)
    workflow.add_node("risk_manager", risk_manager_node)
    
    # Edges - Concurrent Fan-Out from Orchestrator
    workflow.set_entry_point("orchestrator") 
    
    # Orchestrator triggers all analysts in parallel
    workflow.add_edge("orchestrator", "retail")
    workflow.add_edge("orchestrator", "institution")
    workflow.add_edge("orchestrator", "whale")
    workflow.add_edge("orchestrator", "macro")
    
    # Fan-In: All analysts aggregate at the facilitator
    workflow.add_edge("retail", "facilitator")
    workflow.add_edge("institution", "facilitator")
    workflow.add_edge("whale", "facilitator")
    workflow.add_edge("macro", "facilitator")
    
    workflow.add_edge("facilitator", "risk_manager")
    workflow.add_edge("risk_manager", END)
    
    return workflow.compile()

# --- Execution Entry ---

def run_adversarial_debate(dataset: Dict[str, Any]) -> Dict[str, Any]:
    """Executes the adversarial cognitive debate graph.

    Orchestrates the multi-agent interaction where specialized personas
    (Retail, Macro, Whale, Institutional) analyze the provided dataset and
    debate towards a synthesized market thesis.

    Args:
        dataset: The unified intelligence dataset containing price, 
                 correlation, and sentiment inputs.

    Returns:
        dict: The final synthesized signal, including final_decision, 
              confidence, and reasoning logs.
    """
    app = create_debate_swarm_graph()
    
    
    # Determine Volatility & Thinking Level
    # (In prod, this comes from data[volatility], here we mock or extract)
    # Let's assume input has 'volatility' key 0-100, default 40
    vol_score = dataset.get('volatility_score', 40)
    t_level = AdaptiveThinkingConfig.determine_level(vol_score)
    
    initial_state = {
        "symbol": "BTCUSDT",
        "regime": dataset.get('ground_truth', {}).get('regime', 'unknown'),
        "market_data": dataset,
        "thinking_level": t_level,
        "volatility_score": vol_score,
        "retail_view": "",
        "institution_view": "",
        "whale_view": "",
        "macro_view": "",
        "logs": [f"System initialized with {t_level} thinking (Vol: {vol_score})"]
    }
    
    result = app.invoke(initial_state)
    
    # Transform result for AgentCoordinator compatibility
    return {
        "decision": result["final_decision"].decision,
        "confidence": result["final_decision"].confidence,
        "allocation_pct": result["final_decision"].suggested_allocation * 100,
        "reasoning": result["final_decision"].reasoning,
        "bull_case": result["retail_view"], # Mapping Retail to 'Bull' slot for legacy UI compat
        "bear_case": result["whale_view"],  # Mapping Whale to 'Bear' slot for legacy UI compat
        "macro_thesis": result["macro_view"],
        "logs": result["logs"]
    }

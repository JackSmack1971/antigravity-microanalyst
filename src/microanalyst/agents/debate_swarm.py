import operator
from typing import Annotated, Dict, List, Any, TypedDict, Union
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, END
import logging
import json
from src.microanalyst.intelligence.llm_config import get_openrouter_llm
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
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
    decision: str = Field(description="BUY, SELL, or HOLD")
    confidence: float = Field(description="Confidence from 0 to 1")
    suggested_allocation: float = Field(description="Percentage of portfolio to allocate (0.0 to 1.0)")
    reasoning: str = Field(description="Concise rationale for the decision")
    winning_persona: str = Field(description="Which persona led this decision?")

class AgentState(TypedDict):
    """The state of the cognitive debate graph."""
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

    try:
        analysis = engine.analyze_market_structure(market_context)
        
        # Format for debate
        response = f"Intent: {analysis.get('intent')} | Target: ${analysis.get('target_price')} | Logic: {analysis.get('logic')}"
        
    except Exception as e:
        response = f"Error: {e}"
        
    return {
        "whale_view": f"[WHALE ({thinking_level})]: {response}",
        "logs": [f"Whale Agent analyzed intent: {analysis.get('intent')}"]
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

    prompt = ChatPromptTemplate.from_messages([
        ("system", MACRO_AGENT_PROMPT),
        ("user", "Context: Regime={regime}, Data={data}. Analyze structural correlations.")
    ])
    
    chain = prompt | llm | StrOutputParser()
    try:
        response = chain.invoke({"regime": regime, "data": str(data)})
    except Exception as e:
        response = f"Error: {e}"

    return {
        "macro_view": f"[MACRO ({thinking_level})]: {response}",
        "logs": ["Macro Agent analyzed global correlations."]
    }

def facilitator_node(state: AgentState) -> Dict[str, Any]:
    """Synthesizes the 3-way debate into a definitive decision."""
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

    # P6: Extract Confidence from Prediction Oracle (if in debate)
    oracle_conf = 0.5
    if "Intent:" in whale: # Mapped to Whale/Bear slot in coordination
         try:
             # Heuristic check for confidence in logic string or just boost if high whale confidence
             oracle_conf = conf # Use current logic's confidence as baseline
         except: pass

    signal = MarketSignal(
        decision=decision,
        confidence=conf,
        suggested_allocation=0.5 if decision != "HOLD" else 0.0,
        reasoning=reasoning,
        winning_persona=winner
    )
    
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
        "allocation_pct": result["final_decision"].suggested_allocation * 100,
        "reasoning": result["final_decision"].reasoning,
        "bull_case": result["retail_view"], # Mapping Retail to 'Bull' slot for legacy UI compat
        "bear_case": result["whale_view"],  # Mapping Whale to 'Bear' slot for legacy UI compat
        "macro_thesis": result["macro_view"],
        "logs": result["logs"]
    }

from typing import List, Dict, Any
from collections import Counter

class MetaPromptOptimizer:
    """
    Technique 10: Meta-Prompting for Self-Optimization.
    Analyzes aggregated critiques to propose permanent prompt updates.
    """
    
    def __init__(self):
        pass
        
    def analyze_critiques(self, critiques: List[str]) -> Dict[str, Any]:
        """
        Clusters critiques and proposes actionable prompt patches.
        """
        if not critiques:
            return {"status": "No critiques to analyze"}
            
        # 1. Clustering (Simple keyword matching for Tier 2)
        issues = []
        for c in critiques:
            if "RSI" in c: issues.append("RSI_misinterpretation")
            if "chase pumps" in c or "FOMO" in c: issues.append("FOMO_behavior")
            if "leverage" in c: issues.append("risk_violation")
            
        issue_counts = Counter(issues)
        most_common = issue_counts.most_common(1)
        
        if not most_common:
            return {"status": "No systemic patterns found"}
            
        top_issue, count = most_common[0]
        
        # 2. Generate Patch Proposal
        proposal = ""
        if top_issue == "RSI_misinterpretation":
            proposal = "INJECTION: 'When trending, RSI overbought is NOT a sell signal. Look for divergence.'"
        elif top_issue == "FOMO_behavior":
            proposal = "INJECTION: 'Do NOT buy widely publicized pumps. Wait for 30% pullback.'"
        elif top_issue == "risk_violation":
             proposal = "INJECTION: 'Strictly enforce 2% stop loss on all leverage trades.'"
             
        timestamp = "2024-WT-56" # Mock
        
        return {
            "status": "Optimization Proposal Generated",
            "detected_pattern": top_issue,
            "frequency": count,
            "proposal": f"### PROMPT PATCH {timestamp}\n**Reason**: Repeated error {top_issue}\n**Action**: Inject -> {proposal}"
        }

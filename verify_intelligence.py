import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from src.microanalyst.intelligence.context_synthesizer import ContextSynthesizer

def verify_intelligence():
    print("Initializing ContextSynthesizer...")
    synthesizer = ContextSynthesizer()
    
    print("\n[Test 1] Synthesizing Context...")
    try:
        context = synthesizer.synthesize_context(lookback_days=30)
        print(f"✅ Context generated successfully.")
        print(f"   Regime: {context.regime['current_regime']} (Confidence: {context.regime['regime_confidence']:.2f})")
        print(f"   Signals: {len(context.signals)}")
        print(f"   Risks Overall Score: {context.risks['overall_risk_score']:.2f}")
    except Exception as e:
        print(f"❌ Failed to synthesize context: {e}")
        return

    print("\n[Test 2] Generating Reports...")
    formats = ["markdown", "json", "executive"]
    
    for fmt in formats:
        try:
            report_type = "executive" if fmt == "executive" else "comprehensive"
            out_fmt = "markdown" if fmt == "executive" else fmt
            
            report = synthesizer.generate_report(
                context, 
                report_type=report_type, 
                output_format=out_fmt,
                agent_optimized=False
            )
            preview = report[:100].replace('\n', ' ') + "..."
            print(f"✅ Generated {fmt} report: {preview}")
        except Exception as e:
            print(f"❌ Failed to generate {fmt} report: {e}")

    print("\nVerification Complete.")

if __name__ == "__main__":
    verify_intelligence()

import os
import sys
from src.microanalyst.intelligence.vision import VisionParser
from pathlib import Path

def test_vision():
    print("--- Starting Vision Intelligence Verification ---")
    
    # Locate the test file
    screenshot_dir = Path("screenshots")
    test_file = list(screenshot_dir.glob("*coinglass_liquidation_heatmap*full.png"))[0]
    
    if not test_file or not test_file.exists():
        print("skipped: No screenshot found to test.")
        return

    print(f"Analyzing: {test_file}")
    
    parser = VisionParser()
    try:
        results = parser.extract_liquidation_clusters(str(test_file))
        print("\n[VISION OUTPUT]:")
        import json
        print(json.dumps(results, indent=2))
        
        if isinstance(results, list) and len(results) > 0 and "price" in results[0]:
            print("\nSUCCESS: Parsed structured data from image.")
        else:
            print("\nWARNING: Output format unexpected or empty.")
            
    except Exception as e:
        print(f"FAILURE: {e}")

if __name__ == "__main__":
    test_vision()

import asyncio
import sys
from pathlib import Path

# Add project root to path for imports to work
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from src.microanalyst.core.async_retrieval import AsyncRetrievalEngine

def main():
    print("Starting BTC Microanalyst [Async Mode]")
    engine = AsyncRetrievalEngine()
    
    # Run the async pipeline
    try:
        stats = asyncio.run(engine.execute_pipeline())
        
        if stats.get("success", 0) < 8:
            print("CRITICAL: Success rate below threshold. See logs.")
            sys.exit(1)
            
    except Exception as e:
        print(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

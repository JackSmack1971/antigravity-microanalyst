import asyncio
import os
import sys

# Ensure src is in path
sys.path.append(os.getcwd())

from src.microanalyst.synthetic.orderbook_intelligence import OrderBookIntelligence

async def test_orderbook_streaming():
    print("Testing Order Book Intelligence (Real-time Stream)...")
    
    obi = OrderBookIntelligence()
    
    # We will run for a short duration to verify connectivity and parsing
    duration = 5 # seconds
    
    print(f"Connecting to live stream for {duration} seconds...")
    try:
        count = 0
        async for metrics in obi.stream_orderbook(symbol='btcusdt', duration_seconds=duration):
            count += 1
            if count == 1:
                print("✅ connection_established")
            
            # Print sample every ~10 updates (1 sec)
            if count % 10 == 0:
                print(f"Update #{count}")
                print(f"  > Imbalance: {metrics.get('bid_ask_imbalance'):.4f} ({metrics.get('interpretation')})")
                print(f"  > Spread: {metrics.get('spread_pct'):.4f}%")
                print(f"  > Walls: {metrics.get('walls')}")
                print(f"  > Gradient: Bid={metrics.get('bid_gradient'):.2f}, Ask={metrics.get('ask_gradient'):.2f}")
        
        print("\nVerifying Heatmap Generation...")
        heatmap = obi.generate_liquidity_heatmap()
        if 'error' in heatmap:
             print(f"❌ Heatmap Error: {heatmap['error']}")
        else:
             print(f"✅ Heatmap Generated: {len(heatmap.get('top_liquidity_clusters', []))} clusters found.")
             print(f"Top Cluster: {heatmap['top_liquidity_clusters'][0] if heatmap['top_liquidity_clusters'] else 'None'}")

    except Exception as e:
        print(f"❌ Critical Error: {e}")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        
    asyncio.run(test_orderbook_streaming())

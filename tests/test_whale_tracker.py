import asyncio
import os
import sys

sys.path.append(os.getcwd())

from src.microanalyst.synthetic.whale_tracker import WhaleActivityTracker

def test_whale_tracker():
    print("Testing Whale Activity Tracker (Mempool)...")
    
    tracker = WhaleActivityTracker()
    
    print("Fetching live unconfirmed transactions from Blockchain.info...")
    # Using a lower threshold for testing to ensure we catch *something* in a short window
    # if the mempool is quiet for mega whales. 
    # Default is 100 BTC. Let's try 1 BTC for functionality test, 
    # but the method defaults to 100. We'll pass 1.0 explicitely to see flow.
    
    metrics = tracker.detect_whale_movements(threshold_btc=0.5) 
    
    if 'error' in metrics:
        print(f"❌ Error: {metrics['error']}")
    else:
        print(f"✅ Connection Successful")
        print(f"   Whale Transactions Found (>0.5 BTC): {metrics['whale_transactions_count']}")
        print(f"   Total Volume: {metrics['total_volume_btc']:.2f} BTC")
        print(f"   Alert Level: {metrics['alert_level']}")
        
        if metrics['transactions']:
            print("\n   [Latest Whale Samples]")
            for tx in metrics['transactions'][:3]:
                print(f"   🔹 {tx['value_btc']:.2f} BTC | Entity: {tx['entity_name']} | {tx['interpretation']}")
        else:
             print("\n   [No massive whales found in this snapshot - Mempool quiet]")

    print("\nWhale Tracker verification complete!")

if __name__ == "__main__":
    test_whale_tracker()

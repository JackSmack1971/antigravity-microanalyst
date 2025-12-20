from src.microanalyst.intelligence.chain_watcher import ChainWatcher

def verify_chain_watcher():
    print("--- Starting ChainWatcher Verification ---")
    watcher = ChainWatcher()
    stats = watcher.fetch_mempool_stats()
    
    print("On-Chain Stats Received:")
    print(stats)
    
    # Assertions
    assert "mempool_vbytes" in stats
    assert "fastest_fee_sats" in stats
    
    if stats["fastest_fee_sats"] > 0:
        print(f"✅ Live Connection Confirmed. Fastest Fee: {stats['fastest_fee_sats']} sats/vB")
    else:
        print("⚠️ Failed to fetch fees or fee is 0 (unlikely for mainnet)")

    print(f"Congestion Level: {stats.get('congestion_level')}")

if __name__ == "__main__":
    verify_chain_watcher()

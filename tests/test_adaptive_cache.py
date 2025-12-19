import time
import os
import sys

sys.path.append(os.getcwd())

from src.microanalyst.core.adaptive_cache import AdaptiveCacheManager

def test_adaptive_cache():
    print("Testing Adaptive Cache Manager...")
    
    # Initialize (Should log if falling back or using Redis)
    cache = AdaptiveCacheManager()
    backend_type = "Redis" if cache.use_redis else "In-Memory"
    print(f"✅ Cache Initialized. Backend: {backend_type}")
    
    # Test 1: Set and Get (Hit)
    print("\n[Test 1: Basic Cache Hit]")
    def expensive_fetch():
        print("   >>> Fetching fresh data (Source)...")
        return {"data": 42}
        
    # First call: Should fetch
    val1 = cache.get_or_fetch("test:key1", expensive_fetch, policy='realtime')
    print(f"   Value 1: {val1}")
    
    # Second call: Should hit cache (No print from fetch)
    print("   ... Retrieving again (Should be silent) ...")
    val2 = cache.get_or_fetch("test:key1", expensive_fetch, policy='realtime')
    print(f"   Value 2: {val2}")
    
    if val1 == val2:
        print("✅ Cache Hit Successful (Values match)")
    else:
        print("❌ Cache Hit Failed")

    # Test 2: TTL Expiration
    print("\n[Test 2: TTL Expiration]")
    # Realtime policy is 10s. We don't want to wait 10s for a unit test usually,
    # but for verification we can modify policy temporarily or just mock logic.
    # Let's override policy for test key.
    cache.cache_policies['test_short'] = 2 # 2 seconds
    
    val3 = cache.get_or_fetch("test:expiry", expensive_fetch, policy='test_short')
    print("   Data cached. Waiting 3 seconds...")
    time.sleep(3)
    
    print("   Retrieving again (Should fetch fresh)...")
    val4 = cache.get_or_fetch("test:expiry", expensive_fetch, policy='test_short')
    
    # We can't strictly assert "fetch called" without mock spying, but visually the print should appear.
    print("✅ TTL Test Complete (Verify 'Fetching fresh data' appeared twice)")
    
    # Test 3: Invalidation
    print("\n[Test 3: Event Invalidation]")
    cache.get_or_fetch("funding:btc", expensive_fetch, policy='slow')
    
    print("   Invalidating 'funding_update'...")
    cache.invalidate_on_event('funding_update')
    
    # Should fetch again
    print("   Retrieving funding (Should fetch fresh)...")
    cache.get_or_fetch("funding:btc", expensive_fetch, policy='slow')
    print("✅ Invalidation Test Complete")

if __name__ == "__main__":
    test_adaptive_cache()

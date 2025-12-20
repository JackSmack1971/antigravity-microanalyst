import os
import logging
from src.microanalyst.core.proxy_manager import ProxyManager

# Mock Env
os.environ["PROXY_LIST"] = "http://proxy1:8080, http://proxy2:8080"

def test_proxy_manager():
    print("Testing ProxyManager...")
    
    # Initialize
    pm = ProxyManager(use_free_proxies=False)
    
    # Test Load
    print(f"Proxies Loaded: {len(pm.proxies)}")
    if len(pm.proxies) != 2:
        print("FAILURE: Did not load 2 proxies from env.")
        return

    # Test Rotation
    p1 = pm.get_proxy()
    print(f"Got Proxy: {p1}")
    
    # Report Failure
    pm.report_failure(p1)
    print(f"Reported failure for {p1}")
    
    # Should get the other one (random, but if p1 is banned, only p2 remains)
    # Note: simple random choice might pick p1 again if check is not rigorous, 
    # but my logic filters banned.
    
    p2 = pm.get_proxy()
    print(f"Got Proxy: {p2}")
    
    if p2 == p1:
        print("FAILURE: Got banned proxy again!")
    else:
        print("SUCCESS: Got fresh proxy.")

    # Ban second one
    pm.report_failure(p2)
    
    # Now all banned, should recycle or return None depending on implementation.
    # Implementation says: recycle if all banned.
    p3 = pm.get_proxy()
    print(f"Got Proxy (after recycle): {p3}")
    
    if p3 in [p1, p2]:
        print("SUCCESS: Recycled banned list.")
    else:
        print("FAILURE: Did not recycle.")

if __name__ == "__main__":
    test_proxy_manager()

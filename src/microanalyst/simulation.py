import yaml
import requests
import datetime
import os
import sys

# Constants
CONFIG_PATH = "BTC Market Data Adapters Configuration.yml"
LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "simulation_log.txt")

def load_config():
    if not os.path.exists(CONFIG_PATH):
        print(f"Error: Config file not found at {CONFIG_PATH}")
        sys.exit(1)
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def ensure_log_dir():
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)

def log(message):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted_msg = f"[{timestamp}] {message}"
    print(formatted_msg)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(formatted_msg + "\n")

def simulate_http_adapters(adapters):
    success_count = 0
    fail_count = 0
    
    log(f"Starting Non-Destructive Simulation for {len(adapters)} HTTP adapters...")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    for adapter in adapters:
        adapter_id = adapter.get("id")
        url = adapter.get("url")
        
        log(f"Testing Adapter: {adapter_id} | URL: {url}")
        
        try:
            # Using stream=True and verify=False to minimize impact and ignore potential SSL cert issues for simulation
            # We just want to know if the server responds
            response = requests.get(url, headers=headers, stream=True, timeout=10)
            
            if response.status_code < 400:
                log(f"  -> SUCCESS: Status {response.status_code}")
                success_count += 1
            else:
                log(f"  -> FAILURE: Status {response.status_code}")
                fail_count += 1
                
            response.close()
            
        except Exception as e:
            log(f"  -> EXCEPTION: {str(e)}")
            fail_count += 1

    log("-" * 40)
    log(f"Simulation Complete. Success: {success_count}, Failures: {fail_count}")
    return success_count, fail_count

def main():
    ensure_log_dir()
    config = load_config()
    all_adapters = config.get("adapters", [])
    
    # Filter for HTTP adapters
    http_adapters = [a for a in all_adapters if a.get("retrieval_mode") == "http"]
    
    log(f"Found {len(http_adapters)} HTTP adapters in configuration.")
    
    success, fails = simulate_http_adapters(http_adapters)
    
    # We aren't failing hard here based on the instructions, just reporting.
    # But for the mission success metrics later, we need 8/11. 
    # Simulation is just a dry run.
    
if __name__ == "__main__":
    main()

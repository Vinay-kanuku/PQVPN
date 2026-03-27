import subprocess
import requests
import time
import sys
import os

# Configuration
INTERFACE = "wg0"
TARGET_URL = "http://10.0.0.2:9000"
FILE_NAME = "top_secret_project.txt"

def is_quantum_secure():
    """
    Checks if WireGuard has a PSK injected by Arnika.
    """
    try:
        # We need sudo to read WireGuard keys
        result = subprocess.check_output(["wg", "show", INTERFACE, "preshared-keys"], text=True)
        
        # If output contains "(none)", the tunnel is NOT quantum-safe
        if "(none)" in result or not result.strip():
            return False
        return True
    except Exception as e:
        print(f"Error checking security status: {e}")
        return False

def sync_data():
    # 1. SECURITY CHECK
    if not is_quantum_secure():
        print("[BLOCK] Tunnel is NOT Quantum-Secure. Sync aborted.")
        return

    # 2. PERFORM SYNC
    print("[SECURE] Quantum Keys Detected. Sending file...")
    try:
        with open(FILE_NAME, 'rb') as f:
            headers = {'X-Filename': FILE_NAME}
            response = requests.post(TARGET_URL, data=f, headers=headers, timeout=5)
            
        if response.status_code == 200:
            print(f"[SUCCESS] File uploaded to {TARGET_URL}")
        else:
            print(f"[FAIL] Server responded with {response.status_code}")
            
    except Exception as e:
        print(f"[ERROR] Connection failed: {e}")

if __name__ == "__main__":
    # Create a dummy file to sync
    with open(FILE_NAME, "w") as f:
        f.write(f"This data was transferred at {time.ctime()} using Post-Quantum Cryptography.")

    print("--- Arnika Secure Sync Started ---")
    while True:
        sync_data()
        time.sleep(5) # Try to sync every 5 seconds
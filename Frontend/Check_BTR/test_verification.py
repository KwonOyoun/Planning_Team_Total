import requests
import time
import subprocess
import sys
import threading

def run_server():
    print("[Test] Starting Flask Server...")
    # Run server as a subprocess
    process = subprocess.Popen(
        [sys.executable, "app.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    return process

def monitor_output(process, stop_event):
    print("[Test] Monitoring logs...")
    browser_started = False
    bs4_used = False
    login_success = False

    while not stop_event.is_set() and process.poll() is None:
        line = process.stdout.readline()
        if not line:
            break
        line = line.strip()
        if line:
            print(f"[Server Log] {line}")
            if "Initializing Browser..." in line:
                browser_started = True
                print("[Test] CHECK: Browser launch detected (Lazy Start verified)")
            if "Parsing loaded content with BeautifulSoup" in line:
                bs4_used = True
                print("[Test] CHECK: BeautifulSoup usage detected")
            if "Login successful" in line:
                login_success = True
                print("[Test] CHECK: Login successful")
    
    return browser_started, bs4_used, login_success

def test_flow():
    server_process = run_server()
    stop_monitoring = threading.Event()
    
    # Start monitor thread
    monitor_thread = threading.Thread(target=monitor_output, args=(server_process, stop_monitoring))
    monitor_thread.daemon = True
    monitor_thread.start()

    try:
        # Give it time to start
        time.sleep(5)
        
        print("\n[Test] triggering /api/trips (Refresh Data)...")
        # This might take time (scrolling), so we set a long timeout
        try:
            start_time = time.time()
            resp = requests.get("http://127.0.0.1:5001/api/trips", timeout=300)
            elapsed = time.time() - start_time
            print(f"[Test] Request completed in {elapsed:.2f} seconds")
            
            if resp.status_code == 200:
                data = resp.json()
                print(f"[Test] Success! Received {len(data)} items.")
                # print(f"Sample item: {data[0] if data else 'None'}")
            else:
                print(f"[Test] Failed: Status {resp.status_code}, {resp.text}")
                
        except Exception as e:
            print(f"[Test] Request failed: {e}")

    finally:
        print("\n[Test] Stopping server...")
        stop_monitoring.set()
        server_process.terminate()
        server_process.wait()

if __name__ == "__main__":
    test_flow()

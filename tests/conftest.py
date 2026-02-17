
import pytest
import os
import subprocess
import time
import requests
import sys
from pathlib import Path

# Use a specific port for testing to avoid conflicts
PORT = 8503
BASE_URL = f"http://localhost:{PORT}"
ROOT_DIR = Path(__file__).parent.parent

@pytest.fixture(scope="session")
def base_url():
    return BASE_URL

@pytest.fixture(scope="session", autouse=True)
def run_app():
    """Launch the streamlit app as a subprocess."""
    print(f"\nLaunching Streamlit on port {PORT}...")
    
    # Use python -m streamlit to ensure we use the same python environment
    cmd = [sys.executable, "-m", "streamlit", "run", "app.py", f"--server.port={PORT}", "--server.headless=true"]
    
    process = subprocess.Popen(
        cmd,
        cwd=str(ROOT_DIR),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True  # Text mode for easier output reading
    )
    
    # Wait for the server to start
    start_time = time.time()
    connected = False
    while time.time() - start_time < 30:
        try:
            response = requests.get(f"{BASE_URL}/_stcore/health")
            if response.status_code == 200:
                connected = True
                break
        except requests.ConnectionError:
            time.sleep(1)
            
    if not connected:
        # Iffailed, print stderr for debugging
        stdout, stderr = process.communicate(timeout=2)
        print(f"Failed to start Streamlit:\nSTDOUT: {stdout}\nSTDERR: {stderr}")
        process.terminate()
        pytest.fail("Streamlit failed to start within timeout.")
        
    print(f"Streamlit is running at {BASE_URL}")
    yield process
    
    print("\nStopping Streamlit...")
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()

import requests
import json
import random
import time

BASE_URL = "http://127.0.0.1:8000"

def test_health():
    try:
        resp = requests.get(f"{BASE_URL}/")
        print(f"[GET /] Status: {resp.status_code}, Response: {resp.json()}")
    except Exception as e:
        print(f"Health check failed: {e}")

def test_login_flow():
    print("\n--- Testing Login Flow ---")
    payload = {"username": "admin", "password": "password"}
    try:
        resp = requests.post(f"{BASE_URL}/auth/login", json=payload)
        if resp.status_code == 200:
            data = resp.json()
            print(f"Login Success! Session: {data['session_id']}, Token: {data['token']}")
            return data['session_id']
        else:
            print(f"Login Failed: {resp.status_code} - {resp.text}")
            return None
    except Exception as e:
        print(f"Login Request Failed: {e}")
        return None

def test_continuous_keystroke(user_id):
    print(f"\n--- Testing Continuous Auth (Keystroke) for {user_id} ---")
    # Generate random sequence: [hold, flight, digraph, speed]
    # Shape: (50, 4)
    sequence = [[random.random() for _ in range(4)] for _ in range(50)]
    
    payload = {
        "session_id": user_id,
        "data": [{"key": "a", "hold": 0.1, "flight": 0.2}] # Example format
    }
    
    try:
        resp = requests.post(f"{BASE_URL}/auth/keystroke", json=payload)
        if resp.status_code == 200:
            data = resp.json()
            print(f"Risk Score: {data['risk_score']:.4f}")
            print(f"Action: {data['action']}")
            print(f"Reason: {data['reason']}")
        else:
            print(f"Keystroke Auth Failed: {resp.status_code} - {resp.text}")
    except Exception as e:
        print(f"Keystroke Request Failed: {e}")

if __name__ == "__main__":
    # Wait for server to be likely up
    time.sleep(1)
    
    test_health()
    user_id = test_login_flow()
    if user_id:
        test_continuous_keystroke(user_id)

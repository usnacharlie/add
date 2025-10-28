#!/usr/bin/env python3
"""Test script for USSD Gateway endpoints"""

import requests
import json
import time

BASE_URL = "http://localhost:57023"

def test_initial_menu():
    """Test initial USSD menu"""
    print("\n=== Testing Initial Menu ===")

    data = {
        "sessionId": "test_session_001",
        "msisdn": "260979669350",
        "text": ""
    }

    response = requests.post(f"{BASE_URL}/ussd", json=data)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.json()

def test_language_selection():
    """Test language selection"""
    print("\n=== Testing Language Selection ===")

    data = {
        "sessionId": "test_session_002",
        "msisdn": "260979669350",
        "text": "1"  # Select Register
    }

    response = requests.post(f"{BASE_URL}/ussd", json=data)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.json()

def test_registration_flow():
    """Test complete registration flow"""
    print("\n=== Testing Registration Flow ===")

    session_id = "test_session_003"
    phone = "260979669350"

    # Step 1: Initial menu
    print("\nStep 1: Initial Menu")
    response = requests.post(f"{BASE_URL}/ussd", json={
        "sessionId": session_id,
        "msisdn": phone,
        "text": ""
    })
    print(f"Response: {response.json()['response_string'][:100]}...")

    # Step 2: Select Register (1)
    print("\nStep 2: Select Register")
    response = requests.post(f"{BASE_URL}/ussd", json={
        "sessionId": session_id,
        "msisdn": phone,
        "text": "1"
    })
    print(f"Response: {response.json()['response_string'][:100]}...")

    # Step 3: Select Language (1 for English)
    print("\nStep 3: Select English")
    response = requests.post(f"{BASE_URL}/ussd", json={
        "sessionId": session_id,
        "msisdn": phone,
        "text": "1*1"
    })
    print(f"Response: {response.json()['response_string'][:100]}...")

    # Step 4: Enter First Name
    print("\nStep 4: Enter First Name")
    response = requests.post(f"{BASE_URL}/ussd", json={
        "sessionId": session_id,
        "msisdn": phone,
        "text": "1*1*Dennis"
    })
    print(f"Response: {response.json()['response_string'][:100]}...")

    # Step 5: Enter Last Name
    print("\nStep 5: Enter Last Name")
    response = requests.post(f"{BASE_URL}/ussd", json={
        "sessionId": session_id,
        "msisdn": phone,
        "text": "1*1*Dennis*Kazembe"
    })
    print(f"Response: {response.json()['response_string'][:100]}...")

    # Step 6: Enter NRC
    print("\nStep 6: Enter NRC")
    response = requests.post(f"{BASE_URL}/ussd", json={
        "sessionId": session_id,
        "msisdn": phone,
        "text": "1*1*Dennis*Kazembe*123456/12/1"
    })
    print(f"Response: {response.json()['response_string'][:100]}...")

    # Step 7: Enter DOB
    print("\nStep 7: Enter Date of Birth")
    response = requests.post(f"{BASE_URL}/ussd", json={
        "sessionId": session_id,
        "msisdn": phone,
        "text": "1*1*Dennis*Kazembe*123456/12/1*01/01/1990"
    })
    print(f"Response: {response.json()['response_string'][:100]}...")

    # Step 8: Select Province (1 for Lusaka)
    print("\nStep 8: Select Province")
    response = requests.post(f"{BASE_URL}/ussd", json={
        "sessionId": session_id,
        "msisdn": phone,
        "text": "1*1*Dennis*Kazembe*123456/12/1*01/01/1990*1"
    })
    print(f"Response: {response.json()['response_string'][:100]}...")

    return response.json()

def test_callback_endpoint():
    """Test callback endpoint"""
    print("\n=== Testing Callback Endpoint ===")

    data = {
        "status": "success",
        "session_id": "test_session_001",
        "message": "Registration completed",
        "member_id": "ADD2024001"
    }

    response = requests.post(f"{BASE_URL}/ussd/callback", json=data)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    return response.json()

def test_check_status():
    """Test status check"""
    print("\n=== Testing Status Check ===")

    data = {
        "sessionId": "test_session_004",
        "msisdn": "260979669350",
        "text": "2"  # Check Status option
    }

    response = requests.post(f"{BASE_URL}/ussd", json=data)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.json()

def main():
    """Run all tests"""
    print("Starting USSD Gateway Tests")
    print("=" * 50)

    try:
        # Test initial menu
        test_initial_menu()
        time.sleep(1)

        # Test language selection
        test_language_selection()
        time.sleep(1)

        # Test registration flow
        test_registration_flow()
        time.sleep(1)

        # Test callback
        test_callback_endpoint()
        time.sleep(1)

        # Test status check
        test_check_status()

        print("\n" + "=" * 50)
        print("All tests completed successfully!")

    except Exception as e:
        print(f"\nError during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
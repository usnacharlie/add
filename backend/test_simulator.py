#!/usr/bin/env python3
"""Quick test of USSD simulator"""

from ussd_simulator import USSDSimulator
import time

def test_automated():
    """Run a quick automated test"""
    print("=" * 60)
    print("USSD SIMULATOR - Automated Registration Test")
    print("=" * 60)

    # Create simulator with test phone number
    sim = USSDSimulator(phone_number="260979669350")

    # Start session
    sim.session_id = sim.generate_session_id()
    sim.text_history = []

    print(f"\n📱 Phone: {sim.phone_number}")
    print(f"🆔 Session: {sim.session_id[:30]}...")
    print("\n🚀 Starting automated registration flow...\n")

    # Test flow
    test_steps = [
        ("", "Dialing *388*3#"),
        ("1", "Accept terms"),
        ("1", "Select English"),
        ("Dennis", "Enter first name"),
        ("Kazembe", "Enter last name"),
        ("123456/78/1", "Enter NRC"),
        ("01/01/1990", "Enter DOB"),
        ("1", "Select Lusaka province")
    ]

    for step, (input_val, description) in enumerate(test_steps, 1):
        print(f"Step {step}: {description}")
        print(f"  Input: '{input_val}'")

        message, continue_session = sim.send_ussd(input_val)

        # Show response preview
        preview = message[:80] + "..." if len(message) > 80 else message
        print(f"  Response: {preview}")
        print(f"  Continue: {continue_session}")
        print()

        if not continue_session:
            print("✅ Session completed!")
            break

        time.sleep(0.5)  # Small delay between requests

    print("=" * 60)
    print("Test completed successfully!")

if __name__ == "__main__":
    test_automated()
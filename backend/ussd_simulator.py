#!/usr/bin/env python3
"""
USSD Simulator for ADD Membership System
Simulates a phone USSD interaction with the gateway
"""

import requests
import json
import time
import sys
import random
import os
from datetime import datetime

# Configuration
USSD_GATEWAY_URL = "http://localhost:57023/ussd"
EXTERNAL_URL = "http://31.97.113.202:57023/ussd"

class USSDSimulator:
    def __init__(self, phone_number=None, use_external=False):
        """Initialize USSD simulator"""
        self.phone_number = phone_number or self.generate_phone_number()
        self.session_id = None
        self.text_history = []
        self.url = EXTERNAL_URL if use_external else USSD_GATEWAY_URL
        self.session_active = False

    def generate_phone_number(self):
        """Generate a random Zambian phone number"""
        prefixes = ['097', '077', '096', '076', '095', '075']
        return f"260{random.choice(prefixes)}{random.randint(1000000, 9999999)}"

    def generate_session_id(self):
        """Generate a unique session ID"""
        timestamp = int(time.time() * 1000)
        return f"sim_{timestamp}_{random.randint(1000, 9999)}"

    def clear_screen(self):
        """Clear terminal screen"""
        os.system('cls' if os.name == 'nt' else 'clear')

    def display_phone_screen(self, message, show_input=True):
        """Display message in phone-like interface"""
        self.clear_screen()
        print("\n" + "="*50)
        print("📱 USSD SIMULATOR - ADD Membership")
        print("="*50)
        print(f"Phone: {self.phone_number}")
        print(f"Session: {self.session_id[:20]}..." if self.session_id else "No active session")
        print("-"*50)
        print("\n📟 USSD Display:\n")

        # Display the USSD message
        lines = message.split('\n')
        for line in lines:
            print(f"  {line}")

        print("\n" + "-"*50)

        if not show_input:
            print("\n💭 Session ended")
            print("="*50)

    def send_ussd(self, user_input=""):
        """Send USSD request to gateway"""
        try:
            # Build text history
            if user_input:
                self.text_history.append(user_input)

            # Prepare request data
            data = {
                "sessionId": self.session_id,
                "msisdn": self.phone_number,
                "text": "*".join(self.text_history)
            }

            # Send request
            response = requests.post(
                self.url,
                json=data,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )

            if response.status_code == 200:
                result = response.json()
                self.session_active = result.get('continue_session', False)
                return result.get('response_string', 'No response'), self.session_active
            else:
                return f"Error: HTTP {response.status_code}", False

        except requests.exceptions.ConnectionError:
            return "❌ Connection failed. Is the USSD gateway running?", False
        except requests.exceptions.Timeout:
            return "❌ Request timed out", False
        except Exception as e:
            return f"❌ Error: {str(e)}", False

    def run_interactive_session(self):
        """Run an interactive USSD session"""
        print("\n🚀 Starting USSD Simulator...")
        print(f"📞 Using phone number: {self.phone_number}")
        print(f"🌐 Gateway URL: {self.url}")
        time.sleep(2)

        # Start new session
        self.session_id = self.generate_session_id()
        self.text_history = []
        self.session_active = True

        # Send initial request (dialing *388*3#)
        message, continue_session = self.send_ussd()

        if not message.startswith("❌"):
            print("\n📞 Dialing *388*3#...")
            time.sleep(1)

        while continue_session:
            self.display_phone_screen(message)

            # Get user input
            try:
                user_input = input("\n📝 Enter your choice (or 'q' to quit): ").strip()

                if user_input.lower() == 'q':
                    print("\n👋 Ending session...")
                    break

                if not user_input:
                    print("⚠️  Please enter a valid input")
                    time.sleep(1)
                    continue

                # Send user input
                print(f"\n📤 Sending: {user_input}")
                time.sleep(0.5)

                message, continue_session = self.send_ussd(user_input)

            except KeyboardInterrupt:
                print("\n\n👋 Session interrupted by user")
                break

        # Display final message
        if message and not message.startswith("❌"):
            self.display_phone_screen(message, show_input=False)
        else:
            print(f"\n{message}")

        print("\n✅ Session completed")
        print(f"📊 Total inputs: {len(self.text_history)}")

    def run_automated_test(self, test_scenario="register"):
        """Run automated test scenarios"""
        print(f"\n🤖 Running automated test: {test_scenario}")
        print(f"📞 Phone: {self.phone_number}")

        scenarios = {
            "register": [
                ("", "Initial menu"),
                ("1", "Accept terms"),
                ("1", "Select English"),
                ("John", "Enter first name"),
                ("Banda", "Enter last name"),
                ("123456/78/1", "Enter NRC"),
                ("15/03/1985", "Enter DOB"),
                ("1", "Select Lusaka province"),
                ("1", "Select district"),
                ("1", "Select constituency"),
                ("1", "Select ward"),
                ("1", "Confirm details")
            ],
            "check_status": [
                ("", "Initial menu"),
                ("2", "Check status")
            ],
            "invalid": [
                ("", "Initial menu"),
                ("9", "Invalid option"),
                ("abc", "Invalid input"),
                ("", "Empty input")
            ]
        }

        if test_scenario not in scenarios:
            print(f"❌ Unknown scenario: {test_scenario}")
            return

        # Start session
        self.session_id = self.generate_session_id()
        self.text_history = []

        test_steps = scenarios[test_scenario]

        for i, (input_value, description) in enumerate(test_steps, 1):
            print(f"\n📍 Step {i}: {description}")
            print(f"   Input: '{input_value}'")

            message, continue_session = self.send_ussd(input_value)

            print(f"   Response: {message[:60]}..." if len(message) > 60 else f"   Response: {message}")
            print(f"   Continue: {continue_session}")

            if not continue_session:
                print(f"\n🏁 Session ended at step {i}")
                break

            time.sleep(0.5)

        print(f"\n✅ Automated test completed: {test_scenario}")

def main():
    """Main function to run the simulator"""
    print("""
╔══════════════════════════════════════════════╗
║         ADD USSD Gateway Simulator           ║
║     Alliance for Democracy & Development     ║
╚══════════════════════════════════════════════╝
    """)

    while True:
        print("\n📋 MAIN MENU:")
        print("1. Interactive Session (Local)")
        print("2. Interactive Session (External)")
        print("3. Automated Test - Registration")
        print("4. Automated Test - Check Status")
        print("5. Automated Test - Invalid Inputs")
        print("6. Custom Phone Number")
        print("0. Exit")

        try:
            choice = input("\n👉 Select option: ").strip()

            if choice == "0":
                print("\n👋 Goodbye!")
                break

            elif choice == "1":
                sim = USSDSimulator()
                sim.run_interactive_session()

            elif choice == "2":
                sim = USSDSimulator(use_external=True)
                sim.run_interactive_session()

            elif choice == "3":
                sim = USSDSimulator()
                sim.run_automated_test("register")

            elif choice == "4":
                sim = USSDSimulator()
                sim.run_automated_test("check_status")

            elif choice == "5":
                sim = USSDSimulator()
                sim.run_automated_test("invalid")

            elif choice == "6":
                phone = input("📱 Enter phone number (or press Enter for random): ").strip()
                if not phone:
                    phone = None
                sim = USSDSimulator(phone_number=phone)
                sim.run_interactive_session()

            else:
                print("❌ Invalid option. Please try again.")

            input("\n📌 Press Enter to continue...")

        except KeyboardInterrupt:
            print("\n\n👋 Exiting simulator...")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            input("\nPress Enter to continue...")

if __name__ == "__main__":
    main()
# ADD USSD Gateway Simulator

## Overview
The USSD simulator allows you to test the ADD membership registration system as if you were using a real phone.

## Access Methods

### 1. Web-Based Simulator (Recommended)
- **Local:** http://localhost:57023/
- **External:** http://31.97.113.202:57023/

Features:
- Phone-like interface with keypad
- Visual USSD display
- Session management
- Quick test buttons
- Network selection (MTN, Airtel, Zamtel)

### 2. Command-Line Simulator
```bash
cd /var/member/backend
source venv_ussd/bin/activate
python ussd_simulator.py
```

Menu Options:
1. Interactive Session (Local)
2. Interactive Session (External)
3. Automated Test - Registration
4. Automated Test - Check Status
5. Automated Test - Invalid Inputs
6. Custom Phone Number

### 3. Python API Test
```bash
cd /var/member/backend
source venv_ussd/bin/activate
python test_ussd.py
```

## USSD Flow

### Initial Menu (*388*3#)
```
Welcome to ADD!
Alliance for Democracy
& Development
UPND Partner
K50/year membership
1. Accept
2. Decline
```

### Registration Flow
1. Accept terms → Press 1
2. Select language (1-8)
3. Enter first name
4. Enter last name
5. Enter NRC number
6. Enter date of birth (DD/MM/YYYY)
7. Select province
8. Select district
9. Select constituency
10. Select ward
11. Confirm details
12. Payment instructions

### Status Check
- Dial *388*3# → Press 2
- Enter NRC number
- View membership status

## Testing Tips

### Web Simulator
1. Open browser to http://localhost:57023/
2. Click "📞 Dial *388*3#" to start
3. Use the on-screen keypad or keyboard numbers
4. Click "SEND" or press Enter to submit
5. Click "📴 End Session" to stop

### Quick Registration Test
1. Click "⚡ Quick Register"
2. Follow the prompts
3. Enter test data:
   - Name: John Banda
   - NRC: 123456/78/1
   - DOB: 01/01/1990
   - Location: Select 1 for each

### Automated Testing
```python
from ussd_simulator import USSDSimulator

# Create simulator
sim = USSDSimulator(phone_number="260979669350")

# Run automated test
sim.run_automated_test("register")
```

## Test Phone Numbers
- 260979669350 (Dennis)
- 260977123456 (Test user)
- Random: Leave blank for auto-generation

## Endpoints

### Main USSD Handler
- **URL:** `/ussd`
- **Method:** POST
- **Body:**
```json
{
  "sessionId": "test_001",
  "msisdn": "260979669350",
  "text": "1*1*John"
}
```

### Callback URL
- **URL:** `/ussd/callback`
- **Method:** POST
- **Purpose:** Receives async notifications

### Health Check
- **URL:** `/health`
- **Method:** GET

### Active Sessions
- **URL:** `/sessions/active`
- **Method:** GET

## Troubleshooting

### Gateway Not Running
```bash
# Start the gateway
cd /var/member/backend
./start_ussd.sh
```

### Port Already in Use
```bash
# Kill existing process
lsof -i :57023 | grep LISTEN | awk '{print $2}' | xargs -r kill -9

# Restart
./start_ussd.sh
```

### Connection Failed
- Check if gateway is running: `curl http://localhost:57023/health`
- Check logs: Watch the terminal where gateway is running
- Verify port: Should be 57023

## Session Management
- Sessions timeout after 3 minutes
- Each phone number can have one active session
- Session IDs are unique per interaction

## Support
For issues or questions about the USSD gateway, check:
- Gateway logs in terminal
- `/health` endpoint for status
- `/sessions/active` for active sessions
# API Usage Examples

This document provides practical examples for using the Member Registry API.

## Base URL
```
http://localhost:9500/api/v1
```

## Interactive Documentation
Visit http://localhost:9500/docs for interactive API documentation (Swagger UI).

---

## Locations Management

### Create a Province
```bash
curl -X POST http://localhost:9500/api/v1/provinces/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Lusaka"
  }'
```

### Get All Provinces
```bash
curl http://localhost:9500/api/v1/provinces/
```

### Create a District
```bash
curl -X POST http://localhost:9500/api/v1/districts/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Lusaka District",
    "province_id": 1
  }'
```

### Get Districts by Province
```bash
curl http://localhost:9500/api/v1/districts/province/1
```

### Create a Ward
```bash
curl -X POST http://localhost:9500/api/v1/wards/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Ward 1",
    "district_id": 1
  }'
```

### Get Wards by District
```bash
curl http://localhost:9500/api/v1/wards/district/1
```

---

## Member Management

### Create a Member
```bash
curl -X POST http://localhost:9500/api/v1/members/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Banda",
    "gender": "M",
    "age": 35,
    "nrc": "123456/78/9",
    "voters_id": "12345678",
    "contact": "0977123456",
    "ward_id": 1
  }'
```

### Get All Members
```bash
curl http://localhost:9500/api/v1/members/
```

### Search Members by Name
```bash
curl "http://localhost:9500/api/v1/members/?name=John"
```

### Get Member by NRC
```bash
curl http://localhost:9500/api/v1/members/nrc/123456/78/9
```

### Get Member by Voter's ID
```bash
curl http://localhost:9500/api/v1/members/voters-id/12345678
```

### Update a Member
```bash
curl -X PUT http://localhost:9500/api/v1/members/1 \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Banda Updated",
    "age": 36,
    "contact": "0977654321"
  }'
```

### Get Members by Ward
```bash
curl http://localhost:9500/api/v1/members/ward/1
```

---

## Form Submission

### Submit Complete Form with Members
```bash
curl -X POST http://localhost:9500/api/v1/forms/submit \
  -H "Content-Type: application/json" \
  -d '{
    "province_id": 1,
    "district_id": 1,
    "ward_id": 1,
    "prepared_by": "Alice Mwale",
    "sign": "A. Mwale",
    "contact": "0966123456",
    "submission_date": "2025-01-26",
    "members": [
      {
        "name": "Inutu Nyambe",
        "gender": "F",
        "age": 50,
        "nrc": "322904/66/1",
        "voters_id": "10165522",
        "contact": "0973334000",
        "ward_id": 1
      },
      {
        "name": "Peter Phiri",
        "gender": "M",
        "age": 42,
        "nrc": "987654/32/1",
        "voters_id": "20987654",
        "contact": "0955123456",
        "ward_id": 1
      }
    ]
  }'
```

### Get All Forms
```bash
curl http://localhost:9500/api/v1/forms/
```

### Get Form by ID
```bash
curl http://localhost:9500/api/v1/forms/1
```

### Get Forms by Ward
```bash
curl http://localhost:9500/api/v1/forms/ward/1
```

---

## Python Examples

### Using Requests Library

```python
import requests
import json
from datetime import date

BASE_URL = "http://localhost:9500/api/v1"

# Create a province
response = requests.post(
    f"{BASE_URL}/provinces/",
    json={"name": "Copperbelt"}
)
province = response.json()
print(f"Created province: {province}")

# Create a district
response = requests.post(
    f"{BASE_URL}/districts/",
    json={
        "name": "Ndola",
        "province_id": province["id"]
    }
)
district = response.json()

# Create a ward
response = requests.post(
    f"{BASE_URL}/wards/",
    json={
        "name": "Ward 5",
        "district_id": district["id"]
    }
)
ward = response.json()

# Submit a complete form
form_data = {
    "province_id": province["id"],
    "district_id": district["id"],
    "ward_id": ward["id"],
    "prepared_by": "John Doe",
    "sign": "J. Doe",
    "contact": "0977123456",
    "submission_date": str(date.today()),
    "members": [
        {
            "name": "Mary Banda",
            "gender": "F",
            "age": 28,
            "nrc": "111111/11/1",
            "voters_id": "11111111",
            "contact": "0966111111",
            "ward_id": ward["id"]
        }
    ]
}

response = requests.post(
    f"{BASE_URL}/forms/submit",
    json=form_data
)
form = response.json()
print(f"Form submitted with ID: {form['id']}")

# Search members
response = requests.get(
    f"{BASE_URL}/members/",
    params={"name": "Mary"}
)
members = response.json()
print(f"Found {len(members)} members")
```

---

## JavaScript/Fetch Examples

```javascript
const BASE_URL = 'http://localhost:9500/api/v1';

// Create a member
async function createMember() {
  const response = await fetch(`${BASE_URL}/members/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      name: 'Sarah Mwansa',
      gender: 'F',
      age: 31,
      nrc: '222222/22/2',
      voters_id: '22222222',
      contact: '0977222222',
      ward_id: 1
    })
  });
  
  const member = await response.json();
  console.log('Created member:', member);
}

// Get all members
async function getAllMembers() {
  const response = await fetch(`${BASE_URL}/members/`);
  const members = await response.json();
  console.log('Members:', members);
}

// Search members
async function searchMembers(name) {
  const response = await fetch(`${BASE_URL}/members/?name=${encodeURIComponent(name)}`);
  const members = await response.json();
  console.log('Search results:', members);
}

// Submit form
async function submitForm() {
  const formData = {
    province_id: 1,
    district_id: 1,
    ward_id: 1,
    prepared_by: 'Jane Smith',
    submission_date: new Date().toISOString().split('T')[0],
    members: [
      {
        name: 'Test Member',
        gender: 'M',
        age: 25,
        ward_id: 1
      }
    ]
  };
  
  const response = await fetch(`${BASE_URL}/forms/submit`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(formData)
  });
  
  const form = await response.json();
  console.log('Form submitted:', form);
}
```

---

## Response Examples

### Successful Member Creation
```json
{
  "id": 1,
  "name": "John Banda",
  "gender": "M",
  "age": 35,
  "nrc": "123456/78/9",
  "voters_id": "12345678",
  "contact": "0977123456",
  "ward_id": 1,
  "form_metadata_id": null,
  "created_at": "2025-01-26T10:30:00.000Z",
  "updated_at": null
}
```

### Form Submission Response
```json
{
  "id": 1,
  "province_id": 1,
  "district_id": 1,
  "ward_id": 1,
  "prepared_by": "Alice Mwale",
  "sign": "A. Mwale",
  "contact": "0966123456",
  "submission_date": "2025-01-26",
  "created_at": "2025-01-26T10:30:00.000Z",
  "updated_at": null
}
```

### Error Response
```json
{
  "detail": "Province not found"
}
```

---

## Testing with Postman

1. Import the following collection URL: `http://localhost:9500/openapi.json`
2. Set base URL as environment variable: `{{base_url}} = http://localhost:9500/api/v1`
3. Use the examples above as request templates

## Rate Limiting

Currently, no rate limiting is implemented. In production, consider implementing rate limiting for security.

## Authentication

Authentication is not yet implemented. Future versions will include:
- JWT token authentication
- Role-based access control (RBAC)
- API key authentication

---

For more examples, visit the interactive documentation at http://localhost:9500/docs

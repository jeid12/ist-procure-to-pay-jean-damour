# API Testing Guide

This guide provides complete examples for testing all API endpoints.

## Setup

### 1. Import Postman Collection
- Import `postman_collection.json` into Postman
- Collection includes all endpoints with examples
- Variables are automatically set after login

### 2. Using curl (Command Line)

Base URL: `http://localhost:8000`

## Authentication Flow

### 1. Register a New User

```bash
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "newuser@example.com",
    "password": "securepass123",
    "password2": "securepass123",
    "first_name": "John",
    "last_name": "Doe",
    "role": "staff"
  }'
```

**Response:**
```json
{
  "user": {
    "id": 1,
    "email": "newuser@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "full_name": "John Doe",
    "role": "staff"
  },
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

### 2. Login

```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "staff@test.com",
    "password": "test123"
  }'
```

**Save the access token:**
```bash
export ACCESS_TOKEN="your-access-token-here"
```

### 3. Get Current User

```bash
curl -X GET http://localhost:8000/api/auth/me/ \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

### 4. Refresh Token

```bash
curl -X POST http://localhost:8000/api/auth/token/refresh/ \
  -H "Content-Type: application/json" \
  -d '{
    "refresh": "your-refresh-token"
  }'
```

## Purchase Request Workflow

### As Staff User

#### 1. Create Purchase Request

```bash
curl -X POST http://localhost:8000/api/p2p/requests/ \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Office Equipment Purchase",
    "description": "New desks and chairs for the office",
    "amount": "5000.00",
    "items": [
      {
        "item_name": "Standing Desk",
        "description": "Adjustable height desk",
        "quantity": 10,
        "unit_price": "300.00"
      },
      {
        "item_name": "Office Chair",
        "description": "Ergonomic office chair",
        "quantity": 10,
        "unit_price": "200.00"
      }
    ]
  }'
```

**Response:**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "title": "Office Equipment Purchase",
  "description": "New desks and chairs for the office",
  "amount": "5000.00",
  "status": "PENDING",
  "status_display": "Pending",
  "requester": 1,
  "requester_details": {
    "id": 1,
    "email": "staff@test.com",
    "full_name": "John Doe"
  },
  "items": [...],
  "approvals": [
    {
      "level": "LEVEL_1",
      "status": "PENDING"
    },
    {
      "level": "LEVEL_2",
      "status": "PENDING"
    }
  ]
}
```

**Save the request ID:**
```bash
export REQUEST_ID="123e4567-e89b-12d3-a456-426614174000"
```

#### 2. Upload Proforma Invoice

```bash
curl -X POST http://localhost:8000/api/p2p/requests/$REQUEST_ID/upload_proforma/ \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -F "file=@/path/to/proforma.pdf"
```

#### 3. View My Requests

```bash
curl -X GET "http://localhost:8000/api/p2p/requests/my_requests/?page=1&page_size=10" \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

#### 4. Update Request (if PENDING or REJECTED)

```bash
curl -X PUT http://localhost:8000/api/p2p/requests/$REQUEST_ID/ \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Updated Office Equipment Purchase",
    "description": "Updated description",
    "amount": "5200.00"
  }'
```

#### 5. Upload Receipt (after approval)

```bash
curl -X POST http://localhost:8000/api/p2p/requests/$REQUEST_ID/upload_receipt/ \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -F "file=@/path/to/receipt.pdf"
```

### As Approver Level 1

#### 1. Login as Approver L1

```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "approver1@test.com",
    "password": "test123"
  }'

export APPROVER1_TOKEN="approver1-access-token"
```

#### 2. View Pending Requests

```bash
curl -X GET http://localhost:8000/api/p2p/requests/pending/ \
  -H "Authorization: Bearer $APPROVER1_TOKEN"
```

#### 3. Get Request Details

```bash
curl -X GET http://localhost:8000/api/p2p/requests/$REQUEST_ID/ \
  -H "Authorization: Bearer $APPROVER1_TOKEN"
```

#### 4. Approve Request

```bash
curl -X POST http://localhost:8000/api/p2p/requests/$REQUEST_ID/approve/ \
  -H "Authorization: Bearer $APPROVER1_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "comments": "Approved - within budget and necessary for operations"
  }'
```

**Response:**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "APPROVED_LEVEL_1",
  "approvals": [
    {
      "level": "LEVEL_1",
      "status": "APPROVED",
      "approver_details": {...},
      "comments": "Approved - within budget",
      "approved_at": "2025-11-20T10:30:00Z"
    },
    {
      "level": "LEVEL_2",
      "status": "PENDING"
    }
  ]
}
```

#### 5. Or Reject Request

```bash
curl -X POST http://localhost:8000/api/p2p/requests/$REQUEST_ID/reject/ \
  -H "Authorization: Bearer $APPROVER1_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "comments": "Rejected - over budget"
  }'
```

### As Approver Level 2

#### 1. Login as Approver L2

```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "approver2@test.com",
    "password": "test123"
  }'

export APPROVER2_TOKEN="approver2-access-token"
```

#### 2. View Requests (Level 1 Approved)

```bash
curl -X GET http://localhost:8000/api/p2p/requests/ \
  -H "Authorization: Bearer $APPROVER2_TOKEN"
```

#### 3. Final Approval

```bash
curl -X POST http://localhost:8000/api/p2p/requests/$REQUEST_ID/approve/ \
  -H "Authorization: Bearer $APPROVER2_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "comments": "Final approval granted - PO will be generated"
  }'
```

**Response:**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "APPROVED",
  "approvals": [
    {
      "level": "LEVEL_1",
      "status": "APPROVED"
    },
    {
      "level": "LEVEL_2",
      "status": "APPROVED",
      "approver_details": {...},
      "comments": "Final approval granted",
      "approved_at": "2025-11-20T11:00:00Z"
    }
  ]
}
```

**Note:** Purchase Order is automatically generated after Level 2 approval.

### As Finance User

#### 1. Login as Finance

```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "finance@test.com",
    "password": "test123"
  }'

export FINANCE_TOKEN="finance-access-token"
```

#### 2. View Approved Requests

```bash
curl -X GET "http://localhost:8000/api/p2p/requests/?status=APPROVED" \
  -H "Authorization: Bearer $FINANCE_TOKEN"
```

#### 3. View Purchase Orders

```bash
curl -X GET http://localhost:8000/api/p2p/orders/ \
  -H "Authorization: Bearer $FINANCE_TOKEN"
```

**Response:**
```json
{
  "count": 1,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": "po-uuid",
      "po_number": "PO-20251120-0001",
      "purchase_request": "123e4567-e89b-12d3-a456-426614174000",
      "vendor_name": "Office Supplies Inc",
      "total_amount": "5000.00",
      "status": "GENERATED",
      "document": "/media/purchase_orders/po-uuid/PO_20251120-0001.pdf",
      "created_at": "2025-11-20T11:00:00Z"
    }
  ]
}
```

#### 4. Get PO Details

```bash
curl -X GET http://localhost:8000/api/p2p/orders/$PO_ID/ \
  -H "Authorization: Bearer $FINANCE_TOKEN"
```

#### 5. Download PO Document

```bash
curl -X GET http://localhost:8000/media/purchase_orders/$PO_ID/PO_xxx.pdf \
  -H "Authorization: Bearer $FINANCE_TOKEN" \
  --output po_document.pdf
```

#### 6. Update PO Status

```bash
curl -X POST http://localhost:8000/api/p2p/orders/$PO_ID/update_status/ \
  -H "Authorization: Bearer $FINANCE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "SENT"
  }'
```

**Available statuses:**
- `GENERATED` - Initial state
- `SENT` - Sent to vendor
- `COMPLETED` - Transaction completed
- `CANCELLED` - Cancelled

#### 7. Upload Receipt

```bash
curl -X POST http://localhost:8000/api/p2p/requests/$REQUEST_ID/upload_receipt/ \
  -H "Authorization: Bearer $FINANCE_TOKEN" \
  -F "file=@/path/to/receipt.pdf"
```

## Filtering and Searching

### Filter by Status

```bash
curl -X GET "http://localhost:8000/api/p2p/requests/?status=PENDING" \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

### Search Requests

```bash
curl -X GET "http://localhost:8000/api/p2p/requests/?search=office" \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

### Pagination

```bash
curl -X GET "http://localhost:8000/api/p2p/requests/?page=1&page_size=10" \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

### Combined Filters

```bash
curl -X GET "http://localhost:8000/api/p2p/requests/?status=APPROVED&search=office&page=1" \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

## Error Handling

### 400 Bad Request
```json
{
  "field_name": ["Error message"]
}
```

### 401 Unauthorized
```json
{
  "detail": "Authentication credentials were not provided."
}
```

### 403 Forbidden
```json
{
  "error": "You do not have permission to perform this action"
}
```

### 404 Not Found
```json
{
  "detail": "Not found."
}
```

## Complete Test Scenario

### Scenario: Complete Purchase Request Lifecycle

```bash
# 1. Login as Staff
STAFF_TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"staff@test.com","password":"test123"}' \
  | jq -r '.access')

# 2. Create Request
REQUEST_ID=$(curl -s -X POST http://localhost:8000/api/p2p/requests/ \
  -H "Authorization: Bearer $STAFF_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title":"Test Purchase",
    "description":"Test",
    "amount":"1000.00",
    "items":[{"item_name":"Item","quantity":1,"unit_price":"1000.00"}]
  }' | jq -r '.id')

echo "Request ID: $REQUEST_ID"

# 3. Login as Approver L1
APPROVER1_TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"approver1@test.com","password":"test123"}' \
  | jq -r '.access')

# 4. Approve Level 1
curl -X POST http://localhost:8000/api/p2p/requests/$REQUEST_ID/approve/ \
  -H "Authorization: Bearer $APPROVER1_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"comments":"Approved L1"}'

# 5. Login as Approver L2
APPROVER2_TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"approver2@test.com","password":"test123"}' \
  | jq -r '.access')

# 6. Approve Level 2 (triggers PO generation)
curl -X POST http://localhost:8000/api/p2p/requests/$REQUEST_ID/approve/ \
  -H "Authorization: Bearer $APPROVER2_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"comments":"Approved L2"}'

# 7. Login as Finance
FINANCE_TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"finance@test.com","password":"test123"}' \
  | jq -r '.access')

# 8. View Purchase Order
curl -X GET http://localhost:8000/api/p2p/orders/ \
  -H "Authorization: Bearer $FINANCE_TOKEN"
```

## Python Testing Script

```python
import requests

BASE_URL = "http://localhost:8000"

def test_complete_workflow():
    # 1. Login as staff
    response = requests.post(f"{BASE_URL}/api/auth/login/", json={
        "email": "staff@test.com",
        "password": "test123"
    })
    staff_token = response.json()["access"]
    
    # 2. Create request
    response = requests.post(
        f"{BASE_URL}/api/p2p/requests/",
        headers={"Authorization": f"Bearer {staff_token}"},
        json={
            "title": "Test Request",
            "description": "Testing",
            "amount": "1000.00",
            "items": [{
                "item_name": "Test Item",
                "quantity": 1,
                "unit_price": "1000.00"
            }]
        }
    )
    request_id = response.json()["id"]
    print(f"Created request: {request_id}")
    
    # 3. Approve Level 1
    response = requests.post(f"{BASE_URL}/api/auth/login/", json={
        "email": "approver1@test.com",
        "password": "test123"
    })
    approver1_token = response.json()["access"]
    
    response = requests.post(
        f"{BASE_URL}/api/p2p/requests/{request_id}/approve/",
        headers={"Authorization": f"Bearer {approver1_token}"},
        json={"comments": "Approved L1"}
    )
    print(f"L1 Status: {response.json()['status']}")
    
    # 4. Approve Level 2
    response = requests.post(f"{BASE_URL}/api/auth/login/", json={
        "email": "approver2@test.com",
        "password": "test123"
    })
    approver2_token = response.json()["access"]
    
    response = requests.post(
        f"{BASE_URL}/api/p2p/requests/{request_id}/approve/",
        headers={"Authorization": f"Bearer {approver2_token}"},
        json={"comments": "Approved L2"}
    )
    print(f"L2 Status: {response.json()['status']}")
    
    # 5. View PO
    response = requests.post(f"{BASE_URL}/api/auth/login/", json={
        "email": "finance@test.com",
        "password": "test123"
    })
    finance_token = response.json()["access"]
    
    response = requests.get(
        f"{BASE_URL}/api/p2p/orders/",
        headers={"Authorization": f"Bearer {finance_token}"}
    )
    pos = response.json()["results"]
    print(f"Found {len(pos)} purchase orders")

if __name__ == "__main__":
    test_complete_workflow()
```

## Swagger UI Testing

1. Navigate to: http://localhost:8000/api/docs/
2. Click "Authorize" button
3. Enter: `Bearer your-access-token`
4. Test endpoints interactively

## Tips

1. **Save tokens**: Store access/refresh tokens for reuse
2. **Use jq**: Parse JSON responses easily (`apt install jq`)
3. **Set variables**: Use environment variables for tokens and IDs
4. **Check status codes**: `curl -w "\n%{http_code}\n"`
5. **Pretty print**: `curl ... | jq '.'`

## Common Issues

### Token Expired
- Refresh token or login again
- Access tokens expire after 1 hour

### Permission Denied
- Verify user role
- Check if action is allowed for current status

### File Upload Failed
- Check file size (max 10MB)
- Verify file format (PDF, JPG, PNG)
- Use `-F` for multipart/form-data

## Support

- Swagger UI: http://localhost:8000/api/docs/
- API Schema: http://localhost:8000/api/schema/
- Admin Panel: http://localhost:8000/admin/

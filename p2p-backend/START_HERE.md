# 🚀 READY TO TEST - Start Here!

## Quick Start (5 minutes)

### Step 1: Start the Application

```powershell
# In the project directory
docker-compose up --build
```

**Wait for:** "Listening at: http://0.0.0.0:8000" (takes ~2 minutes)

### Step 2: Create Test Data

```powershell
# In a new terminal window
docker-compose exec web python manage.py seed_data
```

**This creates:**
- Admin user (admin@example.com / admin123)
- Staff users (staff@test.com / test123)
- Approver L1 (approver1@test.com / test123)
- Approver L2 (approver2@test.com / test123)
- Finance user (finance@test.com / test123)
- Sample purchase requests

### Step 3: Access the Application

Open your browser to:

1. **API Documentation**: http://localhost:8000/api/docs/
   - Interactive Swagger UI
   - Test all endpoints
   - See request/response examples

2. **Admin Panel**: http://localhost:8000/admin/
   - Login: admin@example.com / admin123
   - View all data
   - Create/edit records

3. **API Root**: http://localhost:8000/api/

---

## Test the Complete Workflow

### Method 1: Using Swagger UI (Recommended)

1. Go to http://localhost:8000/api/docs/

2. **Login as Staff:**
   - Click on `POST /api/auth/login/`
   - Click "Try it out"
   - Use: `staff@test.com` / `test123`
   - Click "Execute"
   - Copy the `access` token

3. **Authorize:**
   - Click "Authorize" button at top
   - Enter: `Bearer YOUR_ACCESS_TOKEN`
   - Click "Authorize"

4. **Create Purchase Request:**
   - Click on `POST /api/p2p/requests/`
   - Click "Try it out"
   - Use the example JSON
   - Click "Execute"
   - Copy the request `id` from response

5. **Login as Approver L1:**
   - Logout (remove authorization)
   - Login with: `approver1@test.com` / `test123`
   - Authorize with new token

6. **Approve Request:**
   - Click on `POST /api/p2p/requests/{id}/approve/`
   - Enter the request ID
   - Add comment: "Approved"
   - Execute

7. **Repeat for Approver L2:**
   - Login as: `approver2@test.com` / `test123`
   - Approve the same request
   - **PO is automatically generated!**

8. **View Purchase Order:**
   - Login as: `finance@test.com` / `test123`
   - Click on `GET /api/p2p/orders/`
   - See the generated PO
   - Download the PDF document

### Method 2: Using Python Test Script

```powershell
# Make sure requests is installed
pip install requests

# Run the test script
python test_api.py
```

This will automatically test:
- ✓ Server availability
- ✓ User registration
- ✓ User login
- ✓ Request creation
- ✓ Request listing
- ✓ Approval workflow (L1 & L2)
- ✓ PO generation
- ✓ PO viewing

### Method 3: Using Postman

1. Import `postman_collection.json` into Postman
2. The collection includes all endpoints
3. Login endpoints automatically set tokens
4. Test each endpoint in sequence

### Method 4: Using curl (Command Line)

```powershell
# 1. Login
$response = Invoke-RestMethod -Uri "http://localhost:8000/api/auth/login/" `
  -Method Post `
  -ContentType "application/json" `
  -Body '{"email":"staff@test.com","password":"test123"}'
$token = $response.access

# 2. Create Request
Invoke-RestMethod -Uri "http://localhost:8000/api/p2p/requests/" `
  -Method Post `
  -Headers @{"Authorization"="Bearer $token"} `
  -ContentType "application/json" `
  -Body '{
    "title":"Test Request",
    "description":"Testing",
    "amount":"1000.00",
    "items":[{"item_name":"Test","quantity":1,"unit_price":"1000.00"}]
  }'
```

---

## What to Test

### ✅ Authentication
- [x] Register new user
- [x] Login with email/password
- [x] Get current user info
- [x] Refresh JWT token

### ✅ Staff Features
- [x] Create purchase request
- [x] Add multiple items
- [x] Upload proforma invoice
- [x] View own requests
- [x] Update pending request
- [x] Upload receipt

### ✅ Approver L1 Features
- [x] View pending requests
- [x] Approve request
- [x] Reject request
- [x] Add approval comments

### ✅ Approver L2 Features
- [x] View L1 approved requests
- [x] Final approval
- [x] Reject request
- [x] Trigger PO generation

### ✅ Finance Features
- [x] View approved requests
- [x] View purchase orders
- [x] Download PO documents
- [x] Update PO status
- [x] Upload receipts

### ✅ Workflow
- [x] Complete approval chain
- [x] Rejection at any level
- [x] Automatic PO generation
- [x] Status transitions
- [x] Audit trail

---

## Expected Results

### After Creating Request:
```json
{
  "status": "PENDING",
  "approvals": [
    {"level": "LEVEL_1", "status": "PENDING"},
    {"level": "LEVEL_2", "status": "PENDING"}
  ]
}
```

### After L1 Approval:
```json
{
  "status": "APPROVED_LEVEL_1",
  "approvals": [
    {"level": "LEVEL_1", "status": "APPROVED"},
    {"level": "LEVEL_2", "status": "PENDING"}
  ]
}
```

### After L2 Approval:
```json
{
  "status": "APPROVED",
  "approvals": [
    {"level": "LEVEL_1", "status": "APPROVED"},
    {"level": "LEVEL_2", "status": "APPROVED"}
  ]
}
```

### Generated Purchase Order:
```json
{
  "po_number": "PO-20251120-0001",
  "status": "GENERATED",
  "document": "/media/purchase_orders/.../PO_xxx.pdf",
  "total_amount": "1000.00"
}
```

---

## Common Commands

```powershell
# View logs
docker-compose logs -f web

# Access Django shell
docker-compose exec web python manage.py shell

# Create superuser
docker-compose exec web python manage.py createsuperuser

# Run migrations
docker-compose exec web python manage.py migrate

# Recreate test data
docker-compose exec web python manage.py seed_data

# Stop containers
docker-compose down

# Restart containers
docker-compose restart

# Reset everything (CAUTION: deletes data)
docker-compose down -v
docker-compose up --build
```

---

## Troubleshooting

### "Port 8000 already in use"
```powershell
# Find and kill process
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Or change port in docker-compose.yml
ports:
  - "8001:8000"
```

### "Database connection refused"
```powershell
# Restart database
docker-compose restart db

# Check database logs
docker-compose logs db
```

### "No test users"
```powershell
# Run seed data command
docker-compose exec web python manage.py seed_data
```

### "Migrations not applied"
```powershell
# Run migrations
docker-compose exec web python manage.py migrate
```

---

## Success Indicators

You'll know everything is working when:

1. ✅ Swagger UI loads at http://localhost:8000/api/docs/
2. ✅ Admin panel loads at http://localhost:8000/admin/
3. ✅ You can login as different users
4. ✅ Staff can create requests
5. ✅ Approvers can approve/reject
6. ✅ PO is generated after final approval
7. ✅ Finance can view POs and download PDFs
8. ✅ All role-based permissions work correctly

---

## Next Steps After Testing

1. **Customize Settings**
   - Edit `core/settings.py`
   - Update `.env` file
   - Configure production database

2. **Add More Features**
   - Additional approval levels
   - Email notifications
   - Custom reports
   - Integration with other systems

3. **Deploy to Production**
   - Follow `DEPLOYMENT.md`
   - Set up production database
   - Configure SSL/HTTPS
   - Set up monitoring

4. **Frontend Integration**
   - Use the API endpoints
   - JWT authentication
   - Handle file uploads
   - Implement role-based UI

---

## Support & Documentation

- 📚 **Full Documentation**: README.md
- 🚀 **Quick Start**: QUICKSTART.md
- 🌐 **Deployment**: DEPLOYMENT.md
- 🧪 **API Testing**: API_TESTING.md
- 📝 **Summary**: IMPLEMENTATION_SUMMARY.md
- 🔧 **API Docs**: http://localhost:8000/api/docs/

---

## 🎉 You're All Set!

The backend is **fully functional and ready to test**. Start with the Swagger UI and explore all the features!

**Happy Testing! 🚀**

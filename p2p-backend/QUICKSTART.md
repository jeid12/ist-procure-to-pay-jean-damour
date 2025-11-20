# Quick Start Guide

## Prerequisites
- Docker and Docker Compose installed
- OR Python 3.11+ and PostgreSQL 15+

## Quick Start with Docker (Recommended)

1. **Start the application**
   ```bash
   docker-compose up --build
   ```

2. **Wait for initialization** (about 1-2 minutes)
   - Database will be created
   - Migrations will run
   - Superuser will be created automatically
   - Server will start on http://localhost:8000

3. **Access the application**
   - API Root: http://localhost:8000/api/
   - Admin Panel: http://localhost:8000/admin/
   - Swagger Docs: http://localhost:8000/api/docs/
   - ReDoc: http://localhost:8000/api/redoc/

4. **Default Admin Credentials**
   ```
   Email: admin@example.com
   Password: admin123
   ```

5. **Create test data**
   ```bash
   docker-compose exec web python manage.py seed_data
   ```

## Quick Start without Docker

1. **Activate virtual environment**
   ```bash
   # Windows
   env\Scripts\activate
   
   # Linux/Mac
   source env/bin/activate
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Setup PostgreSQL**
   - Install PostgreSQL
   - Create database: `p2p_db`
   - Update settings or create `.env`:
     ```
     POSTGRES_DB=p2p_db
     POSTGRES_USER=postgres
     POSTGRES_PASSWORD=your_password
     POSTGRES_HOST=localhost
     POSTGRES_PORT=5432
     ```

4. **Run migrations**
   ```bash
   python manage.py migrate
   ```

5. **Create superuser**
   ```bash
   python manage.py createsuperuser
   ```

6. **Create test data**
   ```bash
   python manage.py seed_data
   ```

7. **Run server**
   ```bash
   python manage.py runserver
   ```

## Test the API

### 1. Login as Staff
```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "staff@test.com",
    "password": "test123"
  }'
```

Save the `access` token from the response.

### 2. Create a Purchase Request
```bash
curl -X POST http://localhost:8000/api/p2p/requests/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Request",
    "description": "Testing the API",
    "amount": "1000.00",
    "items": [
      {
        "item_name": "Test Item",
        "quantity": 1,
        "unit_price": "1000.00"
      }
    ]
  }'
```

### 3. Login as Approver Level 1
```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "approver1@test.com",
    "password": "test123"
  }'
```

### 4. View Pending Requests
```bash
curl -X GET http://localhost:8000/api/p2p/requests/pending/ \
  -H "Authorization: Bearer APPROVER1_ACCESS_TOKEN"
```

### 5. Approve Request
```bash
curl -X POST http://localhost:8000/api/p2p/requests/REQUEST_ID/approve/ \
  -H "Authorization: Bearer APPROVER1_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "comments": "Approved"
  }'
```

### 6. Login as Approver Level 2 and Approve Again
(Repeat steps 3-5 with approver2@test.com)

### 7. Login as Finance and View Purchase Orders
```bash
curl -X GET http://localhost:8000/api/p2p/orders/ \
  -H "Authorization: Bearer FINANCE_ACCESS_TOKEN"
```

## Test Users

After running `seed_data`, these users are available:

| Role | Email | Password | Permissions |
|------|-------|----------|-------------|
| Staff | staff@test.com | test123 | Create/view own requests |
| Staff | staff2@test.com | test123 | Create/view own requests |
| Approver L1 | approver1@test.com | test123 | Approve pending requests |
| Approver L2 | approver2@test.com | test123 | Final approval |
| Finance | finance@test.com | test123 | View POs, upload receipts |
| Admin | admin@example.com | admin123 | Full access |

## Common Commands

```bash
# View logs
docker-compose logs -f web

# Run migrations
docker-compose exec web python manage.py migrate

# Create superuser
docker-compose exec web python manage.py createsuperuser

# Access Django shell
docker-compose exec web python manage.py shell

# Run management command
docker-compose exec web python manage.py seed_data

# Stop containers
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

## Troubleshooting

### Port already in use
```bash
# Change port in docker-compose.yml
ports:
  - "8001:8000"  # Change 8000 to 8001
```

### Database connection error
```bash
# Restart database
docker-compose restart db

# Check database logs
docker-compose logs db
```

### Migrations error
```bash
# Reset database (CAUTION: deletes all data)
docker-compose down -v
docker-compose up --build
```

## Next Steps

1. Read the full README.md for detailed documentation
2. Explore the API at http://localhost:8000/api/docs/
3. Test the complete workflow with different user roles
4. Customize settings in core/settings.py
5. Deploy to production server

## Support

- API Documentation: http://localhost:8000/api/docs/
- Admin Panel: http://localhost:8000/admin/
- Full README: README.md

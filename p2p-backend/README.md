# Procure-to-Pay System Backend

A complete, production-ready Django REST API for a Procure-to-Pay (P2P) system with approval workflow, document processing, and automated purchase order generation.

## Features

### 🔐 Authentication & Authorization
- JWT-based authentication with access and refresh tokens
- Role-based access control (RBAC) for:
  - **Staff**: Create and manage purchase requests
  - **Approver Level 1**: Approve/reject initial requests
  - **Approver Level 2**: Approve/reject level 1 approved requests
  - **Finance**: View approved requests and manage purchase orders

### 📋 Purchase Request Management
- Create purchase requests with items, descriptions, and amounts
- Upload proforma invoices
- Track request status through approval workflow
- View and filter requests based on role

### ✅ Approval Workflow
- Two-level approval system
- Sequential approval process:
  - PENDING → APPROVED_LEVEL_1 → APPROVED_LEVEL_2 → APPROVED
  - Any rejection → REJECTED
- Comments and audit trail for each approval
- Automated status transitions

### 📄 Purchase Order (PO) Generation
- Automatic PO creation upon final approval
- Unique PO number generation
- PDF document generation with vendor details and items
- PO status tracking

### 🤖 OCR & Document Processing
- Extract vendor information from proforma invoices
- Parse amounts, vendor names, emails, and phone numbers
- Validate receipts against purchase orders
- Support for PDF and image formats

### 📁 File Management
- Upload and manage proforma invoices
- Upload and validate receipts
- Secure file storage with proper organization
- File type and size validation

### 📊 API Documentation
- Interactive Swagger UI documentation
- ReDoc documentation
- Complete API schema with examples

## Technology Stack

- **Framework**: Django 5.2.8
- **API**: Django REST Framework 3.16.1
- **Authentication**: djangorestframework-simplejwt 5.5.1
- **Database**: PostgreSQL (via psycopg2-binary)
- **Documentation**: drf-spectacular 0.29.0
- **OCR**: pytesseract, pdf2image
- **PDF Generation**: reportlab 4.2.5
- **Image Processing**: Pillow 10.4.0
- **CORS**: django-cors-headers 4.6.0
- **Containerization**: Docker & Docker Compose

## Project Structure

```
p2p-backend/
├── core/                      # Django project settings
│   ├── settings.py           # Configuration with PostgreSQL, JWT, CORS
│   ├── urls.py               # Main URL routing
│   └── wsgi.py               # WSGI application
├── users/                     # User management app
│   ├── models.py             # Custom User model with roles
│   ├── serializers.py        # User, registration, login serializers
│   ├── views.py              # Authentication endpoints
│   ├── admin.py              # Admin configuration
│   └── urls.py               # Auth routes
├── p2p/                       # Procure-to-Pay app
│   ├── models.py             # PurchaseRequest, RequestItem, Approval, PurchaseOrder
│   ├── serializers.py        # Comprehensive serializers with nested relationships
│   ├── views.py              # ViewSets with role-based filtering
│   ├── permissions.py        # Custom permission classes
│   ├── services.py           # Approval workflow logic
│   ├── document_processor.py # OCR and PDF generation
│   ├── admin.py              # Admin configuration
│   └── urls.py               # P2P routes
├── media/                     # Uploaded files (gitignored)
├── staticfiles/              # Static files (gitignored)
├── logs/                      # Application logs (gitignored)
├── Dockerfile                # Docker image configuration
├── docker-compose.yml        # Multi-container setup
├── entrypoint.sh             # Container initialization script
├── requirements.txt          # Python dependencies
├── .env.example              # Environment variables template
└── README.md                 # This file
```

## Installation & Setup

### Prerequisites
- Docker & Docker Compose (recommended)
- OR Python 3.11+ and PostgreSQL 15+

### Option 1: Docker Setup (Recommended)

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd p2p-backend
   ```

2. **Create environment file**
   ```bash
   copy .env.example .env
   # Edit .env with your configuration
   ```

3. **Build and start containers**
   ```bash
   docker-compose up --build
   ```

4. **Access the application**
   - API: http://localhost:8000
   - Admin: http://localhost:8000/admin
   - Swagger Docs: http://localhost:8000/api/docs/
   - ReDoc: http://localhost:8000/api/redoc/

5. **Default credentials**
   - Email: admin@example.com
   - Password: admin123

### Option 2: Local Setup

1. **Create virtual environment**
   ```bash
   python -m venv env
   env\Scripts\activate  # Windows
   # source env/bin/activate  # Linux/Mac
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Setup PostgreSQL**
   - Install PostgreSQL
   - Create database: `p2p_db`
   - Update `.env` with database credentials

4. **Run migrations**
   ```bash
   python manage.py migrate
   ```

5. **Create superuser**
   ```bash
   python manage.py createsuperuser
   ```

6. **Create logs directory**
   ```bash
   mkdir logs
   ```

7. **Run development server**
   ```bash
   python manage.py runserver
   ```

## API Endpoints

### Authentication
- `POST /api/auth/register/` - Register new user
- `POST /api/auth/login/` - Login and get JWT tokens
- `POST /api/auth/token/refresh/` - Refresh access token
- `GET /api/auth/me/` - Get current user details

### Purchase Requests
- `GET /api/p2p/requests/` - List requests (filtered by role)
- `POST /api/p2p/requests/` - Create new request (staff only)
- `GET /api/p2p/requests/{id}/` - Get request details
- `PUT /api/p2p/requests/{id}/` - Update request (staff, own requests)
- `DELETE /api/p2p/requests/{id}/` - Delete request (staff, own requests)
- `POST /api/p2p/requests/{id}/approve/` - Approve request (approvers)
- `POST /api/p2p/requests/{id}/reject/` - Reject request (approvers)
- `POST /api/p2p/requests/{id}/upload_proforma/` - Upload proforma (staff)
- `POST /api/p2p/requests/{id}/upload_receipt/` - Upload receipt (staff/finance)
- `GET /api/p2p/requests/my_requests/` - Get own requests (staff)
- `GET /api/p2p/requests/pending/` - Get pending requests (approvers)

### Purchase Orders
- `GET /api/p2p/orders/` - List purchase orders
- `GET /api/p2p/orders/{id}/` - Get PO details
- `POST /api/p2p/orders/{id}/update_status/` - Update PO status (finance)

### Documentation
- `GET /api/docs/` - Swagger UI
- `GET /api/redoc/` - ReDoc documentation
- `GET /api/schema/` - OpenAPI schema

## User Roles & Permissions

### Staff
- Create purchase requests
- View own purchase requests
- Update own requests (if PENDING or REJECTED)
- Upload proforma invoices
- Upload receipts
- View own purchase orders

### Approver Level 1
- View PENDING requests
- Approve PENDING requests → APPROVED_LEVEL_1
- Reject PENDING requests → REJECTED
- Add approval comments

### Approver Level 2
- View APPROVED_LEVEL_1 requests
- Approve APPROVED_LEVEL_1 requests → APPROVED
- Reject APPROVED_LEVEL_1 requests → REJECTED
- Add approval comments
- Triggers automatic PO generation on approval

### Finance
- View APPROVED and APPROVED_LEVEL_2 requests
- View all purchase orders
- Update PO status
- Upload receipts
- Validate receipts against POs

## Workflow Example

1. **Staff creates request**
   ```bash
   POST /api/p2p/requests/
   {
     "title": "Office Supplies",
     "description": "Monthly office supplies order",
     "amount": "1500.00",
     "items": [
       {
         "item_name": "Printer Paper",
         "quantity": 10,
         "unit_price": "50.00"
       }
     ]
   }
   ```

2. **Staff uploads proforma**
   ```bash
   POST /api/p2p/requests/{id}/upload_proforma/
   # File upload with OCR extraction
   ```

3. **Level 1 Approver reviews and approves**
   ```bash
   POST /api/p2p/requests/{id}/approve/
   {
     "comments": "Approved - within budget"
   }
   ```

4. **Level 2 Approver reviews and approves**
   ```bash
   POST /api/p2p/requests/{id}/approve/
   {
     "comments": "Final approval granted"
   }
   # Status → APPROVED
   # PO automatically generated
   ```

5. **Finance views PO**
   ```bash
   GET /api/p2p/orders/{po_id}/
   # PDF document available for download
   ```

## Testing

### Create Test Users

```python
python manage.py shell

from django.contrib.auth import get_user_model
User = get_user_model()

# Staff user
User.objects.create_user(
    email='staff@test.com',
    password='test123',
    first_name='John',
    last_name='Doe',
    role='staff'
)

# Approver Level 1
User.objects.create_user(
    email='approver1@test.com',
    password='test123',
    first_name='Jane',
    last_name='Smith',
    role='approver_level_1'
)

# Approver Level 2
User.objects.create_user(
    email='approver2@test.com',
    password='test123',
    first_name='Bob',
    last_name='Johnson',
    role='approver_level_2'
)

# Finance user
User.objects.create_user(
    email='finance@test.com',
    password='test123',
    first_name='Alice',
    last_name='Williams',
    role='finance'
)
```

### Test Workflow

1. Login as staff user
2. Create purchase request
3. Upload proforma invoice
4. Login as approver1
5. View and approve request
6. Login as approver2
7. View and approve request
8. Verify PO generation
9. Login as finance
10. View PO and upload receipt

## Deployment

### Production Considerations

1. **Environment Variables**
   - Set strong SECRET_KEY
   - Set DEBUG=False
   - Configure ALLOWED_HOSTS
   - Use secure database credentials

2. **Database**
   - Use managed PostgreSQL service
   - Enable backups
   - Configure connection pooling

3. **File Storage**
   - Use S3 or similar for media files
   - Configure CDN for static files

4. **Security**
   - Enable HTTPS
   - Configure CORS properly
   - Use environment-specific settings
   - Enable rate limiting

5. **Monitoring**
   - Configure logging
   - Set up error tracking (Sentry)
   - Monitor database performance

### Deploy to Cloud Platform

**Heroku**
```bash
# Install Heroku CLI
heroku create p2p-backend
heroku addons:create heroku-postgresql:hobby-dev
heroku config:set SECRET_KEY=your-secret-key
heroku config:set DEBUG=False
git push heroku main
heroku run python manage.py migrate
heroku run python manage.py createsuperuser
```

**AWS/DigitalOcean**
- Use Docker Compose on EC2/Droplet
- Configure RDS/Managed PostgreSQL
- Set up S3 for media files
- Use Nginx as reverse proxy
- Configure SSL with Let's Encrypt

## Troubleshooting

### Database Connection Issues
```bash
# Check PostgreSQL is running
docker-compose ps

# View logs
docker-compose logs db

# Restart containers
docker-compose restart
```

### Migration Issues
```bash
# Reset migrations (development only)
docker-compose exec web python manage.py migrate --fake p2p zero
docker-compose exec web python manage.py migrate --fake users zero
docker-compose exec web python manage.py migrate
```

### OCR Not Working
- Ensure tesseract is installed
- Check file paths are correct
- Verify file formats are supported
- Review logs for specific errors

## Contributing

1. Fork the repository
2. Create feature branch
3. Make changes with tests
4. Submit pull request

## License

MIT License - See LICENSE file for details

## Support

For issues and questions:
- Create GitHub issue
- Email: support@example.com
- Documentation: http://localhost:8000/api/docs/

## Changelog

### v1.0.0 (2025-11-20)
- Initial release
- Complete P2P workflow
- JWT authentication
- Role-based permissions
- OCR document processing
- Automated PO generation
- Docker containerization
- API documentation

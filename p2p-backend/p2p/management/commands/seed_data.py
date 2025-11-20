from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from p2p.models import PurchaseRequest, RequestItem, Approval
from decimal import Decimal

User = get_user_model()

class Command(BaseCommand):
    help = 'Create test users and sample data for the P2P system'

    def handle(self, *args, **options):
        self.stdout.write('Creating test data...\n')

        # Create users
        self.create_users()
        
        # Create sample purchase requests
        self.create_purchase_requests()
        
        self.stdout.write(self.style.SUCCESS('\n✓ Test data created successfully!'))
        self.stdout.write('\nTest Users Created:')
        self.stdout.write('  Staff: staff@test.com / test123')
        self.stdout.write('  Approver L1: approver1@test.com / test123')
        self.stdout.write('  Approver L2: approver2@test.com / test123')
        self.stdout.write('  Finance: finance@test.com / test123')
        self.stdout.write('  Admin: admin@example.com / admin123\n')

    def create_users(self):
        users_data = [
            {
                'email': 'staff@test.com',
                'password': 'test123',
                'first_name': 'John',
                'last_name': 'Doe',
                'role': 'staff'
            },
            {
                'email': 'staff2@test.com',
                'password': 'test123',
                'first_name': 'Sarah',
                'last_name': 'Miller',
                'role': 'staff'
            },
            {
                'email': 'approver1@test.com',
                'password': 'test123',
                'first_name': 'Jane',
                'last_name': 'Smith',
                'role': 'approver_level_1'
            },
            {
                'email': 'approver2@test.com',
                'password': 'test123',
                'first_name': 'Bob',
                'last_name': 'Johnson',
                'role': 'approver_level_2'
            },
            {
                'email': 'finance@test.com',
                'password': 'test123',
                'first_name': 'Alice',
                'last_name': 'Williams',
                'role': 'finance'
            },
        ]

        for user_data in users_data:
            email = user_data['email']
            if not User.objects.filter(email=email).exists():
                User.objects.create_user(**user_data)
                self.stdout.write(f'  Created user: {email}')
            else:
                self.stdout.write(f'  User exists: {email}')

    def create_purchase_requests(self):
        staff_user = User.objects.get(email='staff@test.com')
        staff2_user = User.objects.get(email='staff2@test.com')

        requests_data = [
            {
                'requester': staff_user,
                'title': 'Office Supplies - Monthly Order',
                'description': 'Monthly order for office supplies including paper, pens, and folders.',
                'amount': Decimal('1250.00'),
                'items': [
                    {'item_name': 'Printer Paper (A4)', 'quantity': 20, 'unit_price': Decimal('15.00')},
                    {'item_name': 'Blue Pens', 'quantity': 50, 'unit_price': Decimal('2.50')},
                    {'item_name': 'File Folders', 'quantity': 100, 'unit_price': Decimal('8.75')},
                ]
            },
            {
                'requester': staff_user,
                'title': 'Computer Equipment',
                'description': 'New laptops for development team',
                'amount': Decimal('4500.00'),
                'items': [
                    {'item_name': 'Dell Laptop i7', 'quantity': 3, 'unit_price': Decimal('1500.00')},
                ]
            },
            {
                'requester': staff2_user,
                'title': 'Software Licenses',
                'description': 'Annual renewal of development tools',
                'amount': Decimal('2800.00'),
                'items': [
                    {'item_name': 'JetBrains License', 'quantity': 5, 'unit_price': Decimal('200.00')},
                    {'item_name': 'Adobe Creative Cloud', 'quantity': 3, 'unit_price': Decimal('600.00')},
                ]
            },
            {
                'requester': staff2_user,
                'title': 'Marketing Materials',
                'description': 'Printed brochures and business cards',
                'amount': Decimal('850.00'),
                'items': [
                    {'item_name': 'Brochures (1000 pcs)', 'quantity': 1, 'unit_price': Decimal('600.00')},
                    {'item_name': 'Business Cards (500 pcs)', 'quantity': 1, 'unit_price': Decimal('250.00')},
                ]
            },
        ]

        for req_data in requests_data:
            items_data = req_data.pop('items')
            
            if not PurchaseRequest.objects.filter(
                title=req_data['title'],
                requester=req_data['requester']
            ).exists():
                pr = PurchaseRequest.objects.create(**req_data)
                
                # Create items
                for item_data in items_data:
                    RequestItem.objects.create(purchase_request=pr, **item_data)
                
                # Create approval chain
                from p2p.services import ApprovalWorkflowService
                ApprovalWorkflowService.create_approval_chain(pr)
                
                self.stdout.write(f'  Created request: {pr.title}')
            else:
                self.stdout.write(f'  Request exists: {req_data["title"]}')

from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
import uuid

User = get_user_model()

def upload_to_request(instance, filename):
    return f'requests/{instance.id}/{filename}'

def upload_to_po(instance, filename):
    return f'purchase_orders/{instance.id}/{filename}'

class PurchaseRequest(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED_LEVEL_1', 'Approved Level 1'),
        ('APPROVED_LEVEL_2', 'Approved Level 2'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    description = models.TextField()
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    requester = models.ForeignKey(User, on_delete=models.CASCADE, related_name='purchase_requests')
    proforma_invoice = models.FileField(upload_to=upload_to_request, null=True, blank=True)
    receipt = models.FileField(upload_to=upload_to_request, null=True, blank=True)
    extracted_data = models.JSONField(null=True, blank=True)  # OCR extracted data
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.status}"

    def can_approve(self, user):
        """Check if user can approve this request"""
        if self.status == 'PENDING' and user.role == 'approver_level_1':
            return True
        elif self.status == 'APPROVED_LEVEL_1' and user.role == 'approver_level_2':
            return True
        return False

    def can_reject(self, user):
        """Check if user can reject this request"""
        return user.role in ['approver_level_1', 'approver_level_2'] and self.status not in ['APPROVED', 'REJECTED']

class RequestItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    purchase_request = models.ForeignKey(PurchaseRequest, on_delete=models.CASCADE, related_name='items')
    item_name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    total_price = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])

    def __str__(self):
        return f"{self.item_name} x {self.quantity}"

    def save(self, *args, **kwargs):
        self.total_price = self.quantity * self.unit_price
        super().save(*args, **kwargs)

class Approval(models.Model):
    LEVEL_CHOICES = [
        ('LEVEL_1', 'Level 1'),
        ('LEVEL_2', 'Level 2'),
    ]

    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    purchase_request = models.ForeignKey(PurchaseRequest, on_delete=models.CASCADE, related_name='approvals')
    level = models.CharField(max_length=10, choices=LEVEL_CHOICES)
    approver = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approvals')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    comments = models.TextField(blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['level', 'created_at']
        unique_together = ['purchase_request', 'level']

    def __str__(self):
        return f"{self.purchase_request.title} - {self.level} - {self.status}"

class PurchaseOrder(models.Model):
    STATUS_CHOICES = [
        ('GENERATED', 'Generated'),
        ('SENT', 'Sent to Vendor'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    po_number = models.CharField(max_length=50, unique=True)
    purchase_request = models.OneToOneField(PurchaseRequest, on_delete=models.CASCADE, related_name='purchase_order')
    vendor_name = models.CharField(max_length=255, blank=True)
    vendor_address = models.TextField(blank=True)
    vendor_email = models.EmailField(blank=True)
    vendor_phone = models.CharField(max_length=20, blank=True)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='GENERATED')
    document = models.FileField(upload_to=upload_to_po, null=True, blank=True)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_pos')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"PO-{self.po_number}"

    @staticmethod
    def generate_po_number():
        """Generate unique PO number"""
        from datetime import datetime
        date_str = datetime.now().strftime('%Y%m%d')
        last_po = PurchaseOrder.objects.filter(po_number__startswith=f'PO-{date_str}').order_by('-po_number').first()
        if last_po:
            last_num = int(last_po.po_number.split('-')[-1])
            new_num = last_num + 1
        else:
            new_num = 1
        return f'PO-{date_str}-{new_num:04d}'
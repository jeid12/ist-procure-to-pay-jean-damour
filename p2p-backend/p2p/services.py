from django.utils import timezone
from django.db import transaction
from .models import PurchaseRequest, Approval, PurchaseOrder
from .document_processor import generate_po_document
import logging

logger = logging.getLogger(__name__)

class ApprovalWorkflowService:
    """Service for handling purchase request approval workflow"""
    
    @staticmethod
    @transaction.atomic
    def create_approval_chain(purchase_request):
        """Create approval records for a new purchase request"""
        Approval.objects.create(
            purchase_request=purchase_request,
            level='LEVEL_1',
            status='PENDING'
        )
        Approval.objects.create(
            purchase_request=purchase_request,
            level='LEVEL_2',
            status='PENDING'
        )
    
    @staticmethod
    @transaction.atomic
    def approve_request(purchase_request, user, comments=''):
        """Approve a purchase request at the appropriate level"""
        if not purchase_request.can_approve(user):
            raise ValueError('You are not authorized to approve this request at this stage')
        
        # Determine approval level
        if user.role == 'approver_level_1':
            approval_level = 'LEVEL_1'
            new_status = 'APPROVED_LEVEL_1'
        elif user.role == 'approver_level_2':
            approval_level = 'LEVEL_2'
            new_status = 'APPROVED_LEVEL_2'
        else:
            raise ValueError('Invalid approver role')
        
        # Update approval record
        approval = Approval.objects.get(
            purchase_request=purchase_request,
            level=approval_level
        )
        approval.status = 'APPROVED'
        approval.approver = user
        approval.comments = comments
        approval.approved_at = timezone.now()
        approval.save()
        
        # Update purchase request status
        purchase_request.status = new_status
        purchase_request.save()
        
        # Check if all approvals are complete
        if new_status == 'APPROVED_LEVEL_2':
            ApprovalWorkflowService.finalize_approval(purchase_request, user)
        
        return purchase_request
    
    @staticmethod
    @transaction.atomic
    def reject_request(purchase_request, user, comments=''):
        """Reject a purchase request"""
        if not purchase_request.can_reject(user):
            raise ValueError('You are not authorized to reject this request')
        
        # Determine approval level
        if user.role == 'approver_level_1':
            approval_level = 'LEVEL_1'
        elif user.role == 'approver_level_2':
            approval_level = 'LEVEL_2'
        else:
            raise ValueError('Invalid approver role')
        
        # Update approval record
        approval = Approval.objects.get(
            purchase_request=purchase_request,
            level=approval_level
        )
        approval.status = 'REJECTED'
        approval.approver = user
        approval.comments = comments
        approval.approved_at = timezone.now()
        approval.save()
        
        # Update purchase request status
        purchase_request.status = 'REJECTED'
        purchase_request.save()
        
        return purchase_request
    
    @staticmethod
    @transaction.atomic
    def finalize_approval(purchase_request, user):
        """Finalize approval and generate PO"""
        purchase_request.status = 'APPROVED'
        purchase_request.save()
        
        # Generate PO number
        po_number = PurchaseOrder.generate_po_number()
        
        # Extract vendor info from extracted_data if available
        vendor_info = {}
        if purchase_request.extracted_data:
            vendor_info = {
                'vendor_name': purchase_request.extracted_data.get('vendor_name', ''),
                'vendor_address': purchase_request.extracted_data.get('vendor_address', ''),
                'vendor_email': purchase_request.extracted_data.get('vendor_email', ''),
                'vendor_phone': purchase_request.extracted_data.get('vendor_phone', ''),
            }
        
        # Create Purchase Order
        po = PurchaseOrder.objects.create(
            po_number=po_number,
            purchase_request=purchase_request,
            total_amount=purchase_request.amount,
            created_by=user,
            **vendor_info
        )
        
        # Generate PO document
        try:
            po_document = generate_po_document(po)
            po.document = po_document
            po.save()
            logger.info(f"Generated PO document for {po.po_number}")
        except Exception as e:
            logger.error(f"Failed to generate PO document: {str(e)}")
        
        return po

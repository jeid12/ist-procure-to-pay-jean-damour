from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import PurchaseRequest, RequestItem, Approval, PurchaseOrder

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.ReadOnlyField()
    
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'full_name', 'role']

class RequestItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = RequestItem
        fields = ['id', 'item_name', 'description', 'quantity', 'unit_price', 'total_price']
        read_only_fields = ['id', 'total_price']

class ApprovalSerializer(serializers.ModelSerializer):
    approver_details = UserSerializer(source='approver', read_only=True)
    level_display = serializers.CharField(source='get_level_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Approval
        fields = ['id', 'level', 'level_display', 'status', 'status_display', 
                  'approver', 'approver_details', 'comments', 'approved_at', 'created_at']
        read_only_fields = ['id', 'approver', 'approved_at', 'created_at']

class PurchaseRequestListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views"""
    requester_details = UserSerializer(source='requester', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    has_proforma = serializers.SerializerMethodField()
    has_receipt = serializers.SerializerMethodField()
    
    class Meta:
        model = PurchaseRequest
        fields = ['id', 'title', 'description', 'amount', 'status', 'status_display',
                  'requester', 'requester_details', 'has_proforma', 'has_receipt',
                  'created_at', 'updated_at']
        read_only_fields = ['id', 'requester', 'created_at', 'updated_at']
    
    def get_has_proforma(self, obj):
        return bool(obj.proforma_invoice)
    
    def get_has_receipt(self, obj):
        return bool(obj.receipt)

class PurchaseRequestDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer with nested relationships"""
    requester_details = UserSerializer(source='requester', read_only=True)
    items = RequestItemSerializer(many=True, required=False)
    approvals = ApprovalSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = PurchaseRequest
        fields = ['id', 'title', 'description', 'amount', 'status', 'status_display',
                  'requester', 'requester_details', 'proforma_invoice', 'receipt',
                  'extracted_data', 'items', 'approvals', 'created_at', 'updated_at']
        read_only_fields = ['id', 'requester', 'status', 'extracted_data', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        items_data = validated_data.pop('items', [])
        purchase_request = PurchaseRequest.objects.create(**validated_data)
        
        # Create items
        for item_data in items_data:
            RequestItem.objects.create(purchase_request=purchase_request, **item_data)
        
        # Create approval chain
        from .services import ApprovalWorkflowService
        ApprovalWorkflowService.create_approval_chain(purchase_request)
        
        return purchase_request
    
    def update(self, instance, validated_data):
        items_data = validated_data.pop('items', None)
        
        # Update purchase request fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update items if provided
        if items_data is not None:
            # Delete existing items
            instance.items.all().delete()
            # Create new items
            for item_data in items_data:
                RequestItem.objects.create(purchase_request=instance, **item_data)
        
        return instance

class PurchaseRequestCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating purchase requests"""
    items = RequestItemSerializer(many=True, required=False)
    
    class Meta:
        model = PurchaseRequest
        fields = ['title', 'description', 'amount', 'proforma_invoice', 'items']
    
    def create(self, validated_data):
        items_data = validated_data.pop('items', [])
        request = self.context.get('request')
        purchase_request = PurchaseRequest.objects.create(
            requester=request.user,
            **validated_data
        )
        
        # Create items
        for item_data in items_data:
            RequestItem.objects.create(purchase_request=purchase_request, **item_data)
        
        # Create approval chain
        from .services import ApprovalWorkflowService
        ApprovalWorkflowService.create_approval_chain(purchase_request)
        
        # Extract data from proforma if uploaded
        if purchase_request.proforma_invoice:
            from .document_processor import extract_proforma_data
            try:
                extracted_data = extract_proforma_data(purchase_request.proforma_invoice.path)
                purchase_request.extracted_data = extracted_data
                purchase_request.save()
            except Exception:
                pass  # Continue even if extraction fails
        
        return purchase_request

class ApprovalActionSerializer(serializers.Serializer):
    """Serializer for approval/rejection actions"""
    comments = serializers.CharField(required=False, allow_blank=True)

class PurchaseOrderSerializer(serializers.ModelSerializer):
    purchase_request_details = PurchaseRequestListSerializer(source='purchase_request', read_only=True)
    created_by_details = UserSerializer(source='created_by', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = PurchaseOrder
        fields = ['id', 'po_number', 'purchase_request', 'purchase_request_details',
                  'vendor_name', 'vendor_address', 'vendor_email', 'vendor_phone',
                  'total_amount', 'status', 'status_display', 'document', 'notes',
                  'created_by', 'created_by_details', 'created_at', 'updated_at']
        read_only_fields = ['id', 'po_number', 'purchase_request', 'created_by', 
                           'created_at', 'updated_at']

class FileUploadSerializer(serializers.Serializer):
    """Serializer for file uploads"""
    file = serializers.FileField()
    
    def validate_file(self, value):
        # Validate file size (max 10MB)
        if value.size > 10 * 1024 * 1024:
            raise serializers.ValidationError("File size cannot exceed 10MB")
        
        # Validate file extension
        allowed_extensions = ['.pdf', '.jpg', '.jpeg', '.png']
        ext = value.name.split('.')[-1].lower()
        if f'.{ext}' not in allowed_extensions:
            raise serializers.ValidationError(
                f"File type not supported. Allowed types: {', '.join(allowed_extensions)}"
            )
        
        return value
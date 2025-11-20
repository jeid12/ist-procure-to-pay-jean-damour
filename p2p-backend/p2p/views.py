from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample, extend_schema_view
from drf_spectacular.types import OpenApiTypes
from .models import PurchaseRequest, RequestItem, Approval, PurchaseOrder
from .serializers import (
    PurchaseRequestListSerializer, PurchaseRequestDetailSerializer,
    PurchaseRequestCreateSerializer, RequestItemSerializer,
    ApprovalSerializer, ApprovalActionSerializer,
    PurchaseOrderSerializer, FileUploadSerializer
)
from .permissions import (
    IsStaff, IsStaffOwner, IsAnyApprover,
    IsFinance, CanViewPurchaseRequest, CanModifyPurchaseRequest
)
from .services import ApprovalWorkflowService
from .document_processor import extract_proforma_data, validate_receipt_against_po
import logging

logger = logging.getLogger(__name__)

class StandardPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

@extend_schema_view(
    list=extend_schema(
        description="List purchase requests (filtered by user role)",
        parameters=[
            OpenApiParameter(name='status', type=OpenApiTypes.STR, description='Filter by status', 
                           enum=['PENDING', 'APPROVED_LEVEL_1', 'APPROVED_LEVEL_2', 'APPROVED', 'REJECTED']),
            OpenApiParameter(name='search', type=OpenApiTypes.STR, description='Search in title and description'),
            OpenApiParameter(name='page', type=OpenApiTypes.INT, description='Page number'),
            OpenApiParameter(name='page_size', type=OpenApiTypes.INT, description='Items per page (max 100)'),
        ]
    ),
    retrieve=extend_schema(
        description="Get detailed information about a specific purchase request"
    ),
    create=extend_schema(
        description="Create a new purchase request (staff only)",
        request=PurchaseRequestCreateSerializer,
        responses={
            201: {
                'type': 'object',
                'properties': {
                    'message': {'type': 'string'},
                    'data': PurchaseRequestDetailSerializer
                }
            },
            400: {
                'type': 'object',
                'properties': {
                    'message': {'type': 'string'},
                    'errors': {'type': 'object'}
                }
            }
        },
        examples=[
            OpenApiExample(
                'Create Request Example',
                value={
                    'title': 'Office Supplies',
                    'description': 'Purchase of printer paper and pens',
                    'amount': 150.00,
                    'items': [
                        {
                            'item_name': 'Printer Paper A4',
                            'description': 'White 80gsm',
                            'quantity': 10,
                            'unit_price': 5.00
                        },
                        {
                            'item_name': 'Blue Pens',
                            'description': 'Ballpoint pens',
                            'quantity': 50,
                            'unit_price': 2.00
                        }
                    ]
                },
                request_only=True
            )
        ]
    ),
    update=extend_schema(
        description="Update a purchase request (only PENDING or REJECTED status, own requests)",
        request=PurchaseRequestCreateSerializer,
        responses={
            200: {
                'type': 'object',
                'properties': {
                    'message': {'type': 'string'},
                    'data': PurchaseRequestDetailSerializer
                }
            },
            400: {
                'type': 'object',
                'properties': {
                    'message': {'type': 'string'},
                    'errors': {'type': 'object'}
                }
            }
        }
    ),
    partial_update=extend_schema(
        description="Partially update a purchase request",
        request=PurchaseRequestCreateSerializer,
        responses={
            200: {
                'type': 'object',
                'properties': {
                    'message': {'type': 'string'},
                    'data': PurchaseRequestDetailSerializer
                }
            }
        }
    ),
    destroy=extend_schema(
        description="Delete a purchase request (only PENDING or REJECTED status)",
        responses={
            204: {
                'type': 'object',
                'properties': {
                    'message': {'type': 'string'}
                }
            }
        }
    )
)
class PurchaseRequestViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Purchase Requests with role-based access control
    
    Staff: Create, update their own requests, upload files
    Approvers: View pending requests, approve/reject
    Finance: View approved requests, upload receipts
    """
    queryset = PurchaseRequest.objects.all().select_related('requester').prefetch_related('items', 'approvals')
    pagination_class = StandardPagination
    
    def get_serializer_class(self):
        if self.action == 'list':
            return PurchaseRequestListSerializer
        elif self.action == 'create':
            return PurchaseRequestCreateSerializer
        return PurchaseRequestDetailSerializer
    
    def get_permissions(self):
        if self.action == 'create':
            return [IsAuthenticated(), IsStaff()]
        elif self.action in ['update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), CanModifyPurchaseRequest()]
        elif self.action in ['approve', 'reject']:
            return [IsAuthenticated(), IsAnyApprover()]
        elif self.action in ['upload_proforma', 'upload_receipt']:
            return [IsAuthenticated()]
        return [IsAuthenticated(), CanViewPurchaseRequest()]
    
    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset()
        
        # Filter based on user role
        if user.role == 'staff':
            # Staff can only see their own requests
            queryset = queryset.filter(requester=user)
        elif user.role == 'approver_level_1':
            # Level 1 approvers see PENDING requests
            queryset = queryset.filter(status='PENDING')
        elif user.role == 'approver_level_2':
            # Level 2 approvers see APPROVED_LEVEL_1 requests
            queryset = queryset.filter(status='APPROVED_LEVEL_1')
        elif user.role == 'finance':
            # Finance sees approved requests
            queryset = queryset.filter(status__in=['APPROVED', 'APPROVED_LEVEL_2'])
        
        # Apply filters
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | 
                Q(description__icontains=search)
            )
        
        return queryset
    
    def create(self, request, *args, **kwargs):
        """Create a new purchase request"""
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            self.perform_create(serializer)
            # Use detail serializer to include all fields including id
            instance = serializer.instance
            detail_serializer = PurchaseRequestDetailSerializer(instance)
            headers = self.get_success_headers(serializer.data)
            return Response({
                'message': 'Purchase request created successfully',
                'data': detail_serializer.data
            }, status=status.HTTP_201_CREATED, headers=headers)
        return Response({
            'message': 'Purchase request creation failed',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    def update(self, request, *args, **kwargs):
        """Update a purchase request"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if serializer.is_valid():
            self.perform_update(serializer)
            return Response({
                'message': 'Purchase request updated successfully',
                'data': serializer.data
            }, status=status.HTTP_200_OK)
        return Response({
            'message': 'Purchase request update failed',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    def destroy(self, request, *args, **kwargs):
        """Delete a purchase request"""
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({
            'message': 'Purchase request deleted successfully'
        }, status=status.HTTP_204_NO_CONTENT)
    
    def perform_create(self, serializer):
        # Don't pass requester here - it's handled in the serializer's create method
        serializer.save()
    
    @extend_schema(
        description="Approve a purchase request (approvers only)",
        request=ApprovalActionSerializer,
        responses={
            200: {
                'type': 'object',
                'properties': {
                    'message': {'type': 'string'},
                    'data': PurchaseRequestDetailSerializer
                }
            },
            400: {
                'type': 'object',
                'properties': {
                    'message': {'type': 'string'},
                    'error': {'type': 'string'}
                }
            }
        },
        examples=[
            OpenApiExample(
                'Approve Example',
                value={'comments': 'Approved - budget available'},
                request_only=True
            )
        ]
    )
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsAnyApprover])
    def approve(self, request, pk=None):
        """Approve a purchase request"""
        purchase_request = self.get_object()
        serializer = ApprovalActionSerializer(data=request.data)
        
        if serializer.is_valid():
            try:
                ApprovalWorkflowService.approve_request(
                    purchase_request,
                    request.user,
                    serializer.validated_data.get('comments', '')
                )
                purchase_request.refresh_from_db()
                return Response({
                    'message': 'Purchase request approved successfully',
                    'data': PurchaseRequestDetailSerializer(purchase_request).data
                }, status=status.HTTP_200_OK)
            except ValueError as e:
                return Response({
                    'message': 'Approval failed',
                    'error': str(e)
                }, status=status.HTTP_400_BAD_REQUEST)
        return Response({
            'message': 'Validation failed',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    @extend_schema(
        description="Reject a purchase request (approvers only)",
        request=ApprovalActionSerializer,
        responses={
            200: {
                'type': 'object',
                'properties': {
                    'message': {'type': 'string'},
                    'data': PurchaseRequestDetailSerializer
                }
            },
            400: {
                'type': 'object',
                'properties': {
                    'message': {'type': 'string'},
                    'error': {'type': 'string'}
                }
            }
        },
        examples=[
            OpenApiExample(
                'Reject Example',
                value={'comments': 'Rejected - insufficient budget justification'},
                request_only=True
            )
        ]
    )
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsAnyApprover])
    def reject(self, request, pk=None):
        """Reject a purchase request"""
        purchase_request = self.get_object()
        serializer = ApprovalActionSerializer(data=request.data)
        
        if serializer.is_valid():
            try:
                ApprovalWorkflowService.reject_request(
                    purchase_request,
                    request.user,
                    serializer.validated_data.get('comments', '')
                )
                purchase_request.refresh_from_db()
                return Response({
                    'message': 'Purchase request rejected successfully',
                    'data': PurchaseRequestDetailSerializer(purchase_request).data
                }, status=status.HTTP_200_OK)
            except ValueError as e:
                return Response({
                    'message': 'Rejection failed',
                    'error': str(e)
                }, status=status.HTTP_400_BAD_REQUEST)
        return Response({
            'message': 'Validation failed',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    @extend_schema(
        description="Upload proforma invoice (staff - own requests only)",
        request={
            'multipart/form-data': {
                'type': 'object',
                'properties': {
                    'file': {
                        'type': 'string',
                        'format': 'binary',
                        'description': 'Proforma invoice file (PDF or image, max 10MB)'
                    }
                }
            }
        },
        responses={
            200: {
                'type': 'object',
                'properties': {
                    'message': {'type': 'string'},
                    'data': PurchaseRequestDetailSerializer
                }
            },
            400: {
                'type': 'object',
                'properties': {
                    'message': {'type': 'string'},
                    'errors': {'type': 'object'}
                }
            },
            403: {
                'type': 'object',
                'properties': {
                    'message': {'type': 'string'},
                    'error': {'type': 'string'}
                }
            }
        }
    )
    @action(detail=True, methods=['post'])
    def upload_proforma(self, request, pk=None):
        """Upload proforma invoice"""
        purchase_request = self.get_object()
        
        # Check permissions
        if request.user.role != 'staff' or purchase_request.requester != request.user:
            return Response({
                'message': 'Permission denied',
                'error': 'You do not have permission to upload files for this request'
            }, status=status.HTTP_403_FORBIDDEN)
        
        serializer = FileUploadSerializer(data=request.data)
        if serializer.is_valid():
            purchase_request.proforma_invoice = serializer.validated_data['file']
            purchase_request.save()
            
            # Extract data from proforma
            try:
                extracted_data = extract_proforma_data(purchase_request.proforma_invoice.path)
                purchase_request.extracted_data = extracted_data
                purchase_request.save()
                logger.info(f"Extracted data from proforma: {extracted_data}")
            except Exception as e:
                logger.error(f"Failed to extract proforma data: {str(e)}")
            
            return Response({
                'message': 'Proforma invoice uploaded successfully',
                'data': PurchaseRequestDetailSerializer(purchase_request).data
            }, status=status.HTTP_200_OK)
        return Response({
            'message': 'File upload failed',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    @extend_schema(
        description="Upload receipt (staff - own requests, finance - all approved requests)",
        request={
            'multipart/form-data': {
                'type': 'object',
                'properties': {
                    'file': {
                        'type': 'string',
                        'format': 'binary',
                        'description': 'Receipt file (PDF or image, max 10MB)'
                    }
                }
            }
        },
        responses={
            200: {
                'type': 'object',
                'properties': {
                    'message': {'type': 'string'},
                    'data': PurchaseRequestDetailSerializer,
                    'receipt_validation': {'type': 'object'}
                }
            },
            400: {
                'type': 'object',
                'properties': {
                    'message': {'type': 'string'},
                    'errors': {'type': 'object'}
                }
            },
            403: {
                'type': 'object',
                'properties': {
                    'message': {'type': 'string'},
                    'error': {'type': 'string'}
                }
            }
        }
    )
    @action(detail=True, methods=['post'])
    def upload_receipt(self, request, pk=None):
        """Upload receipt (staff or finance can upload)"""
        purchase_request = self.get_object()
        
        # Check permissions
        if request.user.role not in ['staff', 'finance']:
            return Response({
                'message': 'Permission denied',
                'error': 'You do not have permission to upload receipts'
            }, status=status.HTTP_403_FORBIDDEN)
        
        if request.user.role == 'staff' and purchase_request.requester != request.user:
            return Response({
                'message': 'Permission denied',
                'error': 'You can only upload receipts for your own requests'
            }, status=status.HTTP_403_FORBIDDEN)
        
        serializer = FileUploadSerializer(data=request.data)
        if serializer.is_valid():
            purchase_request.receipt = serializer.validated_data['file']
            purchase_request.save()
            
            # Validate receipt against PO if it exists
            validation_result = None
            if hasattr(purchase_request, 'purchase_order'):
                try:
                    validation_result = validate_receipt_against_po(
                        purchase_request.receipt.path,
                        purchase_request.purchase_order
                    )
                    logger.info(f"Receipt validation result: {validation_result}")
                except Exception as e:
                    logger.error(f"Failed to validate receipt: {str(e)}")
            
            response_data = {
                'message': 'Receipt uploaded successfully',
                'data': PurchaseRequestDetailSerializer(purchase_request).data
            }
            if validation_result:
                response_data['receipt_validation'] = validation_result
            
            return Response(response_data, status=status.HTTP_200_OK)
        return Response({
            'message': 'File upload failed',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    @extend_schema(
        description="Get current user's purchase requests (staff only)",
        responses={
            200: {
                'type': 'object',
                'properties': {
                    'message': {'type': 'string'},
                    'count': {'type': 'integer'},
                    'data': {'type': 'array', 'items': PurchaseRequestListSerializer}
                }
            },
            403: {
                'type': 'object',
                'properties': {
                    'message': {'type': 'string'},
                    'error': {'type': 'string'}
                }
            }
        }
    )
    @action(detail=False, methods=['get'])
    def my_requests(self, request):
        """Get current user's requests (for staff)"""
        if request.user.role != 'staff':
            return Response({
                'message': 'Access denied',
                'error': 'This endpoint is only for staff users'
            }, status=status.HTTP_403_FORBIDDEN)
        
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'message': 'Requests retrieved successfully',
            'count': queryset.count(),
            'data': serializer.data
        }, status=status.HTTP_200_OK)
    
    @extend_schema(
        description="Get pending purchase requests for approval (approvers only)",
        responses={200: PurchaseRequestListSerializer(many=True)}
    )
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated, IsAnyApprover])
    def pending(self, request):
        """Get pending requests for approvers"""
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

@extend_schema_view(
    list=extend_schema(
        description="List purchase orders (role-based filtering)",
        parameters=[
            OpenApiParameter(name='status', type=OpenApiTypes.STR, description='Filter by status',
                           enum=['GENERATED', 'SENT', 'COMPLETED', 'CANCELLED']),
            OpenApiParameter(name='page', type=OpenApiTypes.INT, description='Page number'),
            OpenApiParameter(name='page_size', type=OpenApiTypes.INT, description='Items per page (max 100)'),
        ]
    ),
    retrieve=extend_schema(
        description="Get detailed information about a specific purchase order"
    )
)
class PurchaseOrderViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for Purchase Orders (read-only)
    
    Finance: View all purchase orders
    Staff: View their own purchase orders
    """
    queryset = PurchaseOrder.objects.all().select_related('purchase_request', 'created_by')
    serializer_class = PurchaseOrderSerializer
    pagination_class = StandardPagination
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset()
        
        if user.role == 'staff':
            # Staff can only see POs for their own requests
            queryset = queryset.filter(purchase_request__requester=user)
        elif user.role == 'finance':
            # Finance can see all POs
            pass
        else:
            # Approvers can see POs for requests they approved
            queryset = queryset.filter(
                purchase_request__approvals__approver=user,
                purchase_request__approvals__status='APPROVED'
            ).distinct()
        
        # Apply filters
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        return queryset
    
    @extend_schema(
        description="Update purchase order status (finance only)",
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'status': {
                        'type': 'string',
                        'enum': ['GENERATED', 'SENT', 'COMPLETED', 'CANCELLED'],
                        'description': 'New status for the purchase order'
                    }
                },
                'required': ['status']
            }
        },
        responses={
            200: {
                'type': 'object',
                'properties': {
                    'message': {'type': 'string'},
                    'data': PurchaseOrderSerializer
                }
            },
            400: {
                'type': 'object',
                'properties': {
                    'message': {'type': 'string'},
                    'error': {'type': 'string'}
                }
            }
        },
        examples=[
            OpenApiExample(
                'Update Status Example',
                value={'status': 'SENT'},
                request_only=True
            )
        ]
    )
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsFinance])
    def update_status(self, request, pk=None):
        """Update PO status (finance only)"""
        po = self.get_object()
        new_status = request.data.get('status')
        
        if new_status not in dict(PurchaseOrder.STATUS_CHOICES).keys():
            return Response({
                'message': 'Invalid status',
                'error': f'Status must be one of: {", ".join(dict(PurchaseOrder.STATUS_CHOICES).keys())}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if request.user.role != 'finance':
            return Response({
                'message': 'Permission denied',
                'error': 'Only finance users can update the status of purchase orders.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        po.status = new_status
        po.save()
        
        return Response({
            'message': 'Purchase order status updated successfully',
            'data': self.get_serializer(po).data
        }, status=status.HTTP_200_OK)
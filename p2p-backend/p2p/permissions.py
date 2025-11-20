from rest_framework import permissions

class IsStaff(permissions.BasePermission):
    """Permission for staff users"""
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'staff'

class IsStaffOwner(permissions.BasePermission):
    """Permission for staff users to access their own requests"""
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'staff'
    
    def has_object_permission(self, request, view, obj):
        # Staff can only modify their own requests
        return obj.requester == request.user

class IsApproverLevel1(permissions.BasePermission):
    """Permission for level 1 approvers"""
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'approver_level_1'

class IsApproverLevel2(permissions.BasePermission):
    """Permission for level 2 approvers"""
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'approver_level_2'

class IsAnyApprover(permissions.BasePermission):
    """Permission for any approver"""
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and \
               request.user.role in ['approver_level_1', 'approver_level_2']

class IsFinance(permissions.BasePermission):
    """Permission for finance users"""
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'finance'

class CanViewPurchaseRequest(permissions.BasePermission):
    """
    Permission to view purchase requests:
    - Staff can view their own requests
    - Approvers can view requests they need to approve
    - Finance can view approved requests
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        user = request.user
        
        # Staff can view their own requests
        if user.role == 'staff':
            return obj.requester == user
        
        # Approvers can view requests at their level
        if user.role == 'approver_level_1':
            return obj.status in ['PENDING', 'APPROVED_LEVEL_1', 'APPROVED_LEVEL_2', 'APPROVED', 'REJECTED']
        
        if user.role == 'approver_level_2':
            return obj.status in ['APPROVED_LEVEL_1', 'APPROVED_LEVEL_2', 'APPROVED', 'REJECTED']
        
        # Finance can view approved requests
        if user.role == 'finance':
            return obj.status in ['APPROVED', 'APPROVED_LEVEL_2']
        
        return False

class CanModifyPurchaseRequest(permissions.BasePermission):
    """
    Permission to modify purchase requests:
    - Only staff can modify their own requests
    - Only if request is PENDING or REJECTED
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'staff'
    
    def has_object_permission(self, request, view, obj):
        # Staff can only modify their own requests
        if obj.requester != request.user:
            return False
        
        # Can only modify if PENDING or REJECTED
        return obj.status in ['PENDING', 'REJECTED']
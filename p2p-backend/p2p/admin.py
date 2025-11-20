from django.contrib import admin
from .models import PurchaseRequest, RequestItem, Approval, PurchaseOrder

class RequestItemInline(admin.TabularInline):
    model = RequestItem
    extra = 1

class ApprovalInline(admin.TabularInline):
    model = Approval
    extra = 0
    readonly_fields = ['level', 'approver', 'status', 'approved_at']

@admin.register(PurchaseRequest)
class PurchaseRequestAdmin(admin.ModelAdmin):
    list_display = ['title', 'requester', 'amount', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['title', 'description', 'requester__email']
    readonly_fields = ['id', 'created_at', 'updated_at']
    inlines = [RequestItemInline, ApprovalInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'title', 'description', 'amount', 'requester', 'status')
        }),
        ('Files', {
            'fields': ('proforma_invoice', 'receipt')
        }),
        ('Extracted Data', {
            'fields': ('extracted_data',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )

@admin.register(RequestItem)
class RequestItemAdmin(admin.ModelAdmin):
    list_display = ['item_name', 'purchase_request', 'quantity', 'unit_price', 'total_price']
    search_fields = ['item_name', 'description']

@admin.register(Approval)
class ApprovalAdmin(admin.ModelAdmin):
    list_display = ['purchase_request', 'level', 'status', 'approver', 'approved_at']
    list_filter = ['level', 'status', 'approved_at']
    search_fields = ['purchase_request__title', 'approver__email']
    readonly_fields = ['id', 'created_at']

@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ['po_number', 'purchase_request', 'vendor_name', 'total_amount', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['po_number', 'vendor_name', 'purchase_request__title']
    readonly_fields = ['id', 'po_number', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'po_number', 'purchase_request', 'total_amount', 'status')
        }),
        ('Vendor Information', {
            'fields': ('vendor_name', 'vendor_address', 'vendor_email', 'vendor_phone')
        }),
        ('Document', {
            'fields': ('document', 'notes')
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at')
        }),
    )
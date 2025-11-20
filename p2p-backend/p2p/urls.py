from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PurchaseRequestViewSet, PurchaseOrderViewSet

router = DefaultRouter()
router.register(r'requests', PurchaseRequestViewSet, basename='purchaserequest')
router.register(r'orders', PurchaseOrderViewSet, basename='purchaseorder')

urlpatterns = [
    path('', include(router.urls)),
]
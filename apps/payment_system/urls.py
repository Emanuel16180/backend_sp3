# apps/payment_system/urls.py

from django.urls import path
from .views import (
    CreateCheckoutSessionView, 
    StripeWebhookView, 
    PaymentStatusView,
    GetStripePublicKeyView,
    PaymentHistoryListView,
    ConfirmPaymentView,
    ListPlansForPurchaseView,
    PurchasePlanView,
    MyPurchasedPlansView
)

urlpatterns = [

    path('plans/list/', ListPlansForPurchaseView.as_view(), name='list-plans-for-purchase'),
    path('plans/purchase/', PurchasePlanView.as_view(), name='purchase-plan'),
    path('plans/my-plans/', MyPurchasedPlansView.as_view(), name='my-purchased-plans'),
    
    path('my-payments/', PaymentHistoryListView.as_view(), name='my-payment-history'),

    path('confirm-payment/', ConfirmPaymentView.as_view(), name='confirm-payment'),

    # Crear sesión de pago
    path('create-checkout-session/', CreateCheckoutSessionView.as_view(), name='create-checkout-session'),
    
    # Webhook de Stripe (debe ser público)
    path('stripe-webhook/', StripeWebhookView.as_view(), name='stripe-webhook'),
    
    # Verificar estado de pago
    path('payment-status/<int:appointment_id>/', PaymentStatusView.as_view(), name='payment-status'),
    
    # Obtener clave pública de Stripe
    path('stripe-public-key/', GetStripePublicKeyView.as_view(), name='stripe-public-key'),
]
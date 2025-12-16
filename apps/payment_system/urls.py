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
    MyPurchasedPlansView,
    # Mobile endpoints
    create_payment_intent_appointment,
    create_payment_intent_plan,
    confirm_payment_intent,
    PsychologistPaymentHistoryView,
    DownloadInvoiceView
)

urlpatterns = [

    path('plans/list/', ListPlansForPurchaseView.as_view(), name='list-plans-for-purchase'),
    path('plans/purchase/', PurchasePlanView.as_view(), name='purchase-plan'),
    path('plans/my-plans/', MyPurchasedPlansView.as_view(), name='my-purchased-plans'),
    
    # CU-27: Historial de Pagos (Paciente)
    path('my-payments/', PaymentHistoryListView.as_view(), name='my-payment-history'),
    # CU-27: Historial de Ingresos (Psicólogo) - NUEVO
    path('psychologist-earnings/', PsychologistPaymentHistoryView.as_view(), name='psychologist-payment-history'),

    # CU-26: Descargar Factura (Para ambos) - NUEVO
    path('transactions/<int:transaction_id>/invoice/', DownloadInvoiceView.as_view(), name='download-invoice'),

    path('confirm-payment/', ConfirmPaymentView.as_view(), name='confirm-payment'),

    # Crear sesión de pago
    path('create-checkout-session/', CreateCheckoutSessionView.as_view(), name='create-checkout-session'),
    
    # Webhook de Stripe (debe ser público)
    path('stripe-webhook/', StripeWebhookView.as_view(), name='stripe-webhook'),
    
    # Verificar estado de pago
    path('payment-status/<int:appointment_id>/', PaymentStatusView.as_view(), name='payment-status'),
    
    # Obtener clave pública de Stripe
    path('stripe-public-key/', GetStripePublicKeyView.as_view(), name='stripe-public-key'),
    
    # ============================================
    # ENDPOINTS PARA FLUTTER MOBILE
    # ============================================
    path('mobile/create-intent-appointment/', create_payment_intent_appointment, name='mobile-create-intent-appointment'),
    path('mobile/create-intent-plan/', create_payment_intent_plan, name='mobile-create-intent-plan'),
    path('mobile/confirm-payment/', confirm_payment_intent, name='mobile-confirm-payment'),
]
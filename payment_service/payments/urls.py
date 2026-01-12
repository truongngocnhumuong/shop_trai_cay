from django.urls import path
from .views import PaymentCreateView, PaymentDetailView, complete_payment, checkout_view

urlpatterns = [
    path('payments/', PaymentCreateView.as_view(), name='payment-create'),
    path('payments/<int:pk>/', PaymentDetailView.as_view(), name='payment-detail'),
    path('payments/<int:pk>/complete/', complete_payment, name='payment-complete'),
    path('checkout/<int:pk>/', checkout_view, name='checkout-ui'),
]

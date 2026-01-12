import uuid
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from .models import Payment
from .serializers import PaymentSerializer
from .utils import update_order_payment_status

class PaymentCreateView(generics.CreateAPIView):
    """
    POST /api/payments/ - Initialize a payment
    """
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payment = serializer.save()
        return Response(PaymentSerializer(payment).data, status=status.HTTP_201_CREATED)

class PaymentDetailView(generics.RetrieveAPIView):
    """
    GET /api/payments/{id}/ - Retrieve payment details
    """
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer

@api_view(['POST'])
@permission_classes([AllowAny])
def complete_payment(request, pk):
    """
    POST /api/payments/{id}/complete/ - Simulate payment completion
    """
    try:
        payment = Payment.objects.get(pk=pk)
        if payment.status == 'completed':
            return Response({'message': 'Payment already completed'}, status=status.HTTP_200_OK)
            
        # Simulate business logic
        payment.status = 'completed'
        payment.transaction_id = f"TRX-{uuid.uuid4().hex[:8].upper()}"
        payment.save()
        
        # Notify Order Service
        success = update_order_payment_status(payment.order_id, 'paid')
        
        if success:
            return Response({
                'message': 'Payment completed successfully',
                'transaction_id': payment.transaction_id,
                'order_status_updated': True
            })
        else:
            # We still completed the payment but failed to notify orders (SOA consistency issue)
            # In real world, we'd use a message queue or retry logic
            return Response({
                'message': 'Payment completed but failed to update order status',
                'transaction_id': payment.transaction_id,
                'order_status_updated': False
            }, status=status.HTTP_207_MULTI_STATUS)
            
    except Payment.DoesNotExist:
        return Response({'error': 'Payment not found'}, status=status.HTTP_404_NOT_FOUND)

from django.db.models import Sum
from django.shortcuts import render

# --- Web Interface Views ---

def dashboard_view(request):
    """
    Web Dashboard for transaction monitoring
    """
    payments = Payment.objects.all().order_by('-created_at')[:20]
    total_revenue = Payment.objects.filter(status='completed').aggregate(Sum('amount'))['amount__sum']
    total_count = Payment.objects.count()
    
    context = {
        'payments': payments,
        'total_revenue': total_revenue,
        'total_count': total_count,
        'active_page': 'dashboard'
    }
    return render(request, 'payments/dashboard.html', context)

def checkout_view(request, pk):
    """
    Premium Checkout UI hosted on Payment Service
    """
    try:
        payment = Payment.objects.get(pk=pk)
        
        if request.method == 'POST':
            # Reuse the complete_payment logic but for a web form
            if payment.status != 'completed':
                payment.status = 'completed'
                payment.transaction_id = f"TRX-{uuid.uuid4().hex[:8].upper()}"
                payment.save()
                update_order_payment_status(payment.order_id, 'paid')
                
            return render(request, 'payments/success.html', {'payment': payment})
            
        return render(request, 'payments/checkout.html', {'payment': payment})
    except Payment.DoesNotExist:
        return render(request, 'error.html', {'message': 'Payment Session Not Found'})

@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    return Response({'status': 'healthy', 'service': 'payment-service'}, status=status.HTTP_200_OK)

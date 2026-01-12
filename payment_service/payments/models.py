from django.db import models

class Payment(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Đang chờ'),
        ('completed', 'Hoàn tất'),
        ('failed', 'Thất bại'),
    )
    
    order_id = models.IntegerField(verbose_name='Order ID')
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Amount')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='Status')
    transaction_id = models.CharField(max_length=100, unique=True, null=True, blank=True, verbose_name='Transaction ID')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Created At')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Updated At')
    
    def __str__(self):
        return f"Payment for Order #{self.order_id} - {self.status}"

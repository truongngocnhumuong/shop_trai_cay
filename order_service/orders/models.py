from django.db import models

class Order(models.Model):
    """Order model for fruit shop"""
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )
    
    user_id = models.IntegerField(verbose_name='User ID')
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name='Total Price')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='Status')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Created At')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Updated At')
    
    class Meta:
        verbose_name = 'Order'
        verbose_name_plural = 'Orders'
        ordering = ['-created_at']
    
    def __str__(self):
        return f'Order #{self.id} - User {self.user_id}'
    
    def calculate_total(self):
        """Calculate total price from order items"""
        total = sum(item.subtotal for item in self.order_items.all())
        self.total_price = total
        self.save()
        return total

class OrderItem(models.Model):
    """OrderItem model for order details"""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='order_items', verbose_name='Order')
    product_id = models.IntegerField(verbose_name='Product ID')
    quantity = models.PositiveIntegerField(default=1, verbose_name='Quantity')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Price at time of order')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Created At')
    
    class Meta:
        verbose_name = 'Order Item'
        verbose_name_plural = 'Order Items'
        ordering = ['created_at']
    
    def __str__(self):
        return f'OrderItem {self.id} - Product {self.product_id} x {self.quantity}'
    
    @property
    def subtotal(self):
        """Calculate subtotal for this item"""
        return self.price * self.quantity


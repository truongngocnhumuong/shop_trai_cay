from django.db import models
from django.core.validators import MinValueValidator

class Inventory(models.Model):
    """Inventory model for product stock management"""
    product_id = models.IntegerField(unique=True, verbose_name='Product ID')
    quantity = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name='Quantity'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Created At')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Updated At')
    
    class Meta:
        verbose_name = 'Inventory'
        verbose_name_plural = 'Inventories'
        ordering = ['product_id']
    
    def __str__(self):
        return f'Product {self.product_id}: {self.quantity} units'
    
    def decrease(self, amount):
        """Decrease inventory quantity"""
        if self.quantity < amount:
            raise ValueError(f"Insufficient inventory. Available: {self.quantity}, Requested: {amount}")
        self.quantity -= amount
        self.save()
        return self.quantity
    
    def increase(self, amount):
        """Increase inventory quantity"""
        self.quantity += amount
        self.save()
        return self.quantity
    
    def set_quantity(self, quantity):
        """Set inventory quantity"""
        if quantity < 0:
            raise ValueError("Quantity cannot be negative")
        self.quantity = quantity
        self.save()
        return self.quantity


from django.db import models

class Product(models.Model):
    """Product model for fruit shop"""
    CATEGORY_CHOICES = (
        ('tropical', 'Tropical Fruits'),
        ('citrus', 'Citrus Fruits'),
        ('berries', 'Berries'),
        ('stone', 'Stone Fruits'),
        ('melons', 'Melons'),
        ('other', 'Other'),
    )
    
    name = models.CharField(max_length=200, verbose_name='Product Name')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Price')
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='other', verbose_name='Category')
    image = models.ImageField(upload_to='products/', blank=True, null=True, verbose_name='Product Image')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Created At')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Updated At')
    
    class Meta:
        verbose_name = 'Product'
        verbose_name_plural = 'Products'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name


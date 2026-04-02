from django.conf import settings
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


from django.db import models

from django.db import models

class Product(models.Model):
    id = models.IntegerField(primary_key=True)
    productDisplayName = models.TextField()
    masterCategory = models.CharField(max_length=100)
    subCategory = models.CharField(max_length=100)
    articleType = models.CharField(max_length=100)
    
    filename = models.CharField(max_length=255, blank=True, null=True)
    link = models.URLField(max_length=500, blank=True, null=True)
    gender = models.CharField(max_length=50)
    season = models.CharField(max_length=50, blank=True, null=True)
    year = models.IntegerField(blank=True, null=True)
    usage = models.CharField(max_length=100, blank=True, null=True)
    color = models.CharField(max_length=50, blank=True, null=True)
    price = models.FloatField()
    brand = models.CharField(max_length=100, blank=True, null=True)
    
    silhouette = models.CharField(max_length=100, blank=True, null=True, db_column='Silhouette')
    figure = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        db_table = 'api_product'

    def __str__(self):
        return f"{self.productDisplayName} ({self.price} $)"

class CartItem(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)
    

class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    phone_number = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Order #{self.id} - {self.total_amount} сом"


class Payment(models.Model):
    PAYMENT_METHOD_CHOICES = [
        ('mbank', 'Mbank'),
        ('visa', 'VISA Card'),
        ('mastercard', 'Mastercard'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='payment')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    phone_number = models.CharField(max_length=20, null=True, blank=True)
    transaction_id = models.CharField(max_length=100, null=True, blank=True, unique=True)
    mbank_invoice_id = models.CharField(max_length=100, null=True, blank=True)
    mbank_session_id = models.CharField(max_length=100, null=True, blank=True)
    card_last_four = models.CharField(max_length=4, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Payment #{self.id} - {self.amount} сом ({self.status})"
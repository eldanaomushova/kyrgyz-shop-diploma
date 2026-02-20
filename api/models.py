from django.conf import settings
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Product(models.Model):
    product_id = models.IntegerField(unique=True, db_column='product_id')
    productDisplayName = models.TextField(db_column='product_display_name')
    masterCategory = models.CharField(max_length=100, db_column='master_category')
    subCategory = models.CharField(max_length=100, db_column='sub_category')
    articleType = models.CharField(max_length=100, db_column='article_type')
    
    filename = models.CharField(max_length=255, db_column='filename')
    link = models.URLField(max_length=500, db_column='link')
    gender = models.CharField(max_length=50, db_column='gender')
    season = models.CharField(max_length=50, db_column='season')
    year = models.IntegerField(db_column='year')
    usage = models.CharField(max_length=100, db_column='usage')
    color = models.CharField(max_length=50, db_column='color')
    price = models.FloatField(db_column='price')
    brand = models.CharField(max_length=100, db_column='brand')
    
    silhouette = models.CharField(max_length=100, null=True, blank=True, db_column='silhouette')
    figure = models.CharField(max_length=100, null=True, blank=True, db_column='figure')

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
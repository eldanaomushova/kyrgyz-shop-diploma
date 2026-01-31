from django.conf import settings
from django.db import models

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
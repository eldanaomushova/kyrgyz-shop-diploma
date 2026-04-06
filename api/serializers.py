from rest_framework import serializers
from .models import Product

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'

class CartItemSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1)

class OrderSerializer(serializers.Serializer):
    products = serializers.ListField(
        child=serializers.DictField()
    )
    total_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    shipping_address = serializers.CharField()
    phone_number = serializers.CharField()
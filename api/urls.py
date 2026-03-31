from django.urls import path
from . import views 
from .views import (
    debug_product_fields,
    login_user, 
    register_user, 
    get_products, 
    get_product_detail,
    initiate_payment,
    payment_callback,
    payment_status,
    clothing_questionnaire,
    virtual_try_on
)

urlpatterns = [
    path('products/', views.get_products),
    path('products/detail/<int:pk>/', views.get_product_detail, name='product-detail'),
    path('categories-tree/', views.get_categories_tree, name='categories-tree'),
    path('full-categories-tree/', views.get_full_categories_tree, name='full-categories-tree'),
    path('cart/', views.cart_operations, name='cart-operations'),
    path('cart/<int:pk>/', views.cart_item_detail, name='cart_item_detail'),
    path('register/', views.register_user, name='register'),
    path('login/', views.login_user, name='login'), 
    
    path('payment/initiate/', initiate_payment, name='initiate-payment'),
    path('payment/callback/', payment_callback, name='payment-callback'),
    path('payment/<int:payment_id>/status/', payment_status, name='payment-status'),
    
    path('questionnaire/', clothing_questionnaire, name='clothing-questionnaire'),
    path('virtual-try-on/', virtual_try_on, name='virtual-try-on'),
    path('api/debug/product-fields/', debug_product_fields, name='debug_product_fields'),
]
from django.urls import path
from . import views

urlpatterns = [
    # Products
    path('products/', views.get_products, name='products'),
    path('products/detail/<pk>/', views.get_product_detail, name='product-detail'),
    path('categories-tree/', views.get_categories_tree, name='categories-tree'),
    path('full-categories-tree/', views.get_full_categories_tree, name='full-categories-tree'),
    
    # Filters and Stats
    path('filters/', views.get_available_filters, name='available-filters'),
    path('stats/', views.get_product_stats, name='product-stats'),
    
    # Cart
    path('cart/', views.cart_operations, name='cart-operations'),
    path('cart/<int:pk>/', views.cart_item_detail, name='cart_item_detail'),
    
    # Auth
    path('register/', views.register_user, name='register'),
    path('login/', views.login_user, name='login'),
    
    # Payment
    path('payment/initiate/', views.initiate_payment, name='initiate-payment'),
    path('payment/status/<int:payment_id>/', views.payment_status, name='payment-status'),
    
    # Recommendations
    path('questionnaire/', views.clothing_questionnaire, name='clothing-questionnaire'),
    
    # Virtual Try-on
    path('virtual-try-on/', views.virtual_try_on, name='virtual-try-on'),
    
    # Debug
    path('debug/product-fields/', views.debug_product_fields, name='debug_product_fields'),
]
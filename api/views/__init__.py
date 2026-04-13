# api/views/__init__.py
"""
Views package for the API
"""


from .virtual_try_on import image_try_on, pose_estimation_view

# Product Views
from .product_views import (
    get_products,
    get_product_detail,
    get_categories_tree,
    get_full_categories_tree,
    get_available_filters,
    get_product_stats,
)

from .ar_try_on_views import extract_garment_view

# Cart Views
from .cart_views import cart_operations, cart_item_detail

# Auth Views
from .auth_views import register_user, login_user

# Payment Views
from .payment_views import initiate_payment, payment_status

# Recommendation Views
from .recommendation_views import clothing_questionnaire

# Export all views
__all__ = [
    # Virtual try-on (image to image)
    'image_try_on',
    'pose_estimation_view',
    'extract_garment_view',
    
    # Products
    'get_products',
    'get_product_detail',
    'get_categories_tree',
    'get_full_categories_tree',
    'get_available_filters',
    'get_product_stats',
    
    # Cart
    'cart_operations',
    'cart_item_detail',
    
    # Auth
    'register_user',
    'login_user',
    
    # Payment
    'initiate_payment',
    'payment_status',
    
    # Recommendations
    'clothing_questionnaire',
]
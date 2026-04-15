from .virtual_try_on import image_try_on, pose_estimation_view

from .product_views import (
    get_products,
    get_product_detail,
    get_categories_tree,
    get_full_categories_tree,
    get_available_filters,
    get_product_stats,
)
from .ar_try_on_views import extract_garment_view 

from .cart_views import cart_operations, cart_item_detail

from .auth_views import register_user, login_user

from .payment_views import initiate_payment, payment_status

from .recommendation_views import clothing_questionnaire

# Export all views
__all__ = [
    'image_try_on',
    'pose_estimation_view',
    'extract_garment_view',
    
    'get_products',
    'get_product_detail',
    'get_categories_tree',
    'get_full_categories_tree',
    'get_available_filters',
    'get_product_stats',
    
    'cart_operations',
    'cart_item_detail',
    
    'register_user',
    'login_user',
    
    'initiate_payment',
    'payment_status',
    
    'clothing_questionnaire',
]
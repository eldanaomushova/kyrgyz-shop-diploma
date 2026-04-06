# api/urls.py
from django.urls import path
from api.views import (  
    get_products,
    get_product_detail,
    get_categories_tree,
    get_full_categories_tree,
    get_available_filters,
    get_product_stats,
    cart_operations,
    cart_item_detail,
    register_user,
    login_user,
    initiate_payment,
    payment_status,
    clothing_questionnaire,
    image_try_on,
    pose_estimation_view,
)
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Products
    path('products/', get_products, name='products'),
    path('products/detail/<pk>/', get_product_detail, name='product-detail'),
    path('categories-tree/', get_categories_tree, name='categories-tree'),
    path('full-categories-tree/', get_full_categories_tree, name='full-categories-tree'),
    
    # Filters and Stats
    path('filters/', get_available_filters, name='available-filters'),
    path('stats/', get_product_stats, name='product-stats'),
    
    # Cart
    path('cart/', cart_operations, name='cart-operations'),
    path('cart/<int:pk>/', cart_item_detail, name='cart_item_detail'),
    
    # Auth
    path('register/', register_user, name='register'),
    path('login/', login_user, name='login'),
    
    # Payment
    path('payment/initiate/', initiate_payment, name='initiate-payment'),
    path('payment/status/<int:payment_id>/', payment_status, name='payment-status'),
    
    # Recommendations
    path('questionnaire/', clothing_questionnaire, name='clothing-questionnaire'),
    
    path('virtual-try-on/image-try-on/', image_try_on, name='image-try-on'),
    path('virtual-try-on/pose-estimation/', pose_estimation_view, name='pose-estimation'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
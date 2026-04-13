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
)
from django.conf import settings
from django.conf.urls.static import static

from api.views.ar_try_on_views import extract_garment_view
from api.views.virtual_try_on import image_try_on, pose_estimation_view
from api.views.ar_try_on_views import extract_garment_view

urlpatterns = [
    path('products/', get_products, name='products'),
    path('products/detail/<pk>/', get_product_detail, name='product-detail'),
    path('categories-tree/', get_categories_tree, name='categories-tree'),
    path('full-categories-tree/', get_full_categories_tree, name='full-categories-tree'),
    
    path('filters/', get_available_filters, name='available-filters'),
    path('stats/', get_product_stats, name='product-stats'),
    
    path('cart/', cart_operations, name='cart-operations'),
    path('cart/<int:pk>/', cart_item_detail, name='cart_item_detail'),
    
    path('register/', register_user, name='register'),
    path('login/', login_user, name='login'),
    
    path('payment/initiate/', initiate_payment, name='initiate-payment'),
    path('payment/status/<int:payment_id>/', payment_status, name='payment-status'),
    
    path('questionnaire/', clothing_questionnaire, name='clothing-questionnaire'),
    
    path('virtual-try-on/extract-garment/', extract_garment_view, name='extract_garment'),
    path('virtual-try-on/image-try-on/', image_try_on, name='image-try-on'),
    path('virtual-try-on/pose-estimation/', pose_estimation_view, name='pose-estimation'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
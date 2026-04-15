from django.urls import path
from api import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('products/',views.get_products, name='products'),
    path('products/detail/<pk>/', views.get_product_detail, name='product-detail'),
    path('categories-tree/', views.get_categories_tree, name='categories-tree'),
    path('full-categories-tree/', views.get_full_categories_tree, name='full-categories-tree'),
    
    path('filters/', views.get_available_filters, name='available-filters'),
    path('stats/', views.get_product_stats, name='product-stats'),
    
    path('cart/', views.cart_operations, name='cart-operations'),
    path('cart/<int:pk>/', views.cart_item_detail, name='cart_item_detail'),
    
    path('register/', views.register_user, name='register'),
    path('login/', views.login_user, name='login'),
    
    path('payment/initiate/', views.initiate_payment, name='initiate-payment'),
    path('payment/status/<int:payment_id>/', views.payment_status, name='payment-status'),
    
    path('questionnaire/', views.clothing_questionnaire, name='clothing-questionnaire'),
    
    path('virtual-try-on/extract-garment/', views.extract_garment_view, name='extract_garment'),
    path('virtual-try-on/image-try-on/', views.image_try_on, name='image-try-on'),
    path('virtual-try-on/pose-estimation/', views.pose_estimation_view, name='pose-estimation'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
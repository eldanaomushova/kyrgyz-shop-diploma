from django.urls import path
from . import views 
from rest_framework_simplejwt.views import TokenRefreshView
from .views import login_user, register_user, get_products, get_product_detail

urlpatterns = [
    path('products/', views.get_products),
    path('products/detail/<int:pk>/', views.get_product_detail, name='product-detail'),
    path('categories-tree/', views.get_categories_tree, name='categories-tree'),
    path('full-categories-tree/', views.get_full_categories_tree, name='full-categories-tree'),
    path('cart/', views.cart_operations, name='cart-operations'),
    path('cart/<int:pk>/', views.cart_item_detail, name='cart_item_detail'),
    path('register/', views.register_user, name='register'),
    path('login/', views.login_user, name='login'), 
    path('token/', login_user, name='login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
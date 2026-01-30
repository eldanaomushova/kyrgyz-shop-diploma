from django.urls import path
from . import views 

urlpatterns = [
    path('products/', views.get_products),
    path('products/detail/<int:pk>/', views.get_product_detail, name='product-detail'),
    path('categories-tree/', views.get_categories_tree, name='categories-tree'),
    path('full-categories-tree/', views.get_full_categories_tree, name='full-categories-tree'),
]
from django.urls import path
from . import views 

urlpatterns = [
    path('products/', views.get_products),
    path('products/<str:gender>/', views.get_products),
    path('products/<str:gender>/<str:category>/', views.get_products),
    path('categories-tree/', views.get_categories_tree, name='categories-tree'),
    path('products/<str:gender>/<str:category>/', views.get_products),
    path('full-categories-tree/', views.get_full_categories_tree, name='full-categories-tree'),
]
from django.shortcuts import get_object_or_404
from rest_framework.pagination import PageNumberPagination
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Product
from .serializers import ProductSerializer

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 12
    page_size_query_param = 'page_size'
    max_page_size = 100

from rest_framework.response import Response 

@api_view(['GET'])
def get_products(request):
    queryset = Product.objects.all().order_by('id')
    
    search_query = request.query_params.get('search', None)
    gender_param = request.query_params.get('gender', None)
    sub_category_param = request.query_params.get('sub', None)
    article_type_param = request.query_params.get('type', None) 

    if search_query:
        queryset = queryset.filter(productDisplayName__icontains=search_query)
    
    if gender_param:
        queryset = queryset.filter(gender__iexact=gender_param)
        
    if sub_category_param:
        queryset = queryset.filter(subCategory__iexact=sub_category_param)
        
    if article_type_param:
        queryset = queryset.filter(articleType__iexact=article_type_param)

    paginator = StandardResultsSetPagination()
    page = paginator.paginate_queryset(queryset, request)
    
    if page is not None:
        serializer = ProductSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    serializer = ProductSerializer(queryset, many=True)
    return Response(serializer.data)


@api_view(['GET'])
def get_categories_tree(request):
    raw_data = Product.objects.values_list('gender', 'masterCategory', 'subCategory').distinct()

    tree = {}

    for gender, master, sub in raw_data:
        if not gender or not master or not sub:
            continue
            
        if gender not in tree:
            tree[gender] = {}
        
        if master not in tree[gender]:
            tree[gender][master] = []
            
        if sub not in tree[gender][master]:
            tree[gender][master].append(sub)

    return Response(tree)

@api_view(['GET'])
def get_full_categories_tree(request):
    raw_data = Product.objects.values_list(
        'gender', 
        'subCategory', 
        'articleType'
    ).distinct()

    tree = {}

    for gender, sub, art_type in raw_data:
        if not all([gender, sub, art_type]):
            continue
            
        if gender not in tree:
            tree[gender] = {}
        
        if sub not in tree[gender]:
            tree[gender][sub] = []
            
        if art_type not in tree[gender][sub]:
            tree[gender][sub].append(art_type)

    return Response(tree)


@api_view(['GET'])
def get_product_detail(request, pk):
    product = get_object_or_404(Product, product_id=pk) 

    serializer = ProductSerializer(product)
    return Response(serializer.data)
import logging
from django.shortcuts import get_object_or_404
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status
from ..serializers import ProductSerializer 
from ..models import Product

logger = logging.getLogger(__name__)

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 12
    page_size_query_param = 'page_size'
    max_page_size = 100

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
    raw_data = Product.objects.values_list('gender', 'subCategory', 'articleType').distinct()
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
    """
    Get product details by ID with improved error handling
    """
    try:
        # Проверяем, что pk не None, не 'undefined', не 'null' и не пустой
        if pk is None or pk == 'undefined' or pk == 'null' or pk == '':
            return Response(
                {
                    'error': 'Invalid product ID',
                    'message': 'Product ID is required and must be a valid number'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Пробуем преобразовать в integer
        try:
            id = int(pk)
        except (ValueError, TypeError):
            return Response(
                {
                    'error': 'Invalid product ID format',
                    'message': f'Product ID must be a number, got: {pk}'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Ищем продукт
        product = get_object_or_404(Product, id=id)
        serializer = ProductSerializer(product)
        return Response(serializer.data)
        
    except Exception as e:
        logger.error(f"Error fetching product detail for pk={pk}: {str(e)}")
        return Response(
            {
                'error': 'Product not found',
                'message': str(e)
            },
            status=status.HTTP_404_NOT_FOUND
        )

@api_view(['GET'])
def get_available_filters(request):
    """
    Get all available filter options for the frontend
    """
    try:
        filters = {
            'genders': list(Product.objects.exclude(gender__isnull=True)
                           .exclude(gender='')
                           .values_list('gender', flat=True)
                           .distinct()),
            'master_categories': list(Product.objects.exclude(masterCategory__isnull=True)
                                     .exclude(masterCategory='')
                                     .values_list('masterCategory', flat=True)
                                     .distinct()),
            'sub_categories': list(Product.objects.exclude(subCategory__isnull=True)
                                  .exclude(subCategory='')
                                  .values_list('subCategory', flat=True)
                                  .distinct()),
            'article_types': list(Product.objects.exclude(articleType__isnull=True)
                                 .exclude(articleType='')
                                 .values_list('articleType', flat=True)
                                 .distinct()),
            'colors': list(Product.objects.exclude(color__isnull=True)
                          .exclude(color='')
                          .values_list('color', flat=True)
                          .distinct()),
            'seasons': list(Product.objects.exclude(season__isnull=True)
                           .exclude(season='')
                           .values_list('season', flat=True)
                           .distinct()),
            'usages': list(Product.objects.exclude(usage__isnull=True)
                          .exclude(usage='')
                          .values_list('usage', flat=True)
                          .distinct()),
            'price_ranges': [
                {'label': 'Low (0-2000)', 'min': 0, 'max': 2000},
                {'label': 'Medium (2000-5000)', 'min': 2000, 'max': 5000},
                {'label': 'High (5000+)', 'min': 5000, 'max': None}
            ]
        }
        
        # Сортируем списки для удобства
        for key in ['genders', 'master_categories', 'sub_categories', 
                    'article_types', 'colors', 'seasons', 'usages']:
            filters[key] = sorted(filters[key])
        
        return Response(filters)
        
    except Exception as e:
        logger.error(f"Error getting filters: {str(e)}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
def get_product_stats(request):
    """
    Get statistics about products in the database
    """
    try:
        total_products = Product.objects.count()
        products_with_color = Product.objects.exclude(color__isnull=True).exclude(color='').count()
        products_with_price = Product.objects.exclude(price__isnull=True).exclude(price=0).count()
        
        # Get price range
        price_stats = Product.objects.aggregate(
            min_price=models.Min('price'),
            max_price=models.Max('price'),
            avg_price=models.Avg('price')
        )
        
        return Response({
            'total_products': total_products,
            'products_with_color': products_with_color,
            'products_with_price': products_with_price,
            'color_coverage': round(products_with_color / total_products * 100, 2) if total_products > 0 else 0,
            'price_stats': {
                'min': price_stats['min_price'] or 0,
                'max': price_stats['max_price'] or 0,
                'avg': round(price_stats['avg_price'], 2) if price_stats['avg_price'] else 0
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting stats: {str(e)}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db.models import Q
from decimal import Decimal

from api.models import Product

@api_view(['GET'])
def search_products(request):
    query = request.query_params.get('search', '')
    
    if len(query) < 2:
        return Response([])
    
    try:
        products = Product.objects.filter(
            Q(productDisplayName__icontains=query) |
            Q(brand__icontains=query) |
            Q(articleType__icontains=query) |
            Q(subCategory__icontains=query)
        )[:20] 
        
        data = [{
            'id': p.id,
            'productDisplayName': p.productDisplayName,
            'brand': p.brand,
            'price': float(p.price) if p.price else None, 
            'gender': p.gender,
            'subCategory': p.subCategory,
            'articleType': p.articleType,
            'link': p.link,
        } for p in products]
        
        return Response(data)
        
    except Exception as e:
        return Response({'error': str(e)}, status=500)
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from ..models import Product  # Make sure your model is named Product

@api_view(['GET'])
@permission_classes([AllowAny])
@authentication_classes([])
def debug_product_fields(request):
    """Debug endpoint to check available fields and sample data"""
    try:
        # Get one sample product
        sample = Product.objects.first()
        
        if sample:
            # Get all field names and their values
            fields = {}
            for field in sample._meta.get_fields():
                field_name = field.name
                try:
                    value = getattr(sample, field_name)
                    fields[field_name] = str(value)[:100]  # Truncate long values
                except:
                    fields[field_name] = "Unable to retrieve"
            
            # Get unique values for key fields
            unique_values = {}
            for field_name in ['gender', 'usage', 'masterCategory', 'subCategory', 'articleType', 'season']:
                if hasattr(Product, field_name):
                    values = Product.objects.values_list(field_name, flat=True).distinct()[:20]
                    unique_values[field_name] = list(values)
            
            return Response({
                'sample_product_fields': fields,
                'unique_values': unique_values,
                'total_products': Product.objects.count()
            })
        else:
            return Response({'error': 'No products found in database'})
    
    except Exception as e:
        return Response({'error': str(e)})

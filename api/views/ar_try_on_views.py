import json
import logging
from datetime import datetime
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from ..models import Product

logger = logging.getLogger(__name__)

def ar_try_on_view(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    return render(request, 'ar_try_on.html', {
        'product': product,
        'product_id': product.id,
        'product_name': product.productDisplayName,
        'product_price': product.price,
        'product_image_url': product.link,
    })

@csrf_exempt
@require_http_methods(["POST"])
def ar_session_api(request):
    try:
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = request.POST.dict()
        
        product_id = data.get('product_id')
        
        if not product_id:
            return JsonResponse({'error': 'product_id is required'}, status=400)
        
        product = get_object_or_404(Product, id=product_id)
        
        return JsonResponse({
            'success': True,
            'ar_url': f'/api/ar/try-on/{product_id}/',
            'session_id': f'session_{product_id}_{int(datetime.now().timestamp())}',
            'product': {
                'id': product.id,
                'name': product.productDisplayName,
                'price': float(product.price) if product.price else 0,
                'image': product.link,
            }
        })
    except Exception as e:
        logger.error(f"AR session error: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def ar_webhook(request):
    try:
        data = json.loads(request.body)
        logger.info(f"AR Webhook received: {data}")
        return JsonResponse({'status': 'success'})
    except Exception as e:
        logger.error(f"Webhook error: {str(e)}")
        return JsonResponse({'error': str(e)}, status=400)

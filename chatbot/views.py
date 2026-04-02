from django.http import JsonResponse
from .services import get_shopping_response
import json
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import redirect, get_object_or_404
from api.models import Product, CartItem


@csrf_exempt
def chat_endpoint(request):  
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            user_message = data.get("message", "")
            bot_html_output = get_shopping_response(user_message)
            return JsonResponse({"response": bot_html_output})
            
        except Exception as e:
            return JsonResponse({"response": "Error processing request"}, status=500)
    return JsonResponse({"error": "Invalid method"}, status=405)

@csrf_exempt
def add_to_cart(request, id):
    product = get_object_or_404(Product, id=id)
    cart_item, created = CartItem.objects.get_or_create(product=product)
    if not created:
        cart_item.quantity += 1
        cart_item.save()
    return redirect('/cart/')
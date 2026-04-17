from rest_framework.response import Response  
from ..models import Product, CartItem
from rest_framework import status
from dotenv import load_dotenv 
from rest_framework.decorators import api_view, permission_classes, authentication_classes
load_dotenv()


@api_view(['GET', 'POST'])
def cart_operations(request):
    if request.method == 'GET':
        items = CartItem.objects.all()
        data = [
            {
                "id": item.product.id,
                "productDisplayName": item.product.productDisplayName,
                "price": item.product.price,
                "link": item.product.link,
                "quantity": item.quantity
            } for item in items
        ]
        return Response(data)

    if request.method == 'POST':
        try:
            product_id = request.data.get('id') or request.data.get('product_id')
            if not product_id:
                return Response({"error": "Product ID is required"}, status=400)
                
            product = Product.objects.get(id=product_id)
            
            cart_item, created = CartItem.objects.get_or_create(product=product)
            if not created:
                cart_item.quantity += 1
                cart_item.save()
                
            return Response({
                "message": "Added to cart",
                "item": {
                    "id": cart_item.product.id,
                    "quantity": cart_item.quantity,
                    "productDisplayName": cart_item.product.productDisplayName,
                    "price": cart_item.product.price
                }
            }, status=status.HTTP_201_CREATED)
            
        except Product.DoesNotExist:
            return Response({"error": "Product not found"}, status=404)
        except Exception as e:
            print(f"CRASH LOG: {e}")
            return Response({"error": str(e)}, status=500)





@api_view(['DELETE', 'PATCH'])
def cart_item_detail(request, pk):
    print(f"DEBUG: Received request for id: {pk}") 
    
    try:
        item = CartItem.objects.get(product__id=pk)
    except CartItem.DoesNotExist:
        print(f"DEBUG: CartItem with id {pk} not found in database.")
        return Response({"error": "Item not found"}, status=404)

    if request.method == 'DELETE':
        item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    if request.method == 'PATCH':
        new_quantity = request.data.get('quantity')
        if new_quantity is not None:
            item.quantity = int(new_quantity) 
            item.save()
            return Response({"message": "Updated", "quantity": item.quantity})
        
        return Response({"error": "No quantity provided"}, status=400)
    
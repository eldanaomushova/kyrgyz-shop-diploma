from django.shortcuts import get_object_or_404
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from .serializers import ProductSerializer
from .models import Product, CartItem, Order, Payment
from django.contrib.auth.models import User
from rest_framework.decorators import api_view, permission_classes
from drf_spectacular.utils import extend_schema
from rest_framework import serializers, status
from django.contrib.auth import authenticate
import json
import uuid
from django.conf import settings
import traceback
import time


class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()
    email = serializers.EmailField()
    firstName = serializers.CharField(required=False)
    lastName = serializers.CharField(required=False)

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 12
    page_size_query_param = 'page_size'
    max_page_size = 100
    
    
class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()
    
    
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



@api_view(['GET', 'POST']) 
def cart_operations(request):
    if request.method == 'GET':
        items = CartItem.objects.all()
        data = [
            {
                "product_id": item.product.product_id,
                "productDisplayName": item.product.productDisplayName,
                "price": item.product.price,
                "link": item.product.link,
                "quantity": item.quantity
            } for item in items
        ]
        return Response(data)

    if request.method == 'POST':
        try:
            p_id = request.data.get('product_id')
            product = Product.objects.get(product_id=p_id)
            
            cart_item, created = CartItem.objects.get_or_create(product=product)
            if not created:
                cart_item.quantity += 1
                cart_item.save()
                
            return Response({"message": "Added"}, status=status.HTTP_201_CREATED)
        except Product.DoesNotExist:
            return Response({"error": "Product not found"}, status=404)
        except Exception as e:
            print(f"CRASH LOG: {e}") 
            return Response({"error": str(e)}, status=500)
        
@api_view(['DELETE', 'PATCH'])
def cart_item_detail(request, pk):
    print(f"DEBUG: Received request for product_id: {pk}") 
    
    try:
        item = CartItem.objects.get(product__product_id=pk)
    except CartItem.DoesNotExist:
        print(f"DEBUG: CartItem with product_id {pk} not found in database.")
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
    
    
@extend_schema(
    request=RegisterSerializer,
    responses={201: {"message": "User created successfully"}},
    description="Registers a new user into the system.",
    tags=['Authentication']
)
    
@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request):
    username = request.data.get('username')
    password = request.data.get('password')
    email = request.data.get('email')
    
    first_name = request.data.get('firstName', '') 
    last_name = request.data.get('lastName', '')

    if not username or not password:
        return Response({"error": "Username and password required"}, status=status.HTTP_400_BAD_REQUEST)

    if User.objects.filter(username=username).exists():
        return Response({"error": "User already exists"}, status=status.HTTP_400_BAD_REQUEST)

    user = User.objects.create_user(
        username=username, 
        password=password, 
        email=email,
        first_name=first_name,
        last_name=last_name
    )
    
    return Response({"message": "User created successfully"}, status=status.HTTP_201_CREATED)



@extend_schema(
    request=LoginSerializer,
    responses={200: dict},
    description="Login to get Access and Refresh tokens",
    tags=['Authentication']
)
@api_view(['POST'])
@permission_classes([AllowAny])
def login_user(request):
    username = request.data.get('username')
    password = request.data.get('password')

    user = authenticate(username=username, password=password)

    if user is not None:
        return Response({
            'message': 'Login successful',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email
            }
        }, status=status.HTTP_200_OK)
    
    return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)






def clean_phone_number(phone):
    """
    Clean and format phone number to +996XXXXXXXXX format
    Accepts: +996701234567, 0701234567, 701234567
    """
    phone = str(phone)
    import re
    cleaned = re.sub(r'[^\d+]', '', phone)
    
    if cleaned.startswith('+996'):
        return cleaned
    
    if cleaned.startswith('0'):
        return '+996' + cleaned[1:]
    
    if len(cleaned) == 9:
        return '+996' + cleaned
    
    return '+996' + cleaned[-9:] if len(cleaned) >= 9 else phone


@api_view(['POST'])
@permission_classes([AllowAny])
def initiate_payment(request):
    """
    Initiate payment through Mbank
    User receives push notification on phone and confirms with PIN
    
    Expected POST data:
    {
        "amount": 5000,
        "phone_number": "+996701234567",
        "payment_method": "mbank"
    }
    """
    try:
        data = request.data
        amount = data.get('amount')
        phone_number = data.get('phone_number')
        payment_method = data.get('payment_method', 'mbank')
        order_id = data.get('order_id')
        
        if not phone_number:
            return Response(
                {'error': 'Телефон номери талап кылынат'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        phone_number = clean_phone_number(phone_number)
        
        try:
            amount = float(amount)
            if amount <= 0:
                return Response(
                    {'error': 'Төлөнүүчү сумма 0дөн чоң болушу керек'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except ValueError:
            return Response(
                {'error': 'Төлөнүүчү сумма саны болушу керек'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if order_id:
            try:
                order_id = int(order_id)
                order = Order.objects.get(id=order_id)
                if order.total_amount != amount:
                    return Response(
                        {'error': 'Төлөнүүчү сумма заказдын суммасына дал келбейт'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                if Payment.objects.filter(order=order).exists():
                    return Response(
                        {'error': 'Бул заказ үчүн төлөм мурунтан эле башталган'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            except (Order.DoesNotExist, ValueError):
                return Response(
                    {'error': 'Заказ табылган жок'},
                    status=status.HTTP_404_NOT_FOUND
                )
        else:
            order = Order.objects.create(
                total_amount=amount,
                phone_number=phone_number,
                status='pending'
            )
        
        payment = Payment.objects.create(
            order=order,
            payment_method=payment_method,
            amount=amount,
            phone_number=phone_number,
            status='pending'
        )
        
        if payment_method == 'mbank':
            mbank_response = initiate_mbank_payment(
                order=order,
                payment=payment,
                amount=amount,
                phone_number=phone_number
            )
            
            if mbank_response.get('success'):
                payment.mbank_invoice_id = mbank_response.get('invoice_id')
                payment.mbank_session_id = mbank_response.get('session_id')
                payment.save()
                
                return Response({
                    'success': True,
                    'payment_id': payment.id,
                    'order_id': order.id,
                    'status': 'pending_confirmation',
                    'message': mbank_response.get('message', 'Та эскерте турган телефонуңузга төлөм сурамасы жиберилди.'),
                    'amount': amount,
                    'phone_number': phone_number,
                    'payment_url': mbank_response.get('payment_url'),
                }, status=status.HTTP_201_CREATED)
            else:
                payment.status = 'failed'
                payment.save()
                
                return Response({
                    'success': False,
                    'error': mbank_response.get('message', 'Төлөм жүргүзүүдө ката болду')
                }, status=status.HTTP_400_BAD_REQUEST)
        elif payment_method == 'visa':
            card_number = data.get('card_number')
            expiry_month = data.get('expiry_month')
            expiry_year = data.get('expiry_year')
            cvv = data.get('cvv')
            
            if not all([card_number, expiry_month, expiry_year, cvv]):
                return Response(
                    {'error': 'Visa төлөм үчүн карта маалыматтары талап кылынат'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if len(card_number.replace(' ', '')) < 13 or not card_number.replace(' ', '').isdigit():
                return Response(
                    {'error': 'Жараксыз карта номери'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            time.sleep(2) 
            
            payment.status = 'success'
            payment.card_last_four = card_number[-4:]
            payment.transaction_id = f"DEMO_{payment.id}_{int(time.time())}"
            payment.save()
            order.status = 'completed'
            order.save()
            
            return Response({
                'success': True,
                'payment_id': payment.id,
                'order_id': order.id,
                'status': 'success',
                'message': 'Visa төлөм ийгиликтүү жүргүзүлдү (демо режим).',
                'amount': amount,
                'phone_number': phone_number,
                'transaction_id': payment.transaction_id,
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'success': True,
            'payment_id': payment.id,
            'order_id': order.id,
            'status': 'pending'
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        error_msg = traceback.format_exc()
        return Response(
            {'error': error_msg},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
        
        
@api_view(['POST'])
@permission_classes([AllowAny])
def payment_callback(request):
    """
    Handle Mbank callback/webhook
    """
    try:
        data = request.data
        invoice_id = data.get('invoice_id')
        session_id = data.get('session_id')
        status_code = data.get('status')
        amount = data.get('amount')
        
        payment = Payment.objects.get(mbank_invoice_id=invoice_id)
        
        checksum_string = f"{invoice_id}{status_code}{MBANK_MERCHANT_SECRET}"
        import hashlib
        expected_checksum = hashlib.sha256(checksum_string.encode()).hexdigest()
        
        if data.get('checksum') != expected_checksum:
            return Response(
                {'error': 'Invalid checksum'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if status_code == 'success':
            payment.status = 'success'
            payment.transaction_id = data.get('transaction_id')
            payment.order.status = 'completed'
            payment.order.save()
        elif status_code == 'failed':
            payment.status = 'failed'
        elif status_code == 'cancelled':
            payment.status = 'cancelled'
        
        payment.save()
        
        return Response({
            'success': True,
            'payment_id': payment.id,
            'status': payment.status
        }, status=status.HTTP_200_OK)
        
    except Payment.DoesNotExist:
        return Response(
            {'error': 'Payment not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def payment_status(request, payment_id):
    """
    Get payment status
    """
    try:
        payment = Payment.objects.get(id=payment_id)
        
        return Response({
            'id': payment.id,
            'status': payment.status,
            'amount': str(payment.amount),
            'payment_method': payment.payment_method,
            'created_at': payment.created_at,
            'order_id': payment.order.id
        })
        
    except Payment.DoesNotExist:
        return Response(
            {'error': 'Payment not found'},
            status=status.HTTP_404_NOT_FOUND
        )
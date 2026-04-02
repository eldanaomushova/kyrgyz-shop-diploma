# import logging
# from venv import logger

# from django.shortcuts import get_object_or_404
# from rest_framework.pagination import PageNumberPagination
# from rest_framework.permissions import AllowAny, IsAuthenticated
# from rest_framework.response import Response
# from .serializers import ProductSerializer
# from .models import Product, CartItem, Order, Payment
# from django.contrib.auth.models import User
# from django.db.models import Q
# from drf_spectacular.utils import extend_schema
# from rest_framework import serializers, status
# from django.contrib.auth import authenticate
# from django.conf import settings
# import traceback
# import time
# import google.genai as genai
# import os
# from .models import Product
# from dotenv import load_dotenv 
# from rest_framework.decorators import api_view, permission_classes, authentication_classes
# from .models import Product
# from .serializers import ProductSerializer
# from django.db import models  
# load_dotenv()



# class RegisterSerializer(serializers.Serializer):
#     username = serializers.CharField()
#     password = serializers.CharField()
#     email = serializers.EmailField()
#     firstName = serializers.CharField(required=False)
#     lastName = serializers.CharField(required=False)

# class StandardResultsSetPagination(PageNumberPagination):
#     page_size = 12
#     page_size_query_param = 'page_size'
#     max_page_size = 100
    
    
# class LoginSerializer(serializers.Serializer):
#     username = serializers.CharField()
#     password = serializers.CharField()
    
    
# @api_view(['GET'])
# def get_products(request):
#     queryset = Product.objects.all().order_by('id')
    
#     search_query = request.query_params.get('search', None)
#     gender_param = request.query_params.get('gender', None)
#     sub_category_param = request.query_params.get('sub', None)
#     article_type_param = request.query_params.get('type', None) 

#     if search_query:
#         queryset = queryset.filter(productDisplayName__icontains=search_query)
    
#     if gender_param:
#         queryset = queryset.filter(gender__iexact=gender_param)
        
#     if sub_category_param:
#         queryset = queryset.filter(subCategory__iexact=sub_category_param)
        
#     if article_type_param:
#         queryset = queryset.filter(articleType__iexact=article_type_param)

#     paginator = StandardResultsSetPagination()
#     page = paginator.paginate_queryset(queryset, request)
    
#     if page is not None:
#         serializer = ProductSerializer(page, many=True)
#         return paginator.get_paginated_response(serializer.data)

#     serializer = ProductSerializer(queryset, many=True)
#     return Response(serializer.data)


# @api_view(['GET'])
# def get_categories_tree(request):
#     raw_data = Product.objects.values_list('gender', 'masterCategory', 'subCategory').distinct()

#     tree = {}

#     for gender, master, sub in raw_data:
#         if not gender or not master or not sub:
#             continue
            
#         if gender not in tree:
#             tree[gender] = {}
        
#         if master not in tree[gender]:
#             tree[gender][master] = []
            
#         if sub not in tree[gender][master]:
#             tree[gender][master].append(sub)

#     return Response(tree)

# @api_view(['GET'])
# def get_full_categories_tree(request):
#     raw_data = Product.objects.values_list(
#         'gender', 
#         'subCategory', 
#         'articleType'
#     ).distinct()

#     tree = {}

#     for gender, sub, art_type in raw_data:
#         if not all([gender, sub, art_type]):
#             continue
            
#         if gender not in tree:
#             tree[gender] = {}
        
#         if sub not in tree[gender]:
#             tree[gender][sub] = []
            
#         if art_type not in tree[gender][sub]:
#             tree[gender][sub].append(art_type)

#     return Response(tree)


# @api_view(['GET'])
# def get_product_detail(request, pk):
#     product = get_object_or_404(Product, product_id=pk) 

#     serializer = ProductSerializer(product)
#     return Response(serializer.data)



# @api_view(['GET', 'POST']) 
# def cart_operations(request):
#     if request.method == 'GET':
#         items = CartItem.objects.all()
#         data = [
#             {
#                 "product_id": item.product.product_id,
#                 "productDisplayName": item.product.productDisplayName,
#                 "price": item.product.price,
#                 "link": item.product.link,
#                 "quantity": item.quantity
#             } for item in items
#         ]
#         return Response(data)

#     if request.method == 'POST':
#         try:
#             p_id = request.data.get('product_id')
#             product = Product.objects.get(product_id=p_id)
            
#             cart_item, created = CartItem.objects.get_or_create(product=product)
#             if not created:
#                 cart_item.quantity += 1
#                 cart_item.save()
                
#             return Response({"message": "Added"}, status=status.HTTP_201_CREATED)
#         except Product.DoesNotExist:
#             return Response({"error": "Product not found"}, status=404)
#         except Exception as e:
#             print(f"CRASH LOG: {e}") 
#             return Response({"error": str(e)}, status=500)
        
# @api_view(['DELETE', 'PATCH'])
# def cart_item_detail(request, pk):
#     print(f"DEBUG: Received request for product_id: {pk}") 
    
#     try:
#         item = CartItem.objects.get(product__product_id=pk)
#     except CartItem.DoesNotExist:
#         print(f"DEBUG: CartItem with product_id {pk} not found in database.")
#         return Response({"error": "Item not found"}, status=404)

#     if request.method == 'DELETE':
#         item.delete()
#         return Response(status=status.HTTP_204_NO_CONTENT)
    
#     if request.method == 'PATCH':
#         new_quantity = request.data.get('quantity')
#         if new_quantity is not None:
#             item.quantity = int(new_quantity) 
#             item.save()
#             return Response({"message": "Updated", "quantity": item.quantity})
        
#         return Response({"error": "No quantity provided"}, status=400)
    
    
# @extend_schema(
#     request=RegisterSerializer,
#     responses={201: {"message": "User created successfully"}},
#     description="Registers a new user into the system.",
#     tags=['Authentication']
# )
    
# @api_view(['POST'])
# @permission_classes([AllowAny])
# def register_user(request):
#     username = request.data.get('username')
#     password = request.data.get('password')
#     email = request.data.get('email')
    
#     first_name = request.data.get('firstName', '') 
#     last_name = request.data.get('lastName', '')

#     if not username or not password:
#         return Response({"error": "Username and password required"}, status=status.HTTP_400_BAD_REQUEST)

#     if User.objects.filter(username=username).exists():
#         return Response({"error": "User already exists"}, status=status.HTTP_400_BAD_REQUEST)

#     user = User.objects.create_user(
#         username=username, 
#         password=password, 
#         email=email,
#         first_name=first_name,
#         last_name=last_name
#     )
    
#     return Response({"message": "User created successfully"}, status=status.HTTP_201_CREATED)



# @extend_schema(
#     request=LoginSerializer,
#     responses={200: dict},
#     description="Login to get Access and Refresh tokens",
#     tags=['Authentication']
# )
# @api_view(['POST'])
# @permission_classes([AllowAny])
# def login_user(request):
#     username = request.data.get('username')
#     password = request.data.get('password')

#     user = authenticate(username=username, password=password)

#     if user is not None:
#         return Response({
#             'message': 'Login successful',
#             'user': {
#                 'id': user.id,
#                 'username': user.username,
#                 'email': user.email
#             }
#         }, status=status.HTTP_200_OK)
    
#     return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)


# def clean_phone_number(phone):
#     """
#     Clean and format phone number to +996XXXXXXXXX format
#     Accepts: +996701234567, 0701234567, 701234567
#     """
#     phone = str(phone)
#     import re
#     cleaned = re.sub(r'[^\d+]', '', phone)
    
#     if cleaned.startswith('+996'):
#         return cleaned
    
#     if cleaned.startswith('0'):
#         return '+996' + cleaned[1:]
    
#     if len(cleaned) == 9:
#         return '+996' + cleaned
    
#     return '+996' + cleaned[-9:] if len(cleaned) >= 9 else phone

# @api_view(['POST'])
# @permission_classes([AllowAny])
# def initiate_payment(request):
#     """
#     Initiate payment through Mbank
#     User receives push notification on phone and confirms with PIN
    
#     Expected POST data:
#     {
#         "amount": 5000,
#         "phone_number": "+996701234567",
#         "payment_method": "mbank"
#     }
#     """
#     try:
#         data = request.data
#         amount = data.get('amount')
#         phone_number = data.get('phone_number')
#         payment_method = data.get('payment_method', 'mbank')
#         order_id = data.get('order_id')
        
#         if not phone_number:
#             return Response(
#                 {'error': 'Телефон номери талап кылынат'},
#                 status=status.HTTP_400_BAD_REQUEST
#             )
        
#         phone_number = clean_phone_number(phone_number)
        
#         try:
#             amount = float(amount)
#             if amount <= 0:
#                 return Response(
#                     {'error': 'Төлөнүүчү сумма 0дөн чоң болушу керек'},
#                     status=status.HTTP_400_BAD_REQUEST
#                 )
#         except ValueError:
#             return Response(
#                 {'error': 'Төлөнүүчү сумма саны болушу керек'},
#                 status=status.HTTP_400_BAD_REQUEST
#             )
        
#         if order_id:
#             try:
#                 order_id = int(order_id)
#                 order = Order.objects.get(id=order_id)
#                 if order.total_amount != amount:
#                     return Response(
#                         {'error': 'Төлөнүүчү сумма заказдын суммасына дал келбейт'},
#                         status=status.HTTP_400_BAD_REQUEST
#                     )
#                 if Payment.objects.filter(order=order).exists():
#                     return Response(
#                         {'error': 'Бул заказ үчүн төлөм мурунтан эле башталган'},
#                         status=status.HTTP_400_BAD_REQUEST
#                     )
#             except (Order.DoesNotExist, ValueError):
#                 return Response(
#                     {'error': 'Заказ табылган жок'},
#                     status=status.HTTP_404_NOT_FOUND
#                 )
#         else:
#             order = Order.objects.create(
#                 total_amount=amount,
#                 phone_number=phone_number,
#                 status='pending'
#             )
        
#         payment = Payment.objects.create(
#             order=order,
#             payment_method=payment_method,
#             amount=amount,
#             phone_number=phone_number,
#             status='pending'
#         )
        
#         if payment_method == 'mbank':
#             mbank_response = initiate_mbank_payment(
#                 order=order,
#                 payment=payment,
#                 amount=amount,
#                 phone_number=phone_number
#             )
            
#             if mbank_response.get('success'):
#                 payment.mbank_invoice_id = mbank_response.get('invoice_id')
#                 payment.mbank_session_id = mbank_response.get('session_id')
#                 payment.save()
                
#                 return Response({
#                     'success': True,
#                     'payment_id': payment.id,
#                     'order_id': order.id,
#                     'status': 'pending_confirmation',
#                     'message': mbank_response.get('message', 'Та эскерте турган телефонуңузга төлөм сурамасы жиберилди.'),
#                     'amount': amount,
#                     'phone_number': phone_number,
#                     'payment_url': mbank_response.get('payment_url'),
#                 }, status=status.HTTP_201_CREATED)
#             else:
#                 payment.status = 'failed'
#                 payment.save()
                
#                 return Response({
#                     'success': False,
#                     'error': mbank_response.get('message', 'Төлөм жүргүзүүдө ката болду')
#                 }, status=status.HTTP_400_BAD_REQUEST)
#         elif payment_method == 'visa':
#             card_number = data.get('card_number')
#             expiry_month = data.get('expiry_month')
#             expiry_year = data.get('expiry_year')
#             cvv = data.get('cvv')
            
#             if not all([card_number, expiry_month, expiry_year, cvv]):
#                 return Response(
#                     {'error': 'Visa төлөм үчүн карта маалыматтары талап кылынат'},
#                     status=status.HTTP_400_BAD_REQUEST
#                 )
            
#             if len(card_number.replace(' ', '')) < 13 or not card_number.replace(' ', '').isdigit():
#                 return Response(
#                     {'error': 'Жараксыз карта номери'},
#                     status=status.HTTP_400_BAD_REQUEST
#                 )
            
#             time.sleep(2) 
            
#             payment.status = 'success'
#             payment.card_last_four = card_number[-4:]
#             payment.transaction_id = f"DEMO_{payment.id}_{int(time.time())}"
#             payment.save()
#             order.status = 'completed'
#             order.save()
            
#             return Response({
#                 'success': True,
#                 'payment_id': payment.id,
#                 'order_id': order.id,
#                 'status': 'success',
#                 'message': 'Visa төлөм ийгиликтүү жүргүзүлдү (демо режим).',
#                 'amount': amount,
#                 'phone_number': phone_number,
#                 'transaction_id': payment.transaction_id,
#             }, status=status.HTTP_201_CREATED)
        
#         return Response({
#             'success': True,
#             'payment_id': payment.id,
#             'order_id': order.id,
#             'status': 'pending'
#         }, status=status.HTTP_201_CREATED)
        
#     except Exception as e:
#         error_msg = traceback.format_exc()
#         return Response(
#             {'error': error_msg},
#             status=status.HTTP_500_INTERNAL_SERVER_ERROR
#         )
        
        
# @api_view(['POST'])
# @permission_classes([AllowAny])
# def payment_callback(request):
#     """
#     Handle Mbank callback/webhook
#     """
#     try:
#         data = request.data
#         invoice_id = data.get('invoice_id')
#         session_id = data.get('session_id')
#         status_code = data.get('status')
#         amount = data.get('amount')
        
#         payment = Payment.objects.get(mbank_invoice_id=invoice_id)
        
#         checksum_string = f"{invoice_id}{status_code}{MBANK_MERCHANT_SECRET}"
#         import hashlib
#         expected_checksum = hashlib.sha256(checksum_string.encode()).hexdigest()
        
#         if data.get('checksum') != expected_checksum:
#             return Response(
#                 {'error': 'Invalid checksum'},
#                 status=status.HTTP_400_BAD_REQUEST
#             )
        
#         if status_code == 'success':
#             payment.status = 'success'
#             payment.transaction_id = data.get('transaction_id')
#             payment.order.status = 'completed'
#             payment.order.save()
#         elif status_code == 'failed':
#             payment.status = 'failed'
#         elif status_code == 'cancelled':
#             payment.status = 'cancelled'
        
#         payment.save()
        
#         return Response({
#             'success': True,
#             'payment_id': payment.id,
#             'status': payment.status
#         }, status=status.HTTP_200_OK)
        
#     except Payment.DoesNotExist:
#         return Response(
#             {'error': 'Payment not found'},
#             status=status.HTTP_404_NOT_FOUND
#         )
#     except Exception as e:
#         return Response(
#             {'error': str(e)},
#             status=status.HTTP_500_INTERNAL_SERVER_ERROR
#         )


# @api_view(['GET'])
# @permission_classes([AllowAny])
# def payment_status(request, payment_id):
#     """
#     Get payment status
#     """
#     try:
#         payment = Payment.objects.get(id=payment_id)
        
#         return Response({
#             'id': payment.id,
#             'status': payment.status,
#             'amount': str(payment.amount),
#             'payment_method': payment.payment_method,
#             'created_at': payment.created_at,
#             'order_id': payment.order.id
#         })
        
#     except Payment.DoesNotExist:
#         return Response(
#             {'error': 'Payment not found'},
#             status=status.HTTP_404_NOT_FOUND
#         )

# @api_view(['POST'])
# @permission_classes([AllowAny])
# @authentication_classes([])
# def clothing_questionnaire(request):
#     try:
        
#         data = request.data
#         occasion = data.get('occasion')
#         body_type = data.get('body_type')
#         preferred_colors = data.get('preferred_colors', [])
#         budget = data.get('budget')
#         gender = data.get('gender')
        
#         if not all([occasion, body_type, gender]):
#             missing_fields = []
#             if not occasion: missing_fields.append('occasion')
#             if not body_type: missing_fields.append('body_type')
#             if not gender: missing_fields.append('gender')
            
#             return Response(
#                 {'error': f'Missing required fields: {", ".join(missing_fields)}'},
#                 status=status.HTTP_400_BAD_REQUEST
#             )
        
#         allowed_categories = ['Кийим-кече', 'Бут кийим']
#         excluded_article_types = [
#             'Дезодарант', 'Духи жана спрей', 'Духи топтому', 'Парфюмерия',
#             'Шарф', 'Шарфтар', 'Галстук', 'Галстуктар', 'Ремень', 'Ремендер',
#             'Көз айнек', 'Көз айнектер', 'Зергер буюмдары топтому', 'Зер буюмдардар',
#             'Шурулар', 'Билериктер', 'Сөйкөлөр', 'Шакек', 'Браслет', 'Кулон',
#             'Саат', 'Сааттар', 'Макияж', 'Тырмактар', 'Териге кам көрүү',
#             'Дене жана ванна үчүн Каражаттар', 'Духи', 'Помада', 'Тушь',
#             'Суу бытылка', 'Планшетке чехол', 'Чехол', 'Зонт', 'Зонттор',
#             'Көйнөктөр', 'Зер буюмдардар', 'Клатч', 'Помада', 'Бюстгалтер'
#         ]
        
    
#         occasion_mapping = {
#             'casual': {
#                 'usage': 'Күн сайын',
#                 'article_types': ['Футболка', 'Джинсы', 'Шымдар', 'Шорты', 'Юбка', 
#                                 'Толстовка', 'Майка', 'Капри', 'Күнүмдүк бут кийим', 
#                                 'Сандалдар', 'Балетка', 'Шлепки']
#             },
#             'formal': {
#                 'usage': 'Формалдуу',
#                 'article_types': ['Костюм', 'Рубашка', 'Расмий бут кийим', 'Көйнөк', 
#                                 'Туфли', 'Жилетка']
#             },
#             'party': {
#                 'usage': 'Кече',
#                 'article_types': ['Көйнөк', 'Туфли', 'Юбка', 'Костюм', 'Балетка']
#             },
#             'sports': {
#                 'usage': 'Спорт',
#                 'article_types': ['Спорттук шымдар', 'Спорт бут кийим', 'Спорттук костюмдар',
#                                 'Толстовка', 'Шорты', 'Спорт Сандалдар', 'Футболка']
#             },
#             'travel': {
#                 'usage': 'Саякат',
#                 'article_types': ['Спорттук шымдар', 'Күнүмдүк бут кийим', 'Толстовка',
#                                 'Джинсы', 'Футболка', 'Сандалдар', 'Шорты']
#             }
#         }
        
#         body_type_mapping = {
#             'slim': ['Slim Fit'],
#             'regular': ['Regular Fit', 'Standard Fit', 'Fitted/Standard'],
#             'athletic': ['Regular Fit', 'Slim Fit', 'Fitted/Standard'],
#             'plus': ['Relaxed Fit', 'Comfort Fit'],
#             'petite': ['Slim Fit', 'Regular Fit']
#         }
        
#         color_mapping = {
#             'black': ['Кара', 'Көмүр', 'Кара-Көк'], 
#             'blue': ['Көк', 'Бирюзовый', 'Бирюза-көк', 'Кызгылт көк', 'Кара-Көк'],  
#             'red': ['Кызыл', 'Бургундия', 'Роза'],
#             'green': ['Жашыл', 'Хаки', 'Оливка', 'Лайм', 'Деңиз жашыл', 'Флуоресцент жашыл'], 
#             'white': ['Ак', 'Серебро', 'Беж', 'Ак-кичине бос', 'Крем'], 
#             'brown': ['Күрөң', 'Беж', 'Кофе күрөң', 'Ачык-Күрөң', 'Боз-күрөң', 'Грибной коричневый', 'Нюд', 'Тери', 'Ржавчина'], 
#             'gray': ['Боз', 'Боз меланж', 'Күңүрт', 'Боз-күрөң', 'Серебро', 'Болот', 'Металдык'], 
#             'yellow': ['Сары', 'Горчица', 'Жез', 'Алтын'],  
#             'purple': ['Фиолетовый', 'Лаванда', 'Пурпурный'], 
#             'pink': ['Кызгылт', 'Роза', 'Персик', 'Кызгылт көк'],  
#             'multi': ['Көп түс'], 
#             'orange': ['Персик', 'Ржавчина', 'Жез'], 
#             'bronze': ['Бронза', 'Алтын', 'Металдык']  
#         }
        
#         try:
#             query = Product.objects.all()
#             query = query.filter(masterCategory__in=allowed_categories)
#             query = query.exclude(articleType__in=excluded_article_types)
            
#             if gender:
#                 query = query.filter(gender__iexact=gender)
#             occasion_config = occasion_mapping.get(occasion, occasion_mapping.get('casual'))
            
#             if occasion_config.get('usage'):
#                 query = query.filter(usage__iexact=occasion_config['usage'])
            
#             if occasion_config.get('article_types'):
#                 query = query.filter(articleType__in=occasion_config['article_types'])
            
#             # Fix 1: Body type filter — only apply if field has data, use OR with null check
#             if body_type and body_type in body_type_mapping:
#                 silhouette_filter = body_type_mapping[body_type]
#                 silhouette_condition = models.Q()
#                 for fit in silhouette_filter:
#                     silhouette_condition |= models.Q(silhouette__icontains=fit)
#                     silhouette_condition |= models.Q(figure__icontains=fit)
                
#                 if query.filter(silhouette_condition).exists():
#                     query = query.filter(silhouette_condition)
                    
#             if preferred_colors:
#                 color_condition = models.Q()
#                 for color in preferred_colors:
#                     color_variants = color_mapping.get(color.lower(), [color])
#                     print(f"Filtering for color '{color}' → variants: {color_variants}") 
#                     for variant in color_variants:
#                         color_condition |= models.Q(color__iexact=variant) 
                
#                 filtered = query.filter(color_condition)
#                 if filtered.exists():
#                     query = filtered
#                 else:
#                     print(f"No products matched color filter, skipping color...")
            
#             if budget:
#                 if budget == 'low':
#                     query = query.filter(price__lte=2000)
#                 elif budget == 'medium':
#                     query = query.filter(price__gte=2000, price__lte=5000)
#                 elif budget == 'high':
#                     query = query.filter(price__gte=5000)
            
#             recommended_products = query.order_by('?')[:10]
            
#             if not recommended_products.exists() and preferred_colors:
#                 print("No products found with color filter, removing color filter...")
#                 query = Product.objects.filter(
#                     masterCategory__in=allowed_categories
#                 ).exclude(
#                     articleType__in=excluded_article_types
#                 )
                
#                 if gender:
#                     query = query.filter(gender__iexact=gender)
                
#                 if occasion_config.get('usage'):
#                     query = query.filter(usage__iexact=occasion_config['usage'])
                
#                 if occasion_config.get('article_types'):
#                     query = query.filter(articleType__in=occasion_config['article_types'])
                
#                 if body_type and body_type in body_type_mapping:
#                     silhouette_condition = models.Q()
#                     for fit in body_type_mapping[body_type]:
#                         silhouette_condition |= models.Q(silhouette__icontains=fit)
#                     if silhouette_condition:
#                         query = query.filter(silhouette_condition)
                
#                 if budget:
#                     if budget == 'low':
#                         query = query.filter(price__lte=2000)
#                     elif budget == 'medium':
#                         query = query.filter(price__gte=2000, price__lte=5000)
#                     elif budget == 'high':
#                         query = query.filter(price__gte=5000)
                
#                 recommended_products = query.order_by('?')[:10]
            
#             if not recommended_products.exists():
#                 query = Product.objects.filter(
#                     masterCategory__in=allowed_categories
#                 ).exclude(
#                     articleType__in=excluded_article_types
#                 ).filter(
#                     gender__iexact=gender
#                 )
                
#                 if occasion_config.get('usage'):
#                     query = query.filter(usage__iexact=occasion_config['usage'])
                
#                 if occasion_config.get('article_types'):
#                     query = query.filter(articleType__in=occasion_config['article_types'])
                
#                 if budget:
#                     if budget == 'low':
#                         query = query.filter(price__lte=2000)
#                     elif budget == 'medium':
#                         query = query.filter(price__gte=2000, price__lte=5000)
#                     elif budget == 'high':
#                         query = query.filter(price__gte=5000)
                
#                 logger.info(f"After relaxing filters (no body type), found {query.count()} products")
#                 recommended_products = query.order_by('?')[:10]
            
#             if not recommended_products.exists():
#                 logger.warning("Still no products, trying without occasion filter...")
#                 query = Product.objects.filter(
#                     masterCategory__in=allowed_categories
#                 ).exclude(
#                     articleType__in=excluded_article_types
#                 ).filter(
#                     gender__iexact=gender
#                 )
                
#                 if budget:
#                     if budget == 'low':
#                         query = query.filter(price__lte=2000)
#                     elif budget == 'medium':
#                         query = query.filter(price__gte=2000, price__lte=5000)
#                     elif budget == 'high':
#                         query = query.filter(price__gte=5000)
                
#                 logger.info(f"After removing occasion filter, found {query.count()} products")
#                 recommended_products = query.order_by('?')[:10]
            
#             if not recommended_products.exists():
#                 logger.warning(f"No products found for gender: {gender}, occasion: {occasion}")
#                 return Response({
#                     'recommendations': [],
#                     'recommendation_count': 0,
#                     'message': 'No products match your criteria. Please try different preferences.',
#                     'filters_applied': {
#                         'occasion': occasion,
#                         'body_type': body_type,
#                         'preferred_colors': preferred_colors,
#                         'budget': budget,
#                         'gender': gender
#                     }
#                 }, status=status.HTTP_200_OK)
            
#             serializer = ProductSerializer(recommended_products, many=True)
            
#             return Response({
#                 'recommendations': serializer.data,
#                 'recommendation_count': recommended_products.count(),
#                 'filters_applied': {
#                     'occasion': occasion,
#                     'body_type': body_type,
#                     'preferred_colors': preferred_colors,
#                     'budget': budget,
#                     'gender': gender
#                 }
#             }, status=status.HTTP_200_OK)
            
#         except Exception as db_error:
#             logger.error(f"Database query error: {str(db_error)}", exc_info=True)
#             return Response({
#                 'recommendations': [],
#                 'recommendation_count': 0,
#                 'error': 'Database query error',
#                 'message': str(db_error)
#             }, status=status.HTTP_200_OK)
        
#     except Exception as e:
#         logger.error(f"Unexpected error in clothing_questionnaire: {str(e)}", exc_info=True)
#         return Response(
#             {'error': 'Internal server error', 'details': str(e)},
#             status=status.HTTP_500_INTERNAL_SERVER_ERROR
#         )


# def build_base_query(gender, allowed_categories, excluded_article_types, occasion_config, budget):
#     q = Product.objects.filter(
#         masterCategory__in=allowed_categories,
#         gender__iexact=gender
#     ).exclude(articleType__in=excluded_article_types)
    
#     if occasion_config.get('usage'):
#         q = q.filter(usage__iexact=occasion_config['usage'])
#     if occasion_config.get('article_types'):
#         q = q.filter(articleType__in=occasion_config['article_types'])
#     if budget == 'low':
#         q = q.filter(price__lte=2000)
#     elif budget == 'medium':
#         q = q.filter(price__gte=2000, price__lte=5000)
#     elif budget == 'high':
#         q = q.filter(price__gte=5000)
#     return q


# @api_view(['GET'])
# @permission_classes([AllowAny])
# @authentication_classes([])
# def debug_product_fields(request):
#     """Debug endpoint to check available fields and sample data"""
#     try:
#         # Get one sample product
#         sample = Product.objects.first()
        
#         if sample:
#             # Get all field names and their values
#             fields = {}
#             for field in sample._meta.get_fields():
#                 field_name = field.name
#                 try:
#                     value = getattr(sample, field_name)
#                     fields[field_name] = str(value)[:100]  # Truncate long values
#                 except:
#                     fields[field_name] = "Unable to retrieve"
            
#             # Get unique values for key fields
#             unique_values = {}
#             for field_name in ['gender', 'usage', 'masterCategory', 'subCategory', 'articleType', 'season']:
#                 if hasattr(Product, field_name):
#                     values = Product.objects.values_list(field_name, flat=True).distinct()[:20]
#                     unique_values[field_name] = list(values)
            
#             return Response({
#                 'sample_product_fields': fields,
#                 'unique_values': unique_values,
#                 'total_products': Product.objects.count()
#             })
#         else:
#             return Response({'error': 'No products found in database'})
    
#     except Exception as e:
#         return Response({'error': str(e)})



# def get_current_season():
#     """Helper function to determine current season"""
#     import datetime
#     month = datetime.datetime.now().month
    
#     if month in [12, 1, 2]:
#         return 'Кыш'  
#     elif month in [3, 4, 5]:
#         return 'Жаз'  
#     elif month in [6, 7, 8]:
#         return 'Жай' 
#     else:
#         return 'Күз'  
    
# @api_view(['POST'])
# @permission_classes([AllowAny])
# def virtual_try_on(request):
#     """
#     Process virtual try-on using Gemini API
#     """
#     try:
#         if 'user_image' not in request.FILES:
#             return Response(
#                 {'error': 'User image is required'},
#                 status=status.HTTP_400_BAD_REQUEST
#             )
        
#         user_image = request.FILES['user_image']
#         product_id = request.data.get('product_id')
        
#         if not product_id:
#             return Response(
#                 {'error': 'Product ID is required'},
#                 status=status.HTTP_400_BAD_REQUEST
#             )
        
#         try:
#             product = Product.objects.get(product_id=product_id)
#         except Product.DoesNotExist:
#             return Response(
#                 {'error': 'Product not found'},
#                 status=status.HTTP_404_NOT_FOUND
#             )
        
#         genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))
#         model = genai.GenerativeModel('gemini-1.5-flash')
        
#         user_image_data = user_image.read()
        
#         import requests
#         from io import BytesIO
        
#         try:
#             product_response = requests.get(product.link)
#             product_image_data = BytesIO(product_response.content)
#         except:
#             return Response(
#                 {'error': 'Could not load product image'},
#                 status=status.HTTP_400_BAD_REQUEST
#             )
        
#         prompt = f"""
#         You are an expert fashion stylist and image editor. Perform a realistic virtual try-on of the clothing item onto the person in the photo.
        
#         Product Details:
#         - Name: {product.productDisplayName}
#         - Type: {product.articleType}
#         - Category: {product.subCategory}
#         - Color: {product.color}
        
#         Instructions:
#         1. Analyze the person's pose, body shape, and proportions
#         2. Virtually fit the clothing item realistically onto the person
#         3. Ensure the clothing drapes naturally and fits properly
#         4. Maintain the person's original face, hair, and background
#         5. Make the result look as realistic as possible
#         6. Preserve lighting and shadows consistency
        
#         Return only the edited image with the clothing virtually tried on.
#         """
        
#         response = model.generate_content([
#             prompt,
#             {
#                 "mime_type": "image/jpeg",
#                 "data": user_image_data
#             },
#             {
#                 "mime_type": "image/jpeg", 
#                 "data": product_image_data.getvalue()
#             }
#         ])
        
#         return Response({
#             'success': True,
#             'message': 'Virtual try-on processed successfully',
#             'product': {
#                 'id': product.product_id,
#                 'name': product.productDisplayName,
#                 'price': product.price,
#                 'image_url': product.link
#             },
#             'note': 'Image generation completed. In production, this would return the edited image URL.'
#         })
        
#     except Exception as e:
#         print(f"Virtual try-on error: {e}")
#         return Response(
#             {'error': str(e)},
#             status=status.HTTP_500_INTERNAL_SERVER_ERROR
#         )
        
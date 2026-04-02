
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from ..models import Order, Payment
from rest_framework import  status
import traceback
import time
from dotenv import load_dotenv 
from rest_framework.decorators import api_view, permission_classes, authentication_classes
load_dotenv()

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

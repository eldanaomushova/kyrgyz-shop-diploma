
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.contrib.auth.models import User
from drf_spectacular.utils import extend_schema
from rest_framework import serializers, status
from django.contrib.auth import authenticate
from dotenv import load_dotenv 
from rest_framework.decorators import api_view, permission_classes, authentication_classes
load_dotenv()

class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()
    email = serializers.EmailField()
    firstName = serializers.CharField(required=False)
    lastName = serializers.CharField(required=False)

    
class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()

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
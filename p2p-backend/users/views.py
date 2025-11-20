from django.contrib.auth import get_user_model, authenticate
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework_simplejwt.tokens import RefreshToken
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes
from .serializers import UserSerializer, UserRegistrationSerializer, LoginSerializer

User = get_user_model()

class UserViewSet(ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Users can only see themselves unless they are superuser
        if self.request.user.is_superuser:
            return User.objects.all()
        return User.objects.filter(id=self.request.user.id)

class RegisterView(APIView):
    permission_classes = [AllowAny]
    serializer_class = UserRegistrationSerializer

    @extend_schema(
        request=UserRegistrationSerializer,
        responses={
            201: {
                'type': 'object',
                'properties': {
                    'message': {'type': 'string'},
                    'user': UserSerializer,
                    'refresh': {'type': 'string'},
                    'access': {'type': 'string'}
                }
            },
            400: {
                'type': 'object',
                'properties': {
                    'message': {'type': 'string'},
                    'errors': {'type': 'object'}
                }
            }
        },
        description="Register a new user with email, password, role, first_name, and last_name",
        examples=[
            OpenApiExample(
                'Register Example',
                value={
                    'email': 'user@example.com',
                    'password': 'SecurePass123',
                    'password2': 'SecurePass123',
                    'role': 'staff',
                    'first_name': 'John',
                    'last_name': 'Doe'
                },
                request_only=True
            )
        ]
    )
    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)
            return Response({
                'message': 'User registered successfully',
                'user': UserSerializer(user).data,
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }, status=status.HTTP_201_CREATED)
        return Response({
            'message': 'Registration failed',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    permission_classes = [AllowAny]
    serializer_class = LoginSerializer

    @extend_schema(
        request=LoginSerializer,
        responses={
            200: {
                'type': 'object',
                'properties': {
                    'message': {'type': 'string'},
                    'refresh': {'type': 'string', 'description': 'JWT refresh token'},
                    'access': {'type': 'string', 'description': 'JWT access token'},
                    'user': {
                        'type': 'object',
                        'properties': {
                            'id': {'type': 'integer'},
                            'email': {'type': 'string'},
                            'first_name': {'type': 'string'},
                            'last_name': {'type': 'string'},
                            'full_name': {'type': 'string'},
                            'role': {'type': 'string'},
                            'is_active': {'type': 'boolean'}
                        }
                    }
                }
            },
            400: {
                'type': 'object',
                'properties': {
                    'message': {'type': 'string'},
                    'errors': {'type': 'object'}
                }
            },
            401: {
                'type': 'object',
                'properties': {
                    'message': {'type': 'string'},
                    'error': {'type': 'string'}
                }
            }
        },
        description="Login with email and password to get JWT tokens",
        examples=[
            OpenApiExample(
                'Login Example',
                value={
                    'email': 'staff@test.com',
                    'password': 'test123'
                },
                request_only=True
            )
        ]
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            password = serializer.validated_data['password']
            user = authenticate(request, username=email, password=password)
            
            if user is not None:
                refresh = RefreshToken.for_user(user)
                return Response({
                    'message': 'Login successful',
                    'user': UserSerializer(user).data,
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                }, status=status.HTTP_200_OK)
            return Response({
                'message': 'Invalid credentials',
                'error': 'Email or password is incorrect'
            }, status=status.HTTP_401_UNAUTHORIZED)
        return Response({
            'message': 'Validation failed',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

@extend_schema(
    responses={200: UserSerializer},
    description="Get current authenticated user details"
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def current_user(request):
    serializer = UserSerializer(request.user)
    return Response(serializer.data)
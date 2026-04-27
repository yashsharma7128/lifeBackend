from django.utils import timezone
from django.contrib.auth import authenticate
from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User, Product, Order, AMC, Contact, BrochureDownload
from .serializers import (
    UserSerializer, UserPublicSerializer, LoginSerializer,
    ProductSerializer, OrderSerializer, AMCSerializer,
    ContactSerializer, BrochureDownloadSerializer
)


# ─────────────────────────────────────────────
# PERMISSIONS
# ─────────────────────────────────────────────
class IsAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'admin'


# ─────────────────────────────────────────────
# AUTH VIEWS
# ─────────────────────────────────────────────
class RegisterView(APIView):
    """POST /api/auth/register/  — Public"""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)
            return Response({
                'access':  str(refresh.access_token),
                'refresh': str(refresh),
                'user':    UserPublicSerializer(user).data,
                'message': 'Registration successful'
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    """
    POST /api/auth/login/  — Public
    Body: { "identifier": "username OR email", "password": "..." }
    Logic: '@' in identifier → email login, else → username login
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        identifier = serializer.validated_data['identifier']
        password   = serializer.validated_data['password']
        print(identifier)
        # Determine login method
        try:
            if '@' in identifier:
                user_obj = User.objects.get(email=identifier)
            else:
                user_obj = User.objects.get(username=identifier)
        except User.DoesNotExist:
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
        print("here")
        # Authenticate with resolved username
        user = authenticate(request, username=user_obj.username, password=password)
        if not user:
            return Response({'error': 'Invalid credentials password'}, status=status.HTTP_401_UNAUTHORIZED)

        if not user.is_active:
            return Response({'error': 'Account is disabled'}, status=status.HTTP_403_FORBIDDEN)

        refresh = RefreshToken.for_user(user)
        return Response({
            'access':  str(refresh.access_token),
            'refresh': str(refresh),
            'user':    UserPublicSerializer(user).data,
            'message': 'Login successful'
        })


class MeView(APIView):
    """GET /api/auth/me/  — Authenticated"""
    def get(self, request):
        return Response(UserPublicSerializer(request.user).data)

    def patch(self, request):
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(UserPublicSerializer(request.user).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ─────────────────────────────────────────────
# USER VIEWS (Admin only)
# ─────────────────────────────────────────────
class UserListView(generics.ListCreateAPIView):
    """GET /api/users/  POST /api/users/  — Admin"""
    queryset = User.objects.all().order_by('-created_at')
    serializer_class = UserSerializer
    permission_classes = [IsAdmin]

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return UserPublicSerializer
        return UserSerializer


class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    """GET/PATCH/DELETE /api/users/<id>/  — Admin"""
    queryset = User.objects.all()
    permission_classes = [IsAdmin]

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return UserPublicSerializer
        return UserSerializer


# ─────────────────────────────────────────────
# PRODUCT VIEWS
# ─────────────────────────────────────────────
class ProductListView(generics.ListCreateAPIView):
    """GET /api/products/  — Public | POST — Admin"""
    queryset = Product.objects.filter(is_active=True)
    serializer_class = ProductSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAdmin()]
        return [permissions.AllowAny()]


class ProductDetailView(generics.RetrieveUpdateDestroyAPIView):
    """GET /api/products/<id>/  — Public | PATCH/DELETE — Admin"""
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

    def get_permissions(self):
        if self.request.method == 'GET':
            return [permissions.AllowAny()]
        return [IsAdmin()]


# ─────────────────────────────────────────────
# ORDER VIEWS
# ─────────────────────────────────────────────
class OrderListView(generics.ListCreateAPIView):
    """GET /api/orders/  — Admin sees all, User sees own | POST — Admin"""
    serializer_class = OrderSerializer

    def get_queryset(self):
        if self.request.user.role == 'admin':
            return Order.objects.all()
        return Order.objects.filter(user=self.request.user)

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAdmin()]
        return [permissions.IsAuthenticated()]

    def perform_create(self, serializer):
        serializer.save()


class OrderDetailView(generics.RetrieveUpdateDestroyAPIView):
    """GET/PATCH/DELETE /api/orders/<id>/"""
    serializer_class = OrderSerializer

    def get_queryset(self):
        if self.request.user.role == 'admin':
            return Order.objects.all()
        return Order.objects.filter(user=self.request.user)

    def get_permissions(self):
        if self.request.method == 'GET':
            return [permissions.IsAuthenticated()]
        return [IsAdmin()]


@api_view(['GET'])
@permission_classes([IsAdmin])
def orders_by_product(request, product_id):
    """GET /api/orders/product/<product_id>/  — Track orders by product_id"""
    orders = Order.objects.filter(product_id=product_id)
    return Response(OrderSerializer(orders, many=True).data)


# ─────────────────────────────────────────────
# AMC VIEWS
# ─────────────────────────────────────────────
class AMCListView(generics.ListCreateAPIView):
    """GET /api/amc/  — Admin sees all, User sees own | POST — Admin"""
    serializer_class = AMCSerializer

    def get_queryset(self):
        qs = AMC.objects.all()
        if self.request.user.role != 'admin':
            qs = qs.filter(user=self.request.user)
        # Auto-update expired AMC status
        today = timezone.now().date()
        qs.filter(end_date__lt=today, status='active').update(status='expired')
        return qs

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAdmin()]
        return [permissions.IsAuthenticated()]


class AMCDetailView(generics.RetrieveUpdateDestroyAPIView):
    """GET/PATCH/DELETE /api/amc/<id>/"""
    serializer_class = AMCSerializer
    permission_classes = [IsAdmin]
    queryset = AMC.objects.all()


# ─────────────────────────────────────────────
# CONTACT VIEWS
# ─────────────────────────────────────────────
class ContactCreateView(generics.CreateAPIView):
    """POST /api/contact/  — Public (from contact form)"""
    serializer_class = ContactSerializer
    permission_classes = [permissions.AllowAny]

    def perform_create(self, serializer):
        ip = self.request.META.get('REMOTE_ADDR')
        serializer.save(ip_address=ip)


class ContactListView(generics.ListAPIView):
    """GET /api/contact/  — Admin only"""
    queryset = Contact.objects.all()
    serializer_class = ContactSerializer
    permission_classes = [IsAdmin]


class ContactDetailView(generics.RetrieveUpdateDestroyAPIView):
    """PATCH /api/contact/<id>/  — Admin (update status to resolved)"""
    queryset = Contact.objects.all()
    serializer_class = ContactSerializer
    permission_classes = [IsAdmin]


# ─────────────────────────────────────────────
# BROCHURE DOWNLOAD TRACKING
# ─────────────────────────────────────────────
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def track_brochure_download(request, brochure_type):
    """
    POST /api/brochure/download/<water|air>/
    Increments download count and returns current count.
    """
    if brochure_type not in ['water', 'air']:
        return Response({'error': 'Invalid brochure type'}, status=status.HTTP_400_BAD_REQUEST)

    obj, _ = BrochureDownload.objects.get_or_create(brochure_type=brochure_type)
    obj.count += 1
    obj.last_download = timezone.now()
    obj.save()

    return Response({
        'brochure_type': brochure_type,
        'count': obj.count,
        'message': f'Download tracked. Total: {obj.count}'
    })


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def brochure_counts(request):
    """GET /api/brochure/counts/  — Returns download counts for all brochures"""
    data = {}
    for obj in BrochureDownload.objects.all():
        data[obj.brochure_type] = obj.count
    return Response(data)


# ─────────────────────────────────────────────
# DASHBOARD STATS (Admin)
# ─────────────────────────────────────────────
@api_view(['GET'])
@permission_classes([IsAdmin])
def admin_dashboard(request):
    """GET /api/admin/dashboard/  — Summary stats"""
    today = timezone.now().date()
    AMC.objects.filter(end_date__lt=today, status='active').update(status='expired')

    return Response({
        'total_users':         User.objects.filter(role='user').count(),
        'total_orders':        Order.objects.count(),
        'active_amc':          AMC.objects.filter(status='active').count(),
        'expired_amc':         AMC.objects.filter(status='expired').count(),
        'pending_contacts':    Contact.objects.filter(status='pending').count(),
        'resolved_contacts':   Contact.objects.filter(status='resolved').count(),
        'brochure_downloads':  {
            obj.brochure_type: obj.count
            for obj in BrochureDownload.objects.all()
        },
        'recent_orders': OrderSerializer(
            Order.objects.order_by('-created_at')[:5], many=True
        ).data,
    })

"""
LIFE CARE RO SYSTEMS — URL Routes
==================================
Auth:
  POST   /api/auth/register/          Register new user
  POST   /api/auth/login/             Login with username OR email
  POST   /api/auth/token/refresh/     Refresh JWT token
  GET    /api/auth/me/                Get current user profile
  PATCH  /api/auth/me/                Update profile

Users (Admin):
  GET    /api/users/                  List all users
  POST   /api/users/                  Create user
  GET    /api/users/<id>/             User detail
  PATCH  /api/users/<id>/             Update user
  DELETE /api/users/<id>/             Delete user

Products:
  GET    /api/products/               List products (public)
  POST   /api/products/               Create product (admin)
  GET    /api/products/<id>/          Product detail
  PATCH  /api/products/<id>/          Update product (admin)
  DELETE /api/products/<id>/          Delete product (admin)

Orders:
  GET    /api/orders/                 List orders (admin=all, user=own)
  POST   /api/orders/                 Create order (admin)
  GET    /api/orders/<id>/            Order detail
  PATCH  /api/orders/<id>/            Update status (admin)
  GET    /api/orders/product/<pid>/   Track by product_id (admin)

AMC:
  GET    /api/amc/                    List AMC plans
  POST   /api/amc/                    Create AMC plan (admin)
  GET    /api/amc/<id>/               AMC detail
  PATCH  /api/amc/<id>/               Update AMC (admin)

Contact:
  POST   /api/contact/                Submit contact form (public)
  GET    /api/contact/                List inquiries (admin)
  PATCH  /api/contact/<id>/           Update status (admin)

Brochure:
  POST   /api/brochure/download/<type>/   Track download (public)
  GET    /api/brochure/counts/            Download counts

Admin Dashboard:
  GET    /api/admin/dashboard/        Summary stats
"""
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

urlpatterns = [
    # Auth
    path('auth/register/',      views.RegisterView.as_view()),
    path('auth/login/',         views.LoginView.as_view()),
    path('auth/token/refresh/', TokenRefreshView.as_view()),
    path('auth/me/',            views.MeView.as_view()),

    # Users
    path('users/',              views.UserListView.as_view()),
    path('users/<int:pk>/',     views.UserDetailView.as_view()),

    # Products
    path('products/',           views.ProductListView.as_view()),
    path('products/<int:pk>/',  views.ProductDetailView.as_view()),

    # Orders
    path('orders/',                          views.OrderListView.as_view()),
    path('orders/<int:pk>/',                 views.OrderDetailView.as_view()),
    path('orders/product/<str:product_id>/', views.orders_by_product),

    # AMC
    path('amc/',            views.AMCListView.as_view()),
    path('amc/<int:pk>/',   views.AMCDetailView.as_view()),

    # Contact
    path('contact/',            views.ContactCreateView.as_view()),
    path('contact/list/',       views.ContactListView.as_view()),
    path('contact/<int:pk>/',   views.ContactDetailView.as_view()),

    # Brochure
    path('brochure/download/<str:brochure_type>/', views.track_brochure_download),
    path('brochure/counts/',                       views.brochure_counts),

    # Admin
    path('admin/dashboard/', views.admin_dashboard),
]

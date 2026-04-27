from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone


class UserManager(BaseUserManager):
    def create_user(self, username, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email is required')
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'admin')
        return self.create_user(username, email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Collection: users
    Supports login via username OR email (identifier field)
    """
    ROLE_CHOICES = [('user', 'User'), ('admin', 'Admin')]

    username   = models.CharField(max_length=150, unique=True)
    email      = models.EmailField(unique=True)
    name       = models.CharField(max_length=200)
    phone      = models.CharField(max_length=15, blank=True)
    role       = models.CharField(max_length=10, choices=ROLE_CHOICES, default='user')
    is_active  = models.BooleanField(default=True)
    is_staff   = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    objects = UserManager()
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email', 'name']

    class Meta:
        db_table = 'users'

    def __str__(self):
        return f'{self.name} ({self.username})'


class Product(models.Model):
    """
    Collection: products
    Hardcoded in frontend — this model tracks orders/AMC references
    """
    CATEGORY_CHOICES = [('water', 'Water Purifier'), ('air', 'Air Purifier')]

    product_id  = models.CharField(max_length=50, unique=True)
    name        = models.CharField(max_length=200)
    description = models.TextField()
    price       = models.CharField(max_length=50)
    category    = models.CharField(max_length=10, choices=CATEGORY_CHOICES)
    specs       = models.JSONField(default=list)
    badge       = models.CharField(max_length=50, blank=True)
    is_active   = models.BooleanField(default=True)
    created_at  = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'products'

    def __str__(self):
        return f'[{self.product_id}] {self.name}'


class Order(models.Model):
    """
    Collection: orders
    Tracks which user bought which product (by product_id)
    """
    PAYMENT_CHOICES = [('cash', 'Cash'), ('upi', 'UPI')]
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]

    order_id     = models.CharField(max_length=50, unique=True)
    user         = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    product_id   = models.CharField(max_length=50)   # References hardcoded product
    product_name = models.CharField(max_length=200)
    amount       = models.CharField(max_length=50)
    payment_mode = models.CharField(max_length=10, choices=PAYMENT_CHOICES, default='cash')
    status       = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending')
    notes        = models.TextField(blank=True)
    created_at   = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'orders'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.order_id} — {self.user.name} — {self.product_name}'


class AMC(models.Model):
    """
    Collection: amc
    Annual Maintenance Contract per user per product
    """
    STATUS_CHOICES = [('active', 'Active'), ('expired', 'Expired'), ('cancelled', 'Cancelled')]

    amc_id       = models.CharField(max_length=50, unique=True)
    user         = models.ForeignKey(User, on_delete=models.CASCADE, related_name='amc_plans')
    product_id   = models.CharField(max_length=50)
    product_name = models.CharField(max_length=200)
    start_date   = models.DateField()
    end_date     = models.DateField()
    next_service = models.DateField(null=True, blank=True)
    amount       = models.CharField(max_length=50)
    status       = models.CharField(max_length=12, choices=STATUS_CHOICES, default='active')
    created_at   = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'amc'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.amc_id} — {self.user.name} — {self.product_name} ({self.status})'


class Contact(models.Model):
    """
    Collection: contacts
    Customer inquiries from the contact form
    """
    STATUS_CHOICES = [('pending', 'Pending'), ('resolved', 'Resolved'), ('spam', 'Spam')]

    name       = models.CharField(max_length=200)
    phone      = models.CharField(max_length=15)
    message    = models.TextField()
    status     = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'contacts'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.name} ({self.phone}) — {self.status}'


class BrochureDownload(models.Model):
    """
    Tracks brochure download counts
    """
    TYPE_CHOICES = [('water', 'Water Purifier'), ('air', 'Air Purifier')]

    brochure_type = models.CharField(max_length=10, choices=TYPE_CHOICES, unique=True)
    count         = models.IntegerField(default=0)
    last_download = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'brochure_downloads'

    def __str__(self):
        return f'{self.brochure_type} — {self.count} downloads'

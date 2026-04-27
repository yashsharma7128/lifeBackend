from rest_framework import serializers
from .models import User, Product, Order, AMC, Contact, BrochureDownload


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'name', 'phone', 'role',
                  'is_active', 'created_at', 'password']
        read_only_fields = ['id', 'created_at']

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for attr, val in validated_data.items():
            setattr(instance, attr, val)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


class UserPublicSerializer(serializers.ModelSerializer):
    """Safe serializer — no sensitive fields"""
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'name', 'phone', 'role', 'created_at']


class LoginSerializer(serializers.Serializer):
    """
    Accepts either username or email in the 'identifier' field.
    Backend logic: if '@' in identifier → email login, else → username login
    """
    identifier = serializers.CharField()
    password   = serializers.CharField(write_only=True)


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'


class OrderSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.name', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'order_id', 'user', 'user_name', 'user_email',
                  'product_id', 'product_name', 'amount', 'payment_mode',
                  'status', 'notes', 'created_at']
        read_only_fields = ['id', 'order_id', 'created_at', 'user_name', 'user_email']

    def create(self, validated_data):
        # Auto-generate order ID
        count = Order.objects.count() + 1
        validated_data['order_id'] = f'ORD-{str(count).zfill(4)}'
        return super().create(validated_data)


class AMCSerializer(serializers.ModelSerializer):
    user_name  = serializers.CharField(source='user.name', read_only=True)
    user_phone = serializers.CharField(source='user.phone', read_only=True)

    class Meta:
        model = AMC
        fields = ['id', 'amc_id', 'user', 'user_name', 'user_phone',
                  'product_id', 'product_name', 'start_date', 'end_date',
                  'next_service', 'amount', 'status', 'created_at']
        read_only_fields = ['id', 'amc_id', 'created_at', 'user_name', 'user_phone']

    def create(self, validated_data):
        count = AMC.objects.count() + 1
        validated_data['amc_id'] = f'AMC-{str(count).zfill(4)}'
        return super().create(validated_data)


class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = ['id', 'name', 'phone', 'message', 'status', 'created_at']
        read_only_fields = ['id',  'created_at']


class BrochureDownloadSerializer(serializers.ModelSerializer):
    class Meta:
        model = BrochureDownload
        fields = ['brochure_type', 'count', 'last_download']

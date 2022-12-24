from django.contrib.auth.hashers import make_password
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import User


class SignUpSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    username = serializers.RegexField(regex='^[\w.@+-]+$', required=True, max_length=150, min_length=1,
                                      allow_null=False, allow_blank=False)
    first_name = serializers.CharField(required=False, max_length=150, allow_blank=True)
    last_name = serializers.CharField(required=False, max_length=150, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    password = serializers.CharField(required=True, max_length=128, style={'input_type': 'password'}, write_only=True)
    password_repeat = serializers.CharField(required=True, max_length=128, style={'input_type': 'password'},
                                            write_only=True)

    def validate_username(self, username):
        """Validate username existence"""
        if self.Meta.model.objects.filter(username=username).exists():
            raise serializers.ValidationError(f'User "{username}" already exists')
        else:
            return username

    @staticmethod
    def validate_password(password):
        """Standard django password validator"""
        validate_password(password)
        return password

    def validate(self, data):
        """Check password and password_repeat"""
        if data.get('password') == self.initial_data.get('password_repeat'):
            return data
        raise serializers.ValidationError({'password_repeat': ['Passwords does not match'],
                                           'password': ['Passwords does not match']})

    def create(self, validated_data):
        """Create user and write it into database"""
        del validated_data['password_repeat']
        validated_data['password'] = make_password(validated_data['password'])
        response = super().create(validated_data)
        return response
        # user = self.Meta.model.objects.create(**validated_data)
        # user.set_password(user.password)
        # user.save()
        # return user

    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email', 'password', 'password_repeat']


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email']


class LoginSerializer(serializers.ModelSerializer):
    username = serializers.CharField(required=True, min_length=1)
    password = serializers.CharField(required=True, min_length=1)

    def validate_username(self, username):
        """Validate username existence"""
        user = self.Meta.model.objects.filter(username=username)
        if not user.exists():
            raise serializers.ValidationError(f'User "{username}" does not exist')
        else:
            return username

    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email', 'password']
        read_only_fields = ['id', 'first_name', 'last_name', 'email']


class RetrieveUpdateSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False, read_only=True)
    username = serializers.RegexField(regex='^[\w.@+-]+$', required=False, max_length=150, min_length=1,
                                      allow_null=False, allow_blank=False)
    first_name = serializers.CharField(required=False, max_length=150, allow_blank=True)
    last_name = serializers.CharField(required=False, max_length=150, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)

    def validate_username(self, username):
        request = self.context.get('request', None)
        if request:
            current_user = request.user
        else:
            raise serializers.ValidationError({'username': ['Login error']})

        """Validate username existence"""
        if self.Meta.model.objects.filter(username=username).exists() and current_user.username != username:
            raise serializers.ValidationError(f'User "{username}" already exists')
        else:
            return username

    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email']


class PasswordUpdateSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Incorrect password")
        return value

    def validate_new_password(self, value):
        validate_password(value)
        return value

    def validate(self, data):
        if data['old_password'] == data['new_password']:
            raise serializers.ValidationError({'old_password': ['Passwords can not match'],
                                               'new_password': ['Passwords can not match']})
        return data

    def save(self, **kwargs):
        password = self.validated_data['new_password']
        user = self.context['request'].user
        user.set_password(password)
        user.save()
        return user

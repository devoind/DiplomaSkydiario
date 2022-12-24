from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.generics import CreateAPIView, RetrieveUpdateDestroyAPIView, UpdateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import User
from .serializers import SignUpSerializer, LoginSerializer, RetrieveUpdateSerializer, PasswordUpdateSerializer


# ping view
@api_view(http_method_names=['GET'])
def ping(request):
    return Response(status=status.HTTP_200_OK, data={'status': 'alive'})


class SignUpView(CreateAPIView):
    serializer_class = SignUpSerializer


class LoginView(CreateAPIView):
    serializer_class = LoginSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        if not serializer.is_valid():
            return Response(status=status.HTTP_400_BAD_REQUEST, data=serializer.errors)

        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return Response(status=status.HTTP_201_CREATED, data={'username': user.username,
                                                                  'first_name': user.first_name,
                                                                  'last_name': user.last_name,
                                                                  'email': user.email,
                                                                  'status': 'success'})
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'password': ['Incorrect password']})


class RetrieveUpdateView(RetrieveUpdateDestroyAPIView):
    queryset = User.objects.all()
    serializer_class = RetrieveUpdateSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

    def delete(self, request, *args, **kwargs):
        logout(request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class PasswordUpdateView(UpdateAPIView):
    serializer_class = PasswordUpdateSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self, queryset=None):
        return self.request.user

    def update(self, request, *args, **kwargs):

        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(status=status.HTTP_200_OK, data={'status': 'success'})
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST, data=serializer.errors)

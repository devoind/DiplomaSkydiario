from django.urls import path

from .views import SignUpView, LoginView, RetrieveUpdateView, PasswordUpdateView

urlpatterns = [
    path('signup', SignUpView.as_view(), name='signup'),
    path('login', LoginView.as_view(), name='login'),
    path('profile', RetrieveUpdateView.as_view(), name='profile'),
    path('update_password', PasswordUpdateView.as_view(), name='update_password')
]

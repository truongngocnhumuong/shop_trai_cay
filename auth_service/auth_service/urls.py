from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView
from users.views import (
    UserRegistrationView,
    UserLoginView,
    TokenVerifyView,
    # Web views
    HomeView,
    LoginPageView,
    RegisterPageView,
    DashboardView,
    WebLoginView,
    WebRegisterView,
    LogoutView
)

urlpatterns = [
    # Web UI
    path('', HomeView.as_view(), name='home'),
    path('login-page/', LoginPageView.as_view(), name='login_page'),
    path('register-page/', RegisterPageView.as_view(), name='register_page'),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('web-login/', WebLoginView.as_view(), name='web_login'),
    path('web-register/', WebRegisterView.as_view(), name='web_register'),
    path('logout/', LogoutView.as_view(), name='logout'),

    # API Endpoints
    path('admin/', admin.site.urls),
    path('api/register/', UserRegistrationView.as_view(), name='register'),
    path('api/login/', UserLoginView.as_view(), name='login'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/verify-token/', TokenVerifyView.as_view(), name='token_verify'),
]

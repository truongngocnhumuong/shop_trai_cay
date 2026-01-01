from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenVerifyView as SimpleJWTTokenVerifyView
from rest_framework_simplejwt.tokens import RefreshToken
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View

from .serializers import (
    CustomTokenObtainPairSerializer,
    UserSerializer
)
from django.contrib.auth import get_user_model
User = get_user_model()


class UserRegistrationView(APIView):
    """
    Register a new user
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            
            # Generate tokens
            refresh = RefreshToken.for_user(user)
            
            return Response({
                'user': UserSerializer(user).data,
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserLoginView(APIView):
    """
    Login user and return JWT tokens
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = CustomTokenObtainPairSerializer(data=request.data)
        if serializer.is_valid():
            return Response(serializer.validated_data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class TokenVerifyView(SimpleJWTTokenVerifyView):
    """
    Verify the token and return the user data if valid
    """
    def post(self, request, *args, **kwargs):
        # First verify the token using the parent class
        response = super().post(request, *args, **kwargs)
        
        # If token is valid, add user data to the response
        if response.status_code == status.HTTP_200_OK:
            # Get the user from the token
            token = request.data.get('token')
            from rest_framework_simplejwt.tokens import AccessToken
            access_token = AccessToken(token)
            user_id = access_token['user_id']
            
            # Get user data
            from django.contrib.auth import get_user_model
            User = get_user_model()
            try:
                user = User.objects.get(id=user_id)
                user_data = UserSerializer(user).data
                response.data['user'] = user_data
            except User.DoesNotExist:
                pass
                
        return response

# --- Web Interface Views ---

class HomeView(View):
    def get(self, request):
        return render(request, 'home.html')

class LoginPageView(View):
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('dashboard')
        return render(request, 'login.html')

class RegisterPageView(View):
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('dashboard')
        return render(request, 'register.html')

class DashboardView(View):
    @method_decorator(login_required(login_url='login_page'))
    def get(self, request):
        return render(request, 'dashboard.html')

class WebLoginView(View):
    def post(self, request):
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f"Chào mừng trở lại, {username}!")
            return redirect('dashboard')
        else:
            messages.error(request, "Sai tên đăng nhập hoặc mật khẩu.")
            return redirect('login_page')

class WebRegisterView(View):
    def post(self, request):
        username = request.POST.get('username')
        email = request.POST.get('email')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')
        
        if password != password2:
            messages.error(request, "Mật khẩu xác nhận không khớp.")
            return redirect('register_page')
            
        data = {
            'username': username,
            'email': email,
            'first_name': first_name,
            'last_name': last_name,
            'password': password,
            'password2': password2,
            'role': 'customer'  # Default role for web registrations
        }
        
        serializer = UserRegistrationSerializer(data=data)
        if serializer.is_valid():
            user = serializer.save()
            login(request, user)
            messages.success(request, "Đăng ký tài khoản thành công!")
            return redirect('dashboard')
        else:
            # Extract first error message
            error_msg = "Lỗi đăng ký: "
            for field, errors in serializer.errors.items():
                error_msg += f"{field}: {errors[0]} "
                break # Only show first error for simplicity
            messages.error(request, error_msg)
            return redirect('register_page')

class LogoutView(View):
    def get(self, request):
        logout(request)
        messages.info(request, "Bạn đã đăng xuất.")
        return redirect('home')

class UserDetailView(APIView):
    """
    Get user details by ID
    """
    permission_classes = [permissions.AllowAny] # In production, restrict this
    
    def get(self, request, pk):
        try:
            user = User.objects.get(pk=pk)
            serializer = UserSerializer(user)
            return Response(serializer.data)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

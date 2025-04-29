from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from django.contrib.auth.forms import SetPasswordForm
from django.conf import settings

app_name = 'accounts'

urlpatterns = [
    # Authentication URLs
    path('signup/', views.signup, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile, name='profile'),
    path('consultant-profile/', views.consultant_profile, name='consultant_profile'),
    path('change-password/', views.change_password, name='change_password'),
    path('profile/delete/', views.delete_account, name='delete_account'),
    
    # Password Reset URLs
    path('password-reset/', views.forgot_password, name='password_reset'),
    path('password-reset/status/', views.password_reset_status, name='password_reset_status'),
    path('reset/<uidb64>/<token>/', views.reset_password_confirm, name='password_reset_confirm'),
    
    # Consultant URLs
    path('consultant/dashboard/', views.consultant_dashboard, name='consultant_dashboard'),
    path('consultant/consultation/<int:consultation_id>/', views.consultant_consultation_detail, name='consultant_consultation_detail'),
    
    # Admin URLs
    path('admin/login/', views.admin_login, name='admin_login'),
    path('admin/signup/', views.admin_signup, name='admin_signup'),
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/profile/', views.admin_profile, name='admin_profile'),
    path('admin/manage-clients/', views.manage_clients, name='manage_clients'),
    path('admin/manage-consultants/', views.manage_consultants, name='manage_consultants'),
    path('admin/client/<int:client_id>/', views.client_detail, name='client_detail'),
    path('admin/consultant/<int:consultant_id>/', views.consultant_detail, name='consultant_detail'),
    path('admin/activate-user/<int:user_id>/', views.activate_user, name='activate_user'),
    path('admin/deactivate-user/<int:user_id>/', views.deactivate_user, name='deactivate_user'),
    path('admin/approve-user/<int:user_id>/', views.approve_user, name='approve_user'),
    path('admin/reject-user/<int:user_id>/', views.reject_user, name='reject_user'),
    path('admin/assign-consultant/<int:consultation_id>/', views.assign_consultant, name='assign_consultant'),
    
    # Test Email URL
    path('test-email/', views.test_email, name='test_email'),
] 
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.contrib.auth import login, authenticate, update_session_auth_hash, logout
from django.contrib.auth.forms import PasswordChangeForm, AuthenticationForm, UserCreationForm
from .forms import SignUpForm, UserProfileUpdateForm, UserUpdateForm, UserProfileForm, ConsultantForm, ConsultantProfileForm, ConsultantUpdateForm, CustomAuthenticationForm
from core.models import Consultation, Document
from .models import UserProfile, Consultant
from django.contrib.auth.models import User
from django.contrib.auth.backends import ModelBackend
from django.db.models import Q
from django.core.mail import send_mail
from django.conf import settings
from django.utils.crypto import get_random_string
from django.urls import reverse
import uuid
from django.template.loader import render_to_string
from django.utils.html import strip_tags
import logging
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.encoding import force_str, force_bytes
from datetime import timedelta

logger = logging.getLogger(__name__)

def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            
            try:
                # Send welcome email
                subject = 'Welcome to Costsecon Accounting Inc'
                html_message = render_to_string('emails/welcome_email.html', {
                    'name': user.first_name,
                    'user_type': user.userprofile.user_type,
                })
                plain_message = strip_tags(html_message)
                
                send_mail(
                    subject,
                    plain_message,
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    html_message=html_message,
                    fail_silently=False
                )
                
                messages.success(request, 'Your account has been created successfully! Please check your email for a welcome message.')
                return redirect('accounts:login')
                
            except Exception as e:
                logger.error(f"Failed to send welcome email: {str(e)}")
                messages.warning(request, 'Your account was created, but we could not send a welcome email. Please contact support if you need assistance.')
                return redirect('accounts:login')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = SignUpForm()
    
    return render(request, 'accounts/signup.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            
            try:
                # Use our custom EmailBackend for authentication
                user = authenticate(request, username=email, password=password)
                
                if user is not None:
                    # Check if user is approved
                    if user.userprofile.user_type in ['admin', 'consultant'] and not user.userprofile.is_approved:
                        messages.error(request, 'Your account is pending approval. Please wait for admin approval.')
                        return redirect('accounts:login')
                    
                    login(request, user)
                    # Redirect based on user type
                    if user.userprofile.user_type == 'consultant':
                        return redirect('accounts:consultant_dashboard')
                    elif user.userprofile.user_type == 'admin':
                        return redirect('accounts:admin_dashboard')
                    else:
                        return redirect('core:home')
                else:
                    messages.error(request, 'Invalid email or password.')
            except Exception as e:
                logger.error(f"Login error: {str(e)}")
                messages.error(request, 'An error occurred during login. Please try again.')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = CustomAuthenticationForm()
        
    return render(request, 'accounts/login.html', {'form': form})

@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Your password was successfully updated!')
            return redirect('accounts:profile')
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'accounts/change_password.html', {'form': form})

@login_required
def profile(request):
    user = request.user
    profile = user.userprofile
    
    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=user)
        profile_form = UserProfileForm(request.POST, request.FILES, instance=profile)
        
        # Initialize consultant_form
        consultant_form = None
        if profile.user_type == 'consultant':
            consultant_form = ConsultantUpdateForm(request.POST, instance=profile.consultant)
            forms_valid = user_form.is_valid() and profile_form.is_valid() and consultant_form.is_valid()
        else:
            forms_valid = user_form.is_valid() and profile_form.is_valid()
        
        if forms_valid:
            try:
                # Save user form
                user_form.save()
                
                # Handle profile picture upload
                if 'profile_picture' in request.FILES:
                    try:
                        # Delete old profile picture from Cloudinary if it exists
                        if profile.profile_picture:
                            import cloudinary
                            try:
                                # Get the public_id from the URL
                                public_id = profile.profile_picture.public_id
                                if public_id:
                                    cloudinary.uploader.destroy(public_id)
                            except Exception as e:
                                logger.warning(f"Error deleting old profile picture: {e}")
                        
                        # Save new profile picture
                        profile.profile_picture = request.FILES['profile_picture']
                    except Exception as e:
                        logger.error(f"Error handling profile picture: {e}")
                        messages.warning(request, 'Error updating profile picture, but other changes were saved.')
                
                # Save profile
                profile.save()
                
                # Save consultant form if applicable
                if profile.user_type == 'consultant' and consultant_form:
                    consultant_form.save()
                
                messages.success(request, 'Your profile was successfully updated!')
                return redirect('accounts:profile')
            except Exception as e:
                logger.error(f"Error updating profile: {e}")
                messages.error(request, f'Error updating profile: {str(e)}')
        else:
            for field, errors in profile_form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        user_form = UserUpdateForm(instance=user)
        profile_form = UserProfileForm(instance=profile)
        consultant_form = ConsultantUpdateForm(instance=profile.consultant) if profile.user_type == 'consultant' else None
    
    # Get consultations for the user
    active_consultations = Consultation.objects.filter(
        user=user,
        status__in=['pending', 'confirmed', 'in_progress']
    ).order_by('-created_at')
    
    completed_consultations = Consultation.objects.filter(
        user=user,
        status='completed'
    ).order_by('-updated_at')
    
    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'consultant_form': consultant_form,
        'active_consultations': active_consultations,
        'completed_consultations': completed_consultations,
    }
    return render(request, 'accounts/profile.html', context)

@login_required
def update_profile(request):
    user = request.user
    profile = user.userprofile
    
    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=user)
        profile_form = UserProfileForm(request.POST, request.FILES, instance=profile)
        
        if profile.user_type == 'consultant':
            consultant_form = ConsultantUpdateForm(request.POST, instance=profile.consultant)
            forms_valid = user_form.is_valid() and profile_form.is_valid() and consultant_form.is_valid()
        else:
            forms_valid = user_form.is_valid() and profile_form.is_valid()
        
        if forms_valid:
            user_form.save()
            profile_form.save()
            
            if profile.user_type == 'consultant':
                consultant_form.save()
            
            messages.success(request, 'Your profile was successfully updated!')
            return redirect('accounts:profile')
    else:
        user_form = UserUpdateForm(instance=user)
        profile_form = UserProfileForm(instance=profile)
        consultant_form = ConsultantUpdateForm(instance=profile.consultant) if profile.user_type == 'consultant' else None
    
    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'consultant_form': consultant_form
    }
    return render(request, 'accounts/profile.html', context)

@login_required
def delete_account(request):
    if request.method == 'POST':
        password = request.POST.get('password')
        user = request.user
        
        # Verify password
        if authenticate(username=user.username, password=password):
            # Delete user profile first
            try:
                user.userprofile.delete()
            except UserProfile.DoesNotExist:
                pass
            
            # Delete user
            user.delete()
            
            # Logout user
            logout(request)
            
            messages.success(request, 'Your account has been successfully deleted.')
            return redirect('core:home')
        else:
            messages.error(request, 'Incorrect password. Please try again.')
    
    return redirect('accounts:profile')

def logout_view(request):
    logout(request)
    return redirect('core:home')

def is_consultant(user):
    try:
        return user.userprofile.user_type == 'consultant'
    except:
        return False

def is_admin(user):
    try:
        return user.userprofile.user_type == 'admin'
    except:
        return False

def is_client(user):
    try:
        return user.userprofile.user_type == 'client'
    except:
        return False

@login_required
@user_passes_test(is_consultant)
def consultant_dashboard(request):
    consultant = get_object_or_404(Consultant, user_profile__user=request.user)
    assigned_consultations = Consultation.objects.filter(consultant=consultant).order_by('-date', '-time')
    
    # Get consultations by status
    pending_consultations = assigned_consultations.filter(status='pending')
    in_progress_consultations = assigned_consultations.filter(status='in_progress')
    completed_consultations = assigned_consultations.filter(status='completed')
    
    context = {
        'consultant': consultant,
        'pending_consultations': pending_consultations,
        'in_progress_consultations': in_progress_consultations,
        'completed_consultations': completed_consultations,
        'total_consultations': assigned_consultations.count(),
    }
    return render(request, 'accounts/consultant_dashboard.html', context)

@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    if not request.user.is_superuser:
        return redirect('core:home')
    
    # Get statistics
    total_clients = User.objects.filter(userprofile__user_type='client').count()
    total_consultants = User.objects.filter(userprofile__user_type='consultant').count()
    pending_approvals = UserProfile.objects.filter(
        user_type__in=['admin', 'consultant'],
        is_approved=False
    ).count()
    
    # Get recent activities
    recent_consultations = Consultation.objects.all().order_by('-created_at')[:5]
    recent_users = User.objects.all().order_by('-date_joined')[:5]
    
    context = {
        'total_clients': total_clients,
        'total_consultants': total_consultants,
        'pending_approvals': pending_approvals,
        'recent_consultations': recent_consultations,
        'recent_users': recent_users,
    }
    return render(request, 'accounts/admin/dashboard.html', context)

@login_required
@user_passes_test(is_consultant)
def consultant_consultation_detail(request, consultation_id):
    consultant = get_object_or_404(Consultant, user_profile__user=request.user)
    consultation = get_object_or_404(Consultation, id=consultation_id, consultant=consultant)
    
    if request.method == 'POST':
        if 'update_status' in request.POST:
            new_status = request.POST.get('status')
            if new_status in dict(Consultation.STATUS_CHOICES):
                consultation.status = new_status
                consultation.save()
                messages.success(request, 'Consultation status updated successfully!')
            else:
                messages.error(request, 'Invalid status selected.')
            return redirect('accounts:consultant_consultation_detail', consultation_id=consultation.id)
    
    context = {
        'consultation': consultation,
        'documents': consultation.documents.all(),
    }
    return render(request, 'accounts/consultant_consultation_detail.html', context)

@login_required
@user_passes_test(is_admin)
def manage_consultants(request):
    consultants = User.objects.filter(userprofile__user_type='consultant').select_related('userprofile')
    return render(request, 'accounts/admin/manage_consultants.html', {'consultants': consultants})

@login_required
@user_passes_test(is_admin)
def edit_consultant(request, consultant_id):
    consultant = get_object_or_404(Consultant, id=consultant_id)
    
    if request.method == 'POST':
        form = ConsultantForm(request.POST, instance=consultant)
        if form.is_valid():
            form.save()
            messages.success(request, 'Consultant updated successfully!')
            return redirect('accounts:manage_consultants')
    else:
        form = ConsultantForm(instance=consultant)
    
    context = {
        'form': form,
        'consultant': consultant,
    }
    return render(request, 'accounts/edit_consultant.html', context)

def consultant_profile(request):
    if not request.user.userprofile.is_consultant:
        return redirect('core:home')
    
    if request.method == 'POST':
        form = ConsultantProfileForm(request.POST, instance=request.user.userprofile.consultant)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your consultant profile has been updated successfully.')
            return redirect('core:consultant_dashboard')
    else:
        form = ConsultantProfileForm(instance=request.user.userprofile.consultant)
    
    return render(request, 'accounts/consultant_profile.html', {'form': form})

def user_profile(request):
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=request.user.userprofile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated successfully.')
            return redirect('core:profile')
    else:
        form = UserProfileForm(instance=request.user.userprofile)
    
    return render(request, 'accounts/user_profile.html', {'form': form})

def password_reset_status(request):
    is_complete = request.GET.get('complete', False)
    email = request.GET.get('email', '')
    
    return render(request, 'accounts/password_reset_status.html', {
        'is_complete': is_complete,
        'email': email
    })

def forgot_password(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email)
            # Generate a unique token
            token = str(uuid.uuid4())
            # Store token in user's profile
            user.userprofile.reset_token = token
            user.userprofile.reset_token_created = timezone.now()
            user.userprofile.save()
            
            # Create reset link
            reset_link = request.build_absolute_uri(
                reverse('accounts:reset_password_confirm', kwargs={
                    'uidb64': urlsafe_base64_encode(force_bytes(user.pk)),
                    'token': token
                })
            )
            
            # Send email
            subject = 'Password Reset Request - Costsecon Accounting Inc'
            html_message = render_to_string('emails/password_reset_email.html', {
                'name': user.first_name,
                'reset_link': reset_link,
                'expiry_hours': settings.PASSWORD_RESET_TIMEOUT // 3600,
            })
            plain_message = strip_tags(html_message)
            
            send_mail(
                subject,
                plain_message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                html_message=html_message,
                fail_silently=False
            )
            
            messages.success(request, 'Password reset instructions have been sent to your email.')
            return redirect('accounts:login')
            
        except User.DoesNotExist:
            messages.error(request, 'No account found with this email address.')
        except Exception as e:
            logger.error(f"Failed to send password reset email: {str(e)}")
            messages.error(request, 'There was an error processing your request. Please try again later.')
    
    return render(request, 'accounts/forgot_password.html')

def reset_password_confirm(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
        
        # Check if token is valid and not expired
        if (user.userprofile.reset_token == token and 
            user.userprofile.reset_token_created and 
            timezone.now() - user.userprofile.reset_token_created < timedelta(seconds=settings.PASSWORD_RESET_TIMEOUT)):
            
            if request.method == 'POST':
                form = SetPasswordForm(user, request.POST)
                if form.is_valid():
                    form.save()
                    # Clear reset token
                    user.userprofile.reset_token = None
                    user.userprofile.reset_token_created = None
                    user.userprofile.save()
                    
                    # Send confirmation email
                    subject = 'Password Reset Successful - Costsecon Accounting Inc'
                    html_message = render_to_string('emails/password_reset_complete.html', {
                        'name': user.first_name,
                    })
                    plain_message = strip_tags(html_message)
                    
                    send_mail(
                        subject,
                        plain_message,
                        settings.DEFAULT_FROM_EMAIL,
                        [user.email],
                        html_message=html_message,
                        fail_silently=False
                    )
                    
                    messages.success(request, 'Your password has been reset successfully. You can now login with your new password.')
                    return redirect('accounts:login')
            else:
                form = SetPasswordForm(user)
            
            return render(request, 'accounts/reset_password.html', {'form': form})
        
        messages.error(request, 'The password reset link is invalid or has expired.')
        return redirect('accounts:forgot_password')
        
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        messages.error(request, 'The password reset link is invalid.')
        return redirect('accounts:forgot_password')
    except Exception as e:
        logger.error(f"Error during password reset: {str(e)}")
        messages.error(request, 'There was an error processing your request. Please try again later.')
        return redirect('accounts:forgot_password')

@login_required
@user_passes_test(is_admin)
def manage_users(request):
    users = User.objects.all().select_related('userprofile')
    context = {
        'users': users,
    }
    return render(request, 'accounts/manage_users.html', context)

@login_required
@user_passes_test(is_admin)
def edit_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    profile = user.userprofile
    
    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=user)
        profile_form = UserProfileForm(request.POST, request.FILES, instance=profile)
        
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'User updated successfully!')
            return redirect('accounts:manage_users')
    else:
        user_form = UserUpdateForm(instance=user)
        profile_form = UserProfileForm(instance=profile)
    
    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'user': user,
    }
    return render(request, 'accounts/edit_user.html', context)

@login_required
@user_passes_test(is_admin)
def delete_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        user.delete()
        messages.success(request, 'User deleted successfully!')
        return redirect('accounts:manage_users')
    
    return render(request, 'accounts/delete_user.html', {'user': user})

@login_required
@user_passes_test(is_admin)
def delete_consultant(request, consultant_id):
    consultant = get_object_or_404(Consultant, id=consultant_id)
    
    if request.method == 'POST':
        consultant.delete()
        messages.success(request, 'Consultant deleted successfully!')
        return redirect('accounts:manage_consultants')
    
    return render(request, 'accounts/delete_consultant.html', {'consultant': consultant})

def test_email(request):
    if request.method == 'POST':
        try:
            email = request.POST.get('email')
            subject = 'Test Email - Costsecon Accounting Inc'
            html_message = render_to_string('emails/test_email.html', {
                'site_name': settings.SITE_NAME,
                'current_time': timezone.now(),
            })
            plain_message = strip_tags(html_message)
            
            send_mail(
                subject,
                plain_message,
                settings.DEFAULT_FROM_EMAIL,
                [email],
                html_message=html_message,
                fail_silently=False,
            )
            messages.success(request, 'Test email sent successfully!')
        except Exception as e:
            logger.error(f"Error sending test email: {e}")
            messages.error(request, f'Error sending email: {str(e)}')
    return render(request, 'accounts/test_email.html')

@login_required
@user_passes_test(is_admin)
def approve_user(request, user_id):
    if request.method == 'POST':
        user_profile = get_object_or_404(UserProfile, user_id=user_id)
        user_profile.is_approved = True
        user_profile.save()
        
        # Send email notification
        subject = 'Account Approved - Costsecon Accounting Inc'
        html_message = render_to_string('emails/account_approved.html', {
            'name': user_profile.user.get_full_name(),
            'user_type': user_profile.user_type,
        })
        plain_message = strip_tags(html_message)
        
        send_mail(
            subject,
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            [user_profile.user.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        messages.success(request, f'User {user_profile.user.get_full_name()} has been approved.')
    return redirect('accounts:admin_dashboard')

@login_required
@user_passes_test(is_admin)
def reject_user(request, user_id):
    if request.method == 'POST':
        user_profile = get_object_or_404(UserProfile, user_id=user_id)
        user = user_profile.user
        
        # Send email notification
        send_mail(
            'Account Rejected',
            'Your account registration has been rejected. Please contact support for more information.',
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )
        
        # Delete the user
        user.delete()
        messages.success(request, f'User {user.get_full_name()} has been rejected and removed.')
    return redirect('accounts:admin_dashboard')

@login_required
@user_passes_test(is_admin)
def assign_consultant(request, consultation_id):
    if request.method == 'POST':
        consultation = get_object_or_404(Consultation, id=consultation_id)
        consultant_id = request.POST.get('consultant_id')
        
        if consultant_id:
            consultant = get_object_or_404(Consultant, id=consultant_id)
            consultation.consultant = consultant
            consultation.status = 'assigned'
            consultation.save()
            
            # Send email notification to consultant
            send_mail(
                'New Consultation Assigned',
                f'You have been assigned to a new consultation. Please check your dashboard for details.',
                settings.DEFAULT_FROM_EMAIL,
                [consultant.user_profile.user.email],
                fail_silently=False,
            )
            
            messages.success(request, 'Consultant assigned successfully.')
        else:
            messages.error(request, 'Please select a consultant.')
    
    return redirect('accounts:admin_dashboard')

@login_required
@user_passes_test(is_admin)
def manage_clients(request):
    clients = User.objects.filter(userprofile__user_type='client').select_related('userprofile')
    return render(request, 'accounts/admin/manage_clients.html', {'clients': clients})

@login_required
@user_passes_test(is_admin)
def client_detail(request, client_id):
    client = get_object_or_404(User, id=client_id, userprofile__user_type='client')
    consultations = Consultation.objects.filter(user=client)
    return render(request, 'accounts/admin/client_detail.html', {
        'client': client,
        'consultations': consultations
    })

@login_required
@user_passes_test(is_admin)
def consultant_detail(request, consultant_id):
    consultant = get_object_or_404(User, id=consultant_id, userprofile__user_type='consultant')
    consultations = Consultation.objects.filter(consultant=consultant.userprofile.consultant)
    return render(request, 'accounts/admin/consultant_detail.html', {
        'consultant': consultant,
        'consultations': consultations
    })

@login_required
@user_passes_test(is_admin)
def deactivate_user(request, user_id):
    if request.method == 'POST':
        user = get_object_or_404(User, id=user_id)
        user.is_active = False
        user.save()
        
        messages.success(request, f'User {user.get_full_name()} has been deactivated.')
    return redirect('accounts:admin_dashboard')

@login_required
@user_passes_test(is_admin)
def activate_user(request, user_id):
    if request.method == 'POST':
        user = get_object_or_404(User, id=user_id)
        user.is_active = True
        user.save()
        
        messages.success(request, f'User {user.get_full_name()} has been activated.')
    return redirect('accounts:admin_dashboard')

def admin_login(request):
    if request.user.is_authenticated and request.user.is_superuser:
        return redirect('accounts:admin_dashboard')
    
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            
            if user is not None and user.is_superuser:
                login(request, user)
                return redirect('accounts:admin_dashboard')
            else:
                messages.error(request, 'Invalid username or password.')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = AuthenticationForm()
    
    return render(request, 'accounts/admin/login.html', {'form': form})

def admin_signup(request):
    if request.user.is_authenticated and request.user.is_superuser:
        return redirect('accounts:admin_dashboard')
    
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_superuser = True
            user.is_staff = True
            user.save()
            
            # Create user profile
            UserProfile.objects.create(
                user=user,
                user_type='admin',
                phone_number=request.POST.get('phone_number'),
                profile_picture=request.FILES.get('profile_picture')
            )
            
            messages.success(request, 'Admin account created successfully!')
            return redirect('accounts:admin_login')
    else:
        form = UserCreationForm()
    
    return render(request, 'accounts/admin/signup.html', {'form': form})

@login_required
def admin_profile(request):
    if not request.user.is_superuser:
        return redirect('core:home')
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=request.user.userprofile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('accounts:admin_profile')
    else:
        form = UserProfileForm(instance=request.user.userprofile)
    
    context = {
        'form': form,
        'total_clients': User.objects.filter(userprofile__user_type='client').count(),
        'total_consultants': User.objects.filter(userprofile__user_type='consultant').count(),
    }
    return render(request, 'accounts/admin/profile.html', context)

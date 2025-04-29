from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from .models import UserProfile, Consultant
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from PIL import Image

class SignUpForm(UserCreationForm):
    username = forms.CharField(max_length=30, required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    email = forms.EmailField(max_length=254, required=True)
    phone_number = forms.CharField(max_length=15, required=True)
    address = forms.CharField(widget=forms.Textarea, required=True)
    profile_picture = forms.ImageField(required=True)
    user_type = forms.ChoiceField(
        choices=UserProfile.USER_TYPE_CHOICES,
        widget=forms.RadioSelect,
        required=True
    )
    company_name = forms.CharField(max_length=100, required=False)
    specialization = forms.CharField(max_length=100, required=False)
    experience_years = forms.IntegerField(required=False, min_value=0)
    bio = forms.CharField(widget=forms.Textarea, required=False)
    hourly_rate = forms.DecimalField(max_digits=10, decimal_places=2, required=False, min_value=0)
    languages = forms.CharField(max_length=200, required=False)
    certifications = forms.CharField(widget=forms.Textarea, required=False)
    education = forms.CharField(widget=forms.Textarea, required=False)

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'phone_number', 'address', 
                 'profile_picture', 'user_type', 'company_name', 'specialization', 
                 'experience_years', 'bio', 'hourly_rate', 'languages', 
                 'certifications', 'education', 'password1', 'password2')

    def clean(self):
        cleaned_data = super().clean()
        user_type = cleaned_data.get('user_type')
        
        if user_type == 'consultant':
            required_fields = ['specialization', 'experience_years', 'bio', 'hourly_rate']
            for field in required_fields:
                if not cleaned_data.get(field):
                    raise ValidationError(f"{field.replace('_', ' ').title()} is required for consultants.")
        
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data['username']
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        
        if commit:
            user.save()
            # Create or update user profile
            profile, created = UserProfile.objects.get_or_create(user=user)
            profile.phone_number = self.cleaned_data['phone_number']
            profile.address = self.cleaned_data['address']
            profile.user_type = self.cleaned_data['user_type']
            profile.company_name = self.cleaned_data['company_name']
            
            # Handle profile picture
            if 'profile_picture' in self.cleaned_data and self.cleaned_data['profile_picture']:
                profile.profile_picture = self.cleaned_data['profile_picture']
            
            # Only set bio if it exists
            if self.cleaned_data.get('bio'):
                profile.bio = self.cleaned_data['bio']
            profile.save()
            
            # Create consultant profile if user is a consultant
            if profile.user_type == 'consultant':
                consultant, created = Consultant.objects.get_or_create(user_profile=profile)
                consultant.specialization = self.cleaned_data['specialization']
                consultant.experience_years = self.cleaned_data['experience_years']
                consultant.bio = self.cleaned_data['bio']
                consultant.hourly_rate = self.cleaned_data['hourly_rate']
                consultant.languages = self.cleaned_data['languages']
                consultant.certifications = self.cleaned_data['certifications']
                consultant.education = self.cleaned_data['education']
                consultant.save()
        
        return user

class ConsultantProfileForm(forms.ModelForm):
    class Meta:
        model = Consultant
        fields = ['specialization', 'experience_years', 'bio']
        widgets = {
            'specialization': forms.TextInput(attrs={'class': 'form-control'}),
            'experience_years': forms.NumberInput(attrs={'class': 'form-control'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }

class CustomAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'})
    )

    error_messages = {
        'invalid_login': 'Please enter a correct email and password.',
        'inactive': 'This account is inactive.',
    }

class UserUpdateForm(forms.ModelForm):
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control'}))
    first_name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email')

class UserProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ('user_type', 'phone_number', 'address', 'company_name', 'profile_picture')
        widgets = {
            'address': forms.Textarea(attrs={'rows': 4}),
            'profile_picture': forms.FileInput(attrs={
                'accept': 'image/*',
                'class': 'form-control',
                'data-max-size': '5242880'  # 5MB in bytes
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make all fields optional in profile update
        for field in self.fields:
            self.fields[field].required = False
        
        # Set initial values if they exist
        if self.instance:
            self.fields['phone_number'].initial = self.instance.phone_number
            self.fields['address'].initial = self.instance.address
            self.fields['company_name'].initial = self.instance.company_name

    def clean_profile_picture(self):
        profile_picture = self.cleaned_data.get('profile_picture')
        if profile_picture:
            # Check file size
            if profile_picture.size > 5 * 1024 * 1024:  # 5MB limit
                raise forms.ValidationError('Image file too large. Maximum size is 5MB.')
            
            # Check file type
            allowed_types = ['image/jpeg', 'image/png', 'image/gif']
            if profile_picture.content_type not in allowed_types:
                raise forms.ValidationError('Unsupported file type. Please upload JPEG, PNG or GIF images only.')
            
            # Check image dimensions
            try:
                img = Image.open(profile_picture)
                if img.height > 2000 or img.width > 2000:
                    raise forms.ValidationError('Image dimensions too large. Maximum size is 2000x2000 pixels.')
            except Exception as e:
                raise forms.ValidationError('Invalid image file. Please upload a valid image.')
            
        return profile_picture

class ConsultantForm(forms.ModelForm):
    email = forms.EmailField(
        label='Email',
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    name = forms.CharField(
        label='Full Name',
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    phone_number = forms.CharField(
        label='Phone Number',
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    specialization = forms.CharField(
        label='Specialization',
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    experience_years = forms.IntegerField(
        label='Years of Experience',
        required=True,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    hourly_rate = forms.DecimalField(
        label='Hourly Rate',
        required=True,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    bio = forms.CharField(
        label='Bio',
        required=True,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4})
    )

    class Meta:
        model = Consultant
        fields = ('specialization', 'experience_years', 'hourly_rate', 'bio')

    def save(self, commit=True):
        consultant = super().save(commit=False)
        if commit:
            # Create or update user profile
            user, created = User.objects.get_or_create(
                email=self.cleaned_data['email'],
                defaults={
                    'username': self.cleaned_data['email'],
                    'first_name': self.cleaned_data['name'].split()[0],
                    'last_name': ' '.join(self.cleaned_data['name'].split()[1:]) if len(self.cleaned_data['name'].split()) > 1 else ''
                }
            )
            
            profile, created = UserProfile.objects.get_or_create(
                user=user,
                defaults={
                    'name': self.cleaned_data['name'],
                    'phone_number': self.cleaned_data['phone_number'],
                    'role': 'consultant'
                }
            )
            
            consultant.user_profile = profile
            consultant.save()
        return consultant 

class ConsultantUpdateForm(forms.ModelForm):
    class Meta:
        model = Consultant
        fields = [
            'specialization', 'experience_years', 'bio', 'hourly_rate',
            'languages', 'certifications', 'education'
        ]
        widgets = {
            'specialization': forms.TextInput(attrs={'class': 'form-control'}),
            'experience_years': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'bio': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'hourly_rate': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'step': 0.01}),
            'languages': forms.TextInput(attrs={'class': 'form-control'}),
            'certifications': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'education': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'})
        } 
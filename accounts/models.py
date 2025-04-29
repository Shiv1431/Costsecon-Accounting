from django.db import models
from django.contrib.auth.models import User
from cloudinary.models import CloudinaryField
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.exceptions import ObjectDoesNotExist

# Create your models here.

class UserProfile(models.Model):
    USER_TYPE_CHOICES = (
        ('client', 'Client'),
        ('consultant', 'Consultant'),
        ('admin', 'Admin'),
    )
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='userprofile')
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES, default='client')
    phone_number = models.CharField(max_length=15, null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    company_name = models.CharField(max_length=100, blank=True, null=True)
    profile_picture = CloudinaryField('profile_pictures', null=True, blank=True, folder='profile_pictures')
    reset_token = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    is_approved = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username}'s Profile"
    
    @property
    def is_consultant(self):
        return self.user_type == 'consultant'
    
    @property
    def is_client(self):
        return self.user_type == 'client'
    
    @property
    def is_admin(self):
        return self.user_type == 'admin'

    def save(self, *args, **kwargs):
        # Auto-approve client users
        if self.user_type == 'client':
            self.is_approved = True
        super().save(*args, **kwargs)

    @classmethod
    def get_or_create_profile(cls, user):
        try:
            return user.userprofile
        except ObjectDoesNotExist:
            return cls.objects.create(user=user)

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
    else:
        # Ensure profile exists for existing users
        UserProfile.get_or_create_profile(instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    try:
        instance.userprofile.save()
    except ObjectDoesNotExist:
        UserProfile.objects.create(user=instance)

class Consultant(models.Model):
    user_profile = models.OneToOneField(UserProfile, on_delete=models.CASCADE)
    specialization = models.CharField(max_length=100)
    experience_years = models.IntegerField()
    bio = models.TextField()
    is_available = models.BooleanField(default=True)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    total_consultations = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    languages = models.CharField(max_length=200, blank=True)
    certifications = models.TextField(blank=True)
    education = models.TextField(blank=True)

    def __str__(self):
        return f"{self.user_profile.user.get_full_name()} - {self.specialization}"
    
    @property
    def full_name(self):
        return self.user_profile.user.get_full_name()
    
    @property
    def email(self):
        return self.user_profile.user.email
    
    @property
    def phone_number(self):
        return self.user_profile.phone_number

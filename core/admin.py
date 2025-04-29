from django.contrib import admin
from .models import Service, Consultation, Feedback, Contact

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'duration', 'created_at')
    search_fields = ('name', 'description')
    list_filter = ('created_at',)

@admin.register(Consultation)
class ConsultationAdmin(admin.ModelAdmin):
    list_display = ('user', 'service', 'date', 'time', 'mode', 'status')
    list_filter = ('status', 'mode', 'date')
    search_fields = ('user__username', 'service__name')
    date_hierarchy = 'date'

@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('user', 'consultation', 'service_rating', 'created_at')
    list_filter = ('service_rating', 'created_at')
    search_fields = ('user__username', 'service_comment')

@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'subject', 'created_at')
    search_fields = ('name', 'email', 'subject', 'message')
    list_filter = ('created_at',)

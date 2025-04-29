from django.contrib import admin
from django.utils.html import format_html
from .models import (
    ClientBehaviorAnalysis, ServiceRecommendation, ConsultationPrediction,
    DocumentAnalysis, MarketTrendAnalysis
)

@admin.register(ClientBehaviorAnalysis)
class ClientBehaviorAnalysisAdmin(admin.ModelAdmin):
    list_display = ('user', 'predicted_next_service', 'last_analyzed')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('last_analyzed',)

    def get_readonly_fields(self, request, obj=None):
        if obj:  # editing an existing object
            return self.readonly_fields + ('user', 'service_preferences', 'interaction_patterns')
        return self.readonly_fields

@admin.register(ServiceRecommendation)
class ServiceRecommendationAdmin(admin.ModelAdmin):
    list_display = ('user', 'get_recommended_services', 'created_at')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('created_at',)

    def get_recommended_services(self, obj):
        return ", ".join([s.name for s in obj.recommended_services.all()])
    get_recommended_services.short_description = 'Recommended Services'

@admin.register(ConsultationPrediction)
class ConsultationPredictionAdmin(admin.ModelAdmin):
    list_display = ('consultation', 'predicted_duration', 'predicted_complexity', 'predicted_success_rate', 'created_at')
    search_fields = ('consultation__user__username', 'consultation__service__name')
    readonly_fields = ('created_at',)

    def get_readonly_fields(self, request, obj=None):
        if obj:  # editing an existing object
            return self.readonly_fields + ('consultation', 'predicted_duration', 'predicted_complexity', 'predicted_success_rate')
        return self.readonly_fields

@admin.register(DocumentAnalysis)
class DocumentAnalysisAdmin(admin.ModelAdmin):
    list_display = ('user', 'document_type', 'created_at', 'view_document')
    search_fields = ('user__username', 'document_type')
    readonly_fields = ('created_at', 'extracted_text', 'analysis_results')
    list_filter = ('document_type', 'created_at')

    def view_document(self, obj):
        return format_html('<a href="{}" target="_blank">View Document</a>', obj.document.url)
    view_document.short_description = 'Document'

@admin.register(MarketTrendAnalysis)
class MarketTrendAnalysisAdmin(admin.ModelAdmin):
    list_display = ('service', 'predicted_demand', 'last_updated')
    search_fields = ('service__name',)
    readonly_fields = ('last_updated',)

    def get_readonly_fields(self, request, obj=None):
        if obj:  # editing an existing object
            return self.readonly_fields + ('service', 'trend_data', 'predicted_demand', 'seasonal_patterns')
        return self.readonly_fields

    def has_add_permission(self, request):
        return False  # Prevent manual creation of market trend analysis

from django.db import models
import json
from django.core.serializers.json import DjangoJSONEncoder
from .sample_models import Product, Customer

class UploadSession(models.Model):
    """Model to track file upload and mapping sessions"""
    file = models.FileField(upload_to='uploads/%Y/%m/%d/')
    original_filename = models.CharField(max_length=255)
    file_type = models.CharField(max_length=10, choices=[('csv', 'CSV'), ('excel', 'Excel')])
    target_model = models.CharField(max_length=100, blank=True, null=True)
    field_mappings = models.JSONField(default=dict, blank=True)
    preview_data = models.JSONField(default=list, blank=True)
    processed_data = models.JSONField(default=list, blank=True)
    validation_errors = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.original_filename} - {self.created_at}"
    
    class Meta:
        ordering = ['-created_at']

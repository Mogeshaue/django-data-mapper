from django.urls import path
from . import views, api_views

urlpatterns = [
    # Web interface URLs
    path('', views.index, name='index'),
    path('upload/', views.upload_file, name='upload_file'),
    path('session/<int:session_id>/model-selection/', views.model_selection, name='model_selection'),
    path('session/<int:session_id>/select-model/', views.select_model, name='select_model'),
    path('session/<int:session_id>/field-mapping/', views.field_mapping, name='field_mapping'),
    path('session/<int:session_id>/update-mapping/', views.update_mapping, name='update_mapping'),
    path('session/<int:session_id>/process/', views.process_file, name='process_file'),
    path('session/<int:session_id>/results/', views.results, name='results'),
    path('session/<int:session_id>/download-json/', views.download_json, name='download_json'),
    path('session/<int:session_id>/download-errors/', views.download_errors, name='download_errors'),
    
    # API URLs for dynamic model discovery and mapping
    path('api/models/', api_views.get_available_models, name='api_get_models'),
    path('api/models/<str:model_name>/schema/', api_views.get_model_schema, name='api_get_model_schema'),
    path('api/validate-mapping/', api_views.validate_mapping, name='api_validate_mapping'),
    path('api/suggest-mappings/', api_views.suggest_mappings, name='api_suggest_mappings'),
]

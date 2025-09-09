from django.urls import path
from . import views

urlpatterns = [
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
]

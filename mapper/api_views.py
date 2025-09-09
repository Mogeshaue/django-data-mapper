from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.apps import apps
from django.db import models
import json
from .utils import ModelIntrospector


@require_http_methods(["GET"])
def get_available_models(request):
    """API endpoint to get all available Django models dynamically"""
    try:
        all_models = ModelIntrospector.get_all_models()
        
        # Filter and format models for API response
        models_data = {}
        for model_name, model_class in all_models.items():
            app_label = model_class._meta.app_label
            
            # Skip system models
            if app_label not in ['admin', 'auth', 'contenttypes', 'sessions', 'messages']:
                models_data[model_name] = {
                    'name': model_name,
                    'app_label': app_label,
                    'model_name': model_class.__name__,
                    'verbose_name': model_class._meta.verbose_name,
                    'verbose_name_plural': model_class._meta.verbose_name_plural,
                    'table_name': model_class._meta.db_table,
                    'field_count': len(model_class._meta.get_fields())
                }
        
        return JsonResponse({
            'success': True,
            'models': models_data,
            'count': len(models_data)
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@require_http_methods(["GET"])
def get_model_schema(request, model_name):
    """API endpoint to get detailed schema for a specific model"""
    try:
        # Get model fields
        fields_info = ModelIntrospector.get_model_fields(model_name)
        
        if not fields_info:
            return JsonResponse({
                'success': False,
                'error': f'Model {model_name} not found'
            }, status=404)
        
        # Get model class for additional metadata
        all_models = ModelIntrospector.get_all_models()
        model_class = all_models.get(model_name)
        
        if not model_class:
            return JsonResponse({
                'success': False,
                'error': f'Model {model_name} not found'
            }, status=404)
        
        # Prepare schema response
        schema = {
            'model_name': model_name,
            'app_label': model_class._meta.app_label,
            'verbose_name': model_class._meta.verbose_name,
            'table_name': model_class._meta.db_table,
            'fields': fields_info,
            'required_fields': [name for name, info in fields_info.items() if info.get('required', False)],
            'optional_fields': [name for name, info in fields_info.items() if not info.get('required', False)]
        }
        
        return JsonResponse({
            'success': True,
            'schema': schema
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def validate_mapping(request):
    """API endpoint to validate field mappings before processing"""
    try:
        data = json.loads(request.body)
        model_name = data.get('model_name')
        field_mappings = data.get('field_mappings', {})
        sample_data = data.get('sample_data', [])
        
        if not model_name or not field_mappings:
            return JsonResponse({
                'success': False,
                'error': 'model_name and field_mappings are required'
            }, status=400)
        
        # Get model fields
        fields_info = ModelIntrospector.get_model_fields(model_name)
        if not fields_info:
            return JsonResponse({
                'success': False,
                'error': f'Model {model_name} not found'
            }, status=404)
        
        validation_results = {
            'mapping_errors': [],
            'sample_validation': [],
            'missing_required_fields': [],
            'unmapped_csv_fields': [],
            'suggestions': []
        }
        
        # Check for required fields that aren't mapped
        required_fields = [name for name, info in fields_info.items() if info.get('required', False)]
        mapped_model_fields = list(field_mappings.values())
        
        for required_field in required_fields:
            if required_field not in mapped_model_fields:
                validation_results['missing_required_fields'].append(required_field)
        
        # Validate each mapping
        for csv_field, model_field in field_mappings.items():
            if model_field and model_field not in fields_info:
                validation_results['mapping_errors'].append({
                    'csv_field': csv_field,
                    'model_field': model_field,
                    'error': f'Model field {model_field} does not exist'
                })
        
        # Validate sample data if provided
        if sample_data:
            for i, row in enumerate(sample_data[:5]):  # Validate first 5 rows
                row_errors = []
                for csv_field, model_field in field_mappings.items():
                    if model_field and csv_field in row:
                        field_info = fields_info.get(model_field, {})
                        is_valid, error_msg, converted_value = ModelIntrospector.validate_field_value(
                            field_info, row[csv_field]
                        )
                        if not is_valid:
                            row_errors.append({
                                'csv_field': csv_field,
                                'model_field': model_field,
                                'value': row[csv_field],
                                'error': error_msg
                            })
                
                if row_errors:
                    validation_results['sample_validation'].append({
                        'row_index': i,
                        'errors': row_errors
                    })
        
        # Calculate validation score
        total_checks = len(field_mappings) + len(required_fields)
        errors_count = len(validation_results['mapping_errors']) + len(validation_results['missing_required_fields'])
        validation_score = max(0, (total_checks - errors_count) / total_checks * 100) if total_checks > 0 else 0
        
        return JsonResponse({
            'success': True,
            'validation': validation_results,
            'validation_score': round(validation_score, 2),
            'is_valid': errors_count == 0
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@require_http_methods(["GET"])
def suggest_mappings(request):
    """API endpoint to suggest field mappings based on CSV headers and model fields"""
    try:
        model_name = request.GET.get('model_name')
        csv_headers = request.GET.getlist('csv_headers')
        
        if not model_name or not csv_headers:
            return JsonResponse({
                'success': False,
                'error': 'model_name and csv_headers are required'
            }, status=400)
        
        # Get model fields
        fields_info = ModelIntrospector.get_model_fields(model_name)
        if not fields_info:
            return JsonResponse({
                'success': False,
                'error': f'Model {model_name} not found'
            }, status=404)
        
        # Generate suggestions using the FieldMapper utility
        from .utils import FieldMapper
        suggested_mappings = FieldMapper.suggest_mappings(csv_headers, fields_info)
        
        # Calculate confidence scores for each suggestion
        suggestions_with_confidence = {}
        for csv_field, model_field in suggested_mappings.items():
            if model_field:
                # Simple confidence calculation based on name similarity
                csv_lower = csv_field.lower().replace('_', '').replace(' ', '')
                model_lower = model_field.lower().replace('_', '')
                
                if csv_lower == model_lower:
                    confidence = 100
                elif csv_lower in model_lower or model_lower in csv_lower:
                    confidence = 80
                elif any(word in model_lower for word in csv_lower.split()):
                    confidence = 60
                else:
                    confidence = 40
                
                suggestions_with_confidence[csv_field] = {
                    'suggested_field': model_field,
                    'confidence': confidence,
                    'field_info': fields_info.get(model_field, {})
                }
        
        return JsonResponse({
            'success': True,
            'suggestions': suggestions_with_confidence,
            'model_fields': fields_info
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

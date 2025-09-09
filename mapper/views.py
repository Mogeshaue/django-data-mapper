from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib import messages
import json
import io

from .models import UploadSession
from .utils import ModelIntrospector, FileProcessor, FieldMapper


def index(request):
    """Home page with file upload form"""
    return render(request, 'mapper/index.html')


@require_http_methods(["POST"])
def upload_file(request):
    """Handle file upload and initial processing"""
    try:
        if 'file' not in request.FILES:
            messages.error(request, 'No file selected.')
            return redirect('index')
        
        uploaded_file = request.FILES['file']
        
        # Detect file type
        try:
            file_type = FileProcessor.detect_file_type(uploaded_file)
        except ValueError as e:
            messages.error(request, str(e))
            return redirect('index')
        
        # Read file preview data
        try:
            headers, preview_data = FileProcessor.read_file_data(uploaded_file, file_type, max_rows=10)
        except ValueError as e:
            messages.error(request, str(e))
            return redirect('index')
        
        # Create upload session
        session = UploadSession.objects.create(
            file=uploaded_file,
            original_filename=uploaded_file.name,
            file_type=file_type,
            preview_data=preview_data
        )
        
        return redirect('model_selection', session_id=session.id)
        
    except Exception as e:
        messages.error(request, f'Error processing file: {str(e)}')
        return redirect('index')


def model_selection(request, session_id):
    """Show model selection page"""
    session = get_object_or_404(UploadSession, id=session_id)
    
    # Get all available models
    all_models = ModelIntrospector.get_all_models()
    
    # Filter out system models and focus on user models
    user_models = {}
    for model_name, model_class in all_models.items():
        app_label = model_class._meta.app_label
        if app_label not in ['admin', 'auth', 'contenttypes', 'sessions', 'messages']:
            user_models[model_name] = {
                'name': model_name,
                'verbose_name': model_class._meta.verbose_name,
                'app_label': app_label
            }
    
    context = {
        'session': session,
        'models': user_models,
        'preview_data': session.preview_data[:5] if session.preview_data else []
    }
    
    return render(request, 'mapper/model_selection.html', context)


@require_http_methods(["POST"])
def select_model(request, session_id):
    """Handle model selection and redirect to field mapping"""
    session = get_object_or_404(UploadSession, id=session_id)
    
    target_model = request.POST.get('target_model')
    if not target_model:
        messages.error(request, 'Please select a target model.')
        return redirect('model_selection', session_id=session_id)
    
    session.target_model = target_model
    session.save()
    
    return redirect('field_mapping', session_id=session_id)


def field_mapping(request, session_id):
    """Show field mapping interface"""
    session = get_object_or_404(UploadSession, id=session_id)
    
    if not session.target_model:
        messages.error(request, 'Please select a target model first.')
        return redirect('model_selection', session_id=session_id)
    
    # Get model fields
    model_fields = ModelIntrospector.get_model_fields(session.target_model)
    
    # Get CSV headers from preview data
    csv_headers = []
    if session.preview_data:
        csv_headers = list(session.preview_data[0].keys()) if session.preview_data else []
    
    # Get or create field mappings
    if not session.field_mappings:
        # Suggest initial mappings
        suggested_mappings = FieldMapper.suggest_mappings(csv_headers, model_fields)
        session.field_mappings = suggested_mappings
        session.save()
    
    context = {
        'session': session,
        'csv_headers': csv_headers,
        'model_fields': model_fields,
        'field_mappings': session.field_mappings,
        'preview_data': session.preview_data[:5] if session.preview_data else []
    }
    
    return render(request, 'mapper/field_mapping.html', context)


@require_http_methods(["POST"])
def update_mapping(request, session_id):
    """Update field mappings via AJAX"""
    session = get_object_or_404(UploadSession, id=session_id)
    
    try:
        data = json.loads(request.body)
        csv_field = data.get('csv_field')
        model_field = data.get('model_field')
        
        if csv_field:
            if not session.field_mappings:
                session.field_mappings = {}
            
            session.field_mappings[csv_field] = model_field
            session.save()
            
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'error': 'Missing csv_field'})
            
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@require_http_methods(["POST"])
def process_file(request, session_id):
    """Process the entire file with current mappings"""
    session = get_object_or_404(UploadSession, id=session_id)
    
    if not session.target_model or not session.field_mappings:
        messages.error(request, 'Please complete the field mapping first.')
        return redirect('field_mapping', session_id=session_id)
    
    try:
        # Process the entire file
        valid_records, invalid_records = FileProcessor.process_full_file(
            session.file,
            session.file_type,
            session.field_mappings,
            session.target_model
        )
        
        # Save processed data
        session.processed_data = valid_records
        session.validation_errors = invalid_records
        session.save()
        
        return redirect('results', session_id=session_id)
        
    except Exception as e:
        messages.error(request, f'Error processing file: {str(e)}')
        return redirect('field_mapping', session_id=session_id)


def results(request, session_id):
    """Show processing results"""
    session = get_object_or_404(UploadSession, id=session_id)
    
    context = {
        'session': session,
        'valid_count': len(session.processed_data),
        'invalid_count': len(session.validation_errors),
        'preview_valid': session.processed_data[:10] if session.processed_data else [],
        'preview_invalid': session.validation_errors[:10] if session.validation_errors else []
    }
    
    return render(request, 'mapper/results.html', context)


def download_json(request, session_id):
    """Download processed data as JSON"""
    session = get_object_or_404(UploadSession, id=session_id)
    
    if not session.processed_data:
        messages.error(request, 'No processed data available for download.')
        return redirect('results', session_id=session_id)
    
    # Create JSON response
    json_data = json.dumps(session.processed_data, indent=2, ensure_ascii=False)
    
    response = HttpResponse(json_data, content_type='application/json')
    filename = f"{session.original_filename.rsplit('.', 1)[0]}_processed.json"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    return response


def download_errors(request, session_id):
    """Download validation errors as JSON"""
    session = get_object_or_404(UploadSession, id=session_id)
    
    if not session.validation_errors:
        messages.error(request, 'No validation errors available for download.')
        return redirect('results', session_id=session_id)
    
    # Create JSON response
    json_data = json.dumps(session.validation_errors, indent=2, ensure_ascii=False)
    
    response = HttpResponse(json_data, content_type='application/json')
    filename = f"{session.original_filename.rsplit('.', 1)[0]}_errors.json"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    return response

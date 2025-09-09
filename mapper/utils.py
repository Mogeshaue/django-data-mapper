import pandas as pd
import openpyxl
from django.apps import apps
from django.db import models
from django.core.exceptions import ValidationError
import json
import io
from typing import Dict, List, Any, Tuple, Optional


class ModelIntrospector:
    """Utility class for introspecting Django models dynamically"""
    
    @staticmethod
    def get_all_models() -> Dict[str, models.Model]:
        """Get all available Django models"""
        all_models = {}
        for model in apps.get_models():
            app_label = model._meta.app_label
            model_name = model.__name__
            full_name = f"{app_label}.{model_name}"
            all_models[full_name] = model
        return all_models
    
    @staticmethod
    def get_model_fields(model_name: str) -> Dict[str, Dict[str, Any]]:
        """Get field information for a specific model"""
        try:
            all_models = ModelIntrospector.get_all_models()
            if model_name not in all_models:
                return {}
            
            model = all_models[model_name]
            fields_info = {}
            
            for field in model._meta.get_fields():
                if hasattr(field, 'name'):
                    field_info = {
                        'name': field.name,
                        'type': field.__class__.__name__,
                        'required': not (field.blank or field.null) if hasattr(field, 'blank') else True,
                        'max_length': getattr(field, 'max_length', None),
                        'choices': getattr(field, 'choices', None),
                        'help_text': getattr(field, 'help_text', ''),
                        'default': getattr(field, 'default', None)
                    }
                    
                    # Handle special field types
                    if isinstance(field, models.ForeignKey):
                        field_info['related_model'] = f"{field.related_model._meta.app_label}.{field.related_model.__name__}"
                    
                    fields_info[field.name] = field_info
            
            return fields_info
        except Exception as e:
            return {}
    
    @staticmethod
    def validate_field_value(field_info: Dict[str, Any], value: Any) -> Tuple[bool, str, Any]:
        """Validate a value against a field definition"""
        try:
            if value is None or value == '':
                if field_info.get('required', True):
                    return False, "This field is required", None
                return True, "", None
            
            field_type = field_info['type']
            converted_value = value
            
            # Type conversion based on field type
            if field_type in ['IntegerField', 'BigIntegerField', 'SmallIntegerField']:
                try:
                    converted_value = int(float(str(value)))
                except (ValueError, TypeError):
                    return False, f"Invalid integer value: {value}", None
            
            elif field_type in ['FloatField', 'DecimalField']:
                try:
                    converted_value = float(value)
                except (ValueError, TypeError):
                    return False, f"Invalid numeric value: {value}", None
            
            elif field_type == 'BooleanField':
                if str(value).lower() in ['true', '1', 'yes', 'on']:
                    converted_value = True
                elif str(value).lower() in ['false', '0', 'no', 'off']:
                    converted_value = False
                else:
                    return False, f"Invalid boolean value: {value}", None
            
            elif field_type in ['CharField', 'TextField']:
                converted_value = str(value)
                max_length = field_info.get('max_length')
                if max_length and len(converted_value) > max_length:
                    return False, f"Text too long (max {max_length} characters)", None
            
            elif field_type in ['DateField', 'DateTimeField']:
                try:
                    # Try to parse date/datetime
                    converted_value = pd.to_datetime(value).isoformat()
                except Exception:
                    return False, f"Invalid date/datetime format: {value}", None
            
            elif field_type == 'EmailField':
                import re
                email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                if not re.match(email_regex, str(value)):
                    return False, f"Invalid email format: {value}", None
                converted_value = str(value)
            
            # Check choices if available
            choices = field_info.get('choices')
            if choices:
                valid_choices = [choice[0] for choice in choices]
                if converted_value not in valid_choices:
                    return False, f"Invalid choice. Must be one of: {valid_choices}", None
            
            return True, "", converted_value
            
        except Exception as e:
            return False, f"Validation error: {str(e)}", None


class FileProcessor:
    """Utility class for processing uploaded files"""
    
    @staticmethod
    def detect_file_type(file) -> str:
        """Detect file type based on extension"""
        filename = file.name.lower()
        if filename.endswith('.csv'):
            return 'csv'
        elif filename.endswith(('.xlsx', '.xls')):
            return 'excel'
        else:
            raise ValueError("Unsupported file type. Please upload CSV or Excel files only.")
    
    @staticmethod
    def read_file_data(file, file_type: str, max_rows: int = 100) -> Tuple[List[str], List[Dict[str, Any]]]:
        """Read data from uploaded file and return headers and preview data"""
        try:
            if file_type == 'csv':
                # Reset file pointer
                file.seek(0)
                df = pd.read_csv(file, nrows=max_rows)
            elif file_type == 'excel':
                # Reset file pointer
                file.seek(0)
                df = pd.read_excel(file, nrows=max_rows)
            else:
                raise ValueError(f"Unsupported file type: {file_type}")
            
            # Clean column names (remove extra spaces, etc.)
            df.columns = df.columns.astype(str).str.strip()
            
            # Replace NaN values with empty strings for preview
            df = df.fillna('')
            
            headers = df.columns.tolist()
            data = df.to_dict('records')
            
            return headers, data
            
        except Exception as e:
            raise ValueError(f"Error reading file: {str(e)}")
    
    @staticmethod
    def process_full_file(file, file_type: str, field_mappings: Dict[str, str], 
                         target_model: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Process the entire file with field mappings and validation"""
        try:
            if file_type == 'csv':
                file.seek(0)
                df = pd.read_csv(file)
            elif file_type == 'excel':
                file.seek(0)
                df = pd.read_excel(file)
            else:
                raise ValueError(f"Unsupported file type: {file_type}")
            
            # Clean column names
            df.columns = df.columns.astype(str).str.strip()
            df = df.fillna('')
            
            # Get model field information
            model_fields = ModelIntrospector.get_model_fields(target_model)
            
            valid_records = []
            invalid_records = []
            
            for index, row in df.iterrows():
                record = {}
                errors = []
                
                # Apply field mappings and validate
                for csv_field, model_field in field_mappings.items():
                    if model_field and model_field in model_fields:
                        value = row.get(csv_field, '')
                        
                        is_valid, error_msg, converted_value = ModelIntrospector.validate_field_value(
                            model_fields[model_field], value
                        )
                        
                        if is_valid:
                            record[model_field] = converted_value
                        else:
                            errors.append({
                                'field': model_field,
                                'value': value,
                                'error': error_msg
                            })
                
                if errors:
                    invalid_records.append({
                        'row': index + 1,
                        'data': dict(row),
                        'errors': errors
                    })
                else:
                    valid_records.append(record)
            
            return valid_records, invalid_records
            
        except Exception as e:
            raise ValueError(f"Error processing file: {str(e)}")


class FieldMapper:
    """Utility class for suggesting and managing field mappings"""
    
    @staticmethod
    def suggest_mappings(csv_headers: List[str], model_fields: Dict[str, Dict[str, Any]]) -> Dict[str, str]:
        """Suggest field mappings based on field names similarity"""
        suggestions = {}
        
        for csv_header in csv_headers:
            best_match = ""
            best_score = 0
            
            csv_header_clean = csv_header.lower().replace('_', '').replace(' ', '').replace('-', '')
            
            for model_field_name, model_field_info in model_fields.items():
                model_field_clean = model_field_name.lower().replace('_', '').replace(' ', '').replace('-', '')
                
                # Exact match
                if csv_header_clean == model_field_clean:
                    best_match = model_field_name
                    break
                
                # Partial match
                if csv_header_clean in model_field_clean or model_field_clean in csv_header_clean:
                    score = min(len(csv_header_clean), len(model_field_clean)) / max(len(csv_header_clean), len(model_field_clean))
                    if score > best_score and score > 0.6:  # Only suggest if similarity > 60%
                        best_match = model_field_name
                        best_score = score
            
            suggestions[csv_header] = best_match
        
        return suggestions

# Django Data Mapper

A Django-based web application that converts CSV and Excel files to JSON format by dynamically mapping data to Django models.

## Features

- **File Upload Support**: Accepts both CSV and Excel files (.csv, .xlsx, .xls)
- **Dynamic Model Introspection**: Automatically discovers all Django models in your project
- **Smart Field Mapping**: Suggests field mappings based on column names similarity
- **Data Validation**: Validates each record against Django model field types and constraints
- **Error Handling**: Identifies and reports invalid records with detailed error messages
- **JSON Export**: Generates clean JSON output for valid records
- **User-Friendly Interface**: Step-by-step wizard interface with Bootstrap styling

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd django-data-mapper
```

2. Create and activate a virtual environment:
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python -m venv venv
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run migrations:
```bash
python manage.py makemigrations
python manage.py migrate
```

5. Start the development server:
```bash
python manage.py runserver
```

6. Open your browser and navigate to:
```
http://127.0.0.1:8000/
```

## Usage

1. **Upload File**: Select and upload a CSV or Excel file
2. **Select Model**: Choose the target Django model from the available models
3. **Map Fields**: Review and adjust the suggested field mappings
4. **Process & Download**: Process the file and download the resulting JSON

## Project Structure

```
django-data-mapper/
├── datamapper/          # Main Django project settings
├── mapper/              # Main application
│   ├── models.py        # UploadSession model and sample models
│   ├── views.py         # View functions for handling requests
│   ├── utils.py         # Utility classes for file processing
│   ├── urls.py          # URL routing
│   └── templatetags/    # Custom template filters
├── templates/           # HTML templates
│   ├── base.html        # Base template with Bootstrap
│   └── mapper/          # App-specific templates
├── media/               # Uploaded files storage
├── static/              # Static files (CSS, JS)
└── sample_products.csv  # Sample CSV file for testing
```

## Key Components

### Models
- **UploadSession**: Tracks file upload sessions and processing state
- **Product**: Sample model for testing (products catalog)
- **Customer**: Sample model for testing (customer records)

### Utilities
- **ModelIntrospector**: Dynamically discovers and analyzes Django models
- **FileProcessor**: Handles CSV/Excel file reading and processing
- **FieldMapper**: Suggests intelligent field mappings

### Features in Detail

#### Dynamic Model Discovery
The application automatically discovers all Django models in your project and presents them for selection. System models (auth, admin, etc.) are filtered out by default.

#### Field Type Validation
Supports validation for various Django field types:
- CharField, TextField (with max_length validation)
- IntegerField, FloatField, DecimalField
- BooleanField
- DateField, DateTimeField
- EmailField (with format validation)
- Fields with choices

#### Error Reporting
Invalid records are captured with detailed error information:
- Row number
- Field name
- Invalid value
- Specific error message

## Sample Data

A sample CSV file (`sample_products.csv`) is included for testing the Product model. It contains 10 product records with various field types.

## Requirements

- Python 3.9+
- Django 4.2+
- pandas
- openpyxl (for Excel support)
- xlrd (for older Excel formats)

## Development

### Adding New Models
Simply create new models in any Django app, run migrations, and they'll automatically appear in the model selection.

### Customizing Field Mapping Logic
Edit the `FieldMapper.suggest_mappings()` method in `mapper/utils.py` to customize the mapping suggestion algorithm.

### Extending File Format Support
The `FileProcessor` class in `mapper/utils.py` can be extended to support additional file formats.

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

import os
import uuid
import hashlib
import traceback
import threading
import json
# from dotenv import load_dotenv
import logging
import logging.handlers
from datetime import datetime

import pyodbc



# Load environment variables from .env file
# load_dotenv()

# Configure logging
# Create logs directory if it doesn't exist
if not os.path.exists('logs'):
    os.makedirs('logs')


# Set up root logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)



# Create log file with timestamp
log_file = f"logs/app_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

# File handler with rotation
file_handler = logging.handlers.RotatingFileHandler(
    log_file,
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5
)
file_handler.setLevel(logging.INFO)

# Console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# Create formatter and add it to the handlers
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# Add the handlers to the logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)

logging.info('Starting application with logging configured')

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
from azure.storage.blob import BlobServiceClient
from azure.core.credentials import AzureKeyCredential
from azure.search.documents.indexes import SearchIndexerClient
# This class doesn't exist in the current version
# Database connection setup
from db_helper import DBConnectionManager
import os

# SQL Server connection string
conn_str = os.getenv('CONNECTION_STRING')

logger.info(f"conn_str: {conn_str}")

# Initialize DB connection manager
DBConnectionManager.initialize(conn_str)

# Initialize Flask app with static folder for React frontend
app = Flask(__name__, static_folder='frontend/build', static_url_path='/')

# Enable CORS for all routes and origins with all necessary options
CORS(app,
     resources={r"/*": {"origins": "*"}},
     supports_credentials=True,
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
     allow_headers=["Content-Type", "X-Compound-ID", "Authorization"]
)


# Register API blueprint
from api_routes import api_bp
app.register_blueprint(api_bp)

# Configure Azure Blob Storage

# Azure OpenAI Configuration
AZURE_OPENAI_ENDPOINT = os.getenv('AZURE_OPENAI_ENDPOINT')
AZURE_OPENAI_KEY = os.getenv('AZURE_OPENAI_KEY')
AZURE_OPENAI_DEPLOYMENT = os.getenv('AZURE_OPENAI_DEPLOYMENT')

# Configure OpenAI client - simplified approach

# We'll use the base openai module for API calls
# This avoids client initialization issues


# Import shared utilities
from utils import APIError, extract_compound_id, create_response


# Configure upload folder (temporary storage before upload to Azure)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER



# Flask cleanup on shutdown
import atexit

# Register shutdown function with atexit
@atexit.register
def shutdown_event():
    logging.info("Shutting down application, closing database connections...")
    try:
        DBConnectionManager.close()
        logging.info("Database connections closed successfully")
    except Exception as e:
        logging.error(f"Error closing database connections: {str(e)}")
        logging.debug("Exception details", exc_info=True)


@app.route('/test')
def test():
    return create_response(
                data={'status': True
                })

@app.route('/test-db')
def test_db():
    logger.info("##############")
    logger.info(pyodbc.drivers())
    logger.info("##############")

    return create_response(
                data={'status': True,
                'drivers': len(pyodbc.drivers)
                })


@app.route('/')
def home():
    return send_from_directory(app.static_folder, 'index.html')


@app.route('/api/indexer-status')
def indexer_status():
    from upload_file import indexer_client, AZURE_SEARCH_INDEXER_NAME
    
    # Get optional document ID parameter
    document_id = request.args.get('document_id')
    
    if document_id:
        # Get document indexer details from the database
        db = DBConnectionManager.get_instance()
        result = db.select("SELECT id, index_name, indexer_name, status, error_message FROM ipx_documents WHERE id = ?", (document_id,))
        
        if not result or len(result) == 0:
            return create_response(
                status='error',
                error={
                    'code': 'DOCUMENT_NOT_FOUND',
                    'message': f'Document with ID {document_id} not found'
                },
                status_code=404
            )
            
        document = result[0]
        indexer_name = document['indexer_name']
        
        try:
            # Get indexer status from Azure Search
            indexer_status = indexer_client.get_indexer_status(indexer_name)
            
            return create_response(
                data={
                    'document_id': document['id'],
                    'indexer_name': indexer_name,
                    'index_name': document['index_name'],
                    'status': document['status'],
                    'error_message': document['error_message'],
                    'indexer_status': indexer_status.status,
                    'last_run': {
                        'status': indexer_status.last_result.status if indexer_status.last_result else 'No runs yet',
                        'message': indexer_status.last_result.error_message if indexer_status.last_result and hasattr(indexer_status.last_result, 'error_message') else None,
                        'start_time': str(indexer_status.last_result.start_time) if indexer_status.last_result else None,
                        'end_time': str(indexer_status.last_result.end_time) if indexer_status.last_result else None,
                        'document_count': indexer_status.last_result.document_count if indexer_status.last_result else 0,
                        'error_count': indexer_status.last_result.error_count if indexer_status.last_result else 0,
                    }
                }
            )
        except Exception as e:
            # Indexer might not exist yet or other error
            return create_response(
                data={
                    'document_id': document['id'],
                    'indexer_name': indexer_name,
                    'index_name': document['index_name'],
                    'status': document['status'],
                    'error_message': document['error_message'],
                    'indexer_status': 'unknown',
                    'error': str(e)
                }
            )
    else:
        # Get general indexer status (original behavior)
        status = indexer_client.get_indexer_status(AZURE_SEARCH_INDEXER_NAME)
        return create_response(
            data={
                'indexer_name': AZURE_SEARCH_INDEXER_NAME,
                'status': status.status,
                'last_run': status.last_result.status if status.last_result else 'No runs yet'
            }
        )
    
# Global error handler for APIError exceptions
@app.errorhandler(APIError)
def handle_api_error(error):
    return create_response(
        status='error',
        error={
            'code': error.error_code,
            'message': error.message
        },
        status_code=error.status_code
    )

# Catch-all route to serve React app for any non-API routes
@app.route('/<path:path>')
def serve_react(path):
    # Check if the path is for an API route
    if path.startswith('api/'):
        return jsonify({'error': 'API endpoint not found'}), 404
    # Otherwise serve the React app
    return send_from_directory(app.static_folder, 'index.html')


@app.route('/api/index-documents', methods=['POST'])
def index_documents():
    try:
        # Extract headers
        compound_id = extract_compound_id(request)
        
        # Check if a file was uploaded
        if 'file' not in request.files:
            return create_response(
                status='error',
                error={
                    'code': 'FILE_MISSING',
                    'message': 'No file part in the request'
                },
                status_code=400
            )
        
        file = request.files['file']
    
        # If user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            return create_response(
                status='error',
                error={
                    'code': 'FILENAME_MISSING',
                    'message': 'No selected file'
                },
                status_code=400
            )
    
        # Calculate SHA-256 hash of file content
        import hashlib
        file_content = file.read()
        file_hash = hashlib.sha256(file_content).hexdigest()
        
        # Reset file pointer after reading
        file.seek(0)

        duplicate_file = DBConnectionManager.get_instance().select("SELECT * FROM ipx_documents WHERE compound_id = ? and sha256 = ?", (compound_id, file_hash))
        print(f"Is duplicate file: {duplicate_file}")
        
        if duplicate_file and len(duplicate_file) > 0:
            return create_response(
                status='error',
                error={
                    'code': 'DUPLICATE_DOCUMENT',
                    'message': 'This document has already been uploaded for this compound',
                    'document_id': duplicate_file[0]['id']
                },
                status_code=409  # Conflict
            )

        # Generate a unique blob name to avoid overwrites
        original_filename = secure_filename(file.filename)
        # Add a UUID to ensure uniqueness
        unique_filename = f"{uuid.uuid4()}_{original_filename}"
        
        # Save file temporarily
        temp_file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        os.makedirs(os.path.dirname(temp_file_path), exist_ok=True)
        file.save(temp_file_path)
        
        # Upload file to blob storage
        from upload_file import upload_file
        
        size = os.path.getsize(temp_file_path)  # Get file size
        result = upload_file(temp_file_path, unique_filename, original_filename, size, file_hash, compound_id)
        return result
        # The upload_file function now returns standardized responses
    except APIError:
        # APIErrors are already handled by the global error handler
        raise
    except Exception as e:
        logging.error("Unexpected error", exc_info=True)  # Log full stack trace to file
        return create_response(
            status='error',
            error={
                'code': 'INTERNAL_SERVER_ERROR',
                'message': f'An unexpected error occurred: {str(e)}'
            },
            status_code=500
        )


@app.route('/api/search-documents', methods=['POST'])
def search_documents():
    # Get data from request body
    data = request.get_json()
    
    # Validate required fields
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    user_query = data.get('query')
    
    if not user_query:
        return jsonify({'error': 'Missing required field: query'}), 400
    
    # Optional parameters
    document_ids = data.get('documentIds', [])
    
    try:
        # Get compound ID from header (will use default if not provided)
        try:
            compound_id = extract_compound_id(request)
        except Exception as e:
            logging.warning(f"Could not extract compound ID: {str(e)}")
            compound_id = None
        
        # Import and call the search function with all required parameters
        from open_ai_azure import search_documents

        # Pass both document_ids and compound_id
        # If document_ids is provided, it will search those specific documents
        # If not, it will use compound_id to find all indexed documents for that compound
        result, sources = search_documents(user_query, document_ids, compound_id)
        
        logging.info(f"Search completed across {len(sources)} sources")
            
        return jsonify({
            'success': True,
            'message': 'Search completed',
            'query': user_query,
            'answer': result,
            "sources": sources
        })
            
    except Exception as e:
        # Log the error but don't raise it to the user
        logging.error(f"Search error: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'Failed to search documents: {str(e)}'
        }), 500

@app.route('/api/search-database', methods=['POST'])
def search_database():
    # Get data from request body
    data = request.get_json()
    
    # Validate required fields
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    query = data.get('query')
    table_name = data.get('table_name')
    columns = data.get('columns', '*')  # Default to all columns if not specified
    include_summary = data.get('summary', False)  # Get summary boolean parameter, default to False
    
    if not query or not table_name:
        return jsonify({'error': 'Missing required fields: query or table_name'}), 400

    
    
    try:
        # Create the prompt for Azure OpenAI
        prompt = f"""Based on the following SQL table schema:

Table: Products (ipx_b_products)

id: Unique identifier for the product

name: Name of the product

description: Description of the product

category_id: Foreign key referencing Categories.id

supplier_id: Foreign key referencing Suppliers.id

price: Price of the product

stock_quantity: Quantity in stock

created_at: Timestamp when the product was created

Table: Categories (ipx_b_categories)

id: Unique identifier for the category

name: Name of the category

created_at: Timestamp when the category was created

Table: Suppliers (ipx_b_suppliers)

id: Unique identifier for the supplier

name: Name of the supplier

contact_email: Email address for the supplier

phone_number: Phone number for the supplier

address: Physical address of the supplier

created_at: Timestamp when the supplier was created



Generate a SQL query to answer this question: "{query}"

this is the main table the user spesified: {table_name}

If specific columns were requested, please include only these columns: {columns if columns != '*' else 'All columns are requested'}

Return only the SQL query without any explanation."""

        # Call Azure OpenAI to generate SQL query from natural language
        try:
            # Will be overwritten by the actual OpenAI response
            generated_sql = ''
            # Import using the latest OpenAI library pattern
            from openai import AzureOpenAI
            
            # Clean initialization with only required parameters
            client = AzureOpenAI(
                azure_endpoint=AZURE_OPENAI_ENDPOINT,
                api_key=AZURE_OPENAI_KEY,
                api_version="2023-05-15"
            )

            
            # Generate SQL from natural language query
            response = client.chat.completions.create(
                model=AZURE_OPENAI_DEPLOYMENT,
                messages=[
                    {"role": "system", "content": "You are a SQL expert specializing in Microsoft SQL Server syntax. Generate only SQL queries compatible with SQL Server (use TOP instead of LIMIT, proper date functions, etc). Do not include any explanations or markdown formatting in your response."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=5000
            )
            
            # Extract the SQL query from the response
            generated_sql = response.choices[0].message.content.strip()
            
            # Remove any markdown code block formatting if present
            if generated_sql.startswith('```sql'):
                generated_sql = generated_sql[6:]
            if generated_sql.endswith('```'):
                generated_sql = generated_sql[:-3]
            generated_sql = generated_sql.strip()
            
        except Exception as openai_error:
            # Catch any OpenAI-related errors
            raise Exception(f"OpenAI API error: {str(openai_error)}")
        
        # Connect to the database and execute the query
        try:
            # Initialize the connection manager with our connection string
            # DBConnectionManager.initialize(conn_str)
            # Validate that the SQL query is read-only before execution
            sql_lower = generated_sql.lower().strip()
            
            # Check if the query starts with select and doesn't contain any data modification keywords
            if not sql_lower.startswith('select'):
                return jsonify({
                    'success': False,
                    'message': 'Security error: Only SELECT queries are allowed',
                    'query': query,
                    'table_name': table_name,
                    'generated_sql': generated_sql
                }), 403
                
            # Check for potentially dangerous operations
            dangerous_keywords = ['insert', 'update', 'delete', 'drop', 'alter', 'truncate', 
                                 'create', 'exec', 'execute', 'sp_', 'xp_']
            
            for keyword in dangerous_keywords:
                if keyword in sql_lower.split():
                    return jsonify({
                        'success': False,
                        'message': f'Security error: Dangerous operation detected: {keyword}',
                        'query': query,
                        'table_name': table_name,
                        'generated_sql': generated_sql
                    }), 403
            
            # Get the singleton instance
            db_manager = DBConnectionManager.get_instance()
            
            # Execute the validated SQL query using the select method
            results = db_manager.select(generated_sql)
            db_manager.close()
            
            # Prepare the response
            response_data = {
                'success': True,
                'message': 'Database search completed',
                'query': query,
                'table_name': table_name,
                'columns': columns,
                'generated_sql': generated_sql,  # Include the generated SQL for transparency
                'results': results
            }
            
            # Only include summary if explicitly requested
            if include_summary:
                response_data['summary'] = convert_db_result_to_human(results, query)
            
            return jsonify(response_data)
            
        except Exception as db_error:
            # Return an error if database execution fails
            return jsonify({
                'success': False,
                'message': f'Database execution error: {str(db_error)}',
                'query': query,
                'table_name': table_name,
                'generated_sql': generated_sql
            }), 500
            
    except Exception as e:
        # Handle any errors that occur during the OpenAI API call
        return jsonify({
            'success': False,
            'message': f'Error generating SQL: {str(e)}',
            'query': query,
            'table_name': table_name
        }), 500


def convert_db_result_to_human(db_result, user_question):
    from openai import AzureOpenAI
    
    # Clean initialization with only required parameters
    client = AzureOpenAI(
        azure_endpoint=AZURE_OPENAI_ENDPOINT,
        api_key=AZURE_OPENAI_KEY,
        api_version="2023-05-15"
    )

    
    # Generate SQL from natural language query
    response = client.chat.completions.create(
        model=AZURE_OPENAI_DEPLOYMENT,
        messages=[
            {"role": "system", "content": f"You need to take the user question and db results and return human readdable text to give a summary of the db results"},
            {"role": "user", "content": f"You have this user question {user_question} and the database query result return humman text that reacap the results this is the db results: {db_result}"}
        ],
        temperature=0.3,
        max_tokens=5000
    )
    
    # Extract the SQL query from the response
    generated_sql = response.choices[0].message.content.strip()
    
    # Remove any markdown code block formatting if present
    return generated_sql

if __name__ == '__main__':
    app.run(debug=False)


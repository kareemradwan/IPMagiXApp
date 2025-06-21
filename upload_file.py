from azure.storage.blob import BlobServiceClient, ContentSettings
import os
import traceback
import time
import re
import hashlib
import logging
from flask import jsonify
import threading
from azure.search.documents.indexes import SearchIndexerClient, SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex, SimpleField, SearchableField, SearchField, 
    SearchFieldDataType, IndexingSchedule, SearchIndexer, 
    SearchIndexerDataSourceConnection,
    BlobIndexerParsingMode
)
from azure.core.exceptions import ResourceExistsError, HttpResponseError
from azure.core.credentials import AzureKeyCredential

from db_helper import DBConnectionManager

# Helper function to create standardized API responses
def create_response(status="success", data=None, error=None, status_code=200):
    """
    Creates a standardized API response
    
    Args:
        status (str): 'success' or 'error'
        data (dict): Data to return for successful responses
        error (dict): Error information with code and message
        status_code (int): HTTP status code
        
    Returns:
        tuple: (response_json, status_code)
    """
    response = {'status': status}
    
    if data is not None:
        response['data'] = data
    
    if error is not None:
        response['error'] = error
    
    return jsonify(response), status_code


CONTAINER_NAME = os.getenv('CONTAINER_NAME')

BLOB_CONNECTION_STRING = os.getenv('BLOB_CONNECTION_STRING',  '')
AZURE_SEARCH_ENDPOINT = os.getenv('AZURE_SEARCH_ENDPOINT') 
AZURE_SEARCH_API_KEY = os.getenv('AZURE_SEARCH_API_KEY')

# Create search clients
indexer_client = SearchIndexerClient(
    endpoint=AZURE_SEARCH_ENDPOINT,
    credential=AzureKeyCredential(AZURE_SEARCH_API_KEY)
)

# We also need a SearchIndexClient for managing indexes
index_client = SearchIndexClient(
    endpoint=AZURE_SEARCH_ENDPOINT,
    credential=AzureKeyCredential(AZURE_SEARCH_API_KEY)
)

# Helper function to create valid Azure Search names (sanitize names)
def sanitize_name(name):
    """
    Convert a string into a valid Azure Search resource name
    - Must contain only lowercase letters, digits, or dashes
    - Cannot start or end with dashes
    - Limited to 128 characters
    """
    # Convert to lowercase and replace invalid characters with dashes
    sanitized = re.sub(r'[^a-z0-9-]', '-', name.lower())
    # Remove leading and trailing dashes
    sanitized = sanitized.strip('-')
    # Ensure it's not empty (if the name was all invalid chars)
    if not sanitized:
        # Generate a hash-based name if the sanitized name is empty
        sanitized = f"idx-{hashlib.md5(name.encode()).hexdigest()[:8]}"
    # Ensure it's not too long
    return sanitized[:128]

# Function to create index if it doesn't exist
def create_search_index(index_name):
    """
    Create an Azure Cognitive Search index with fields suitable for document data
    """
    try:
        # Sanitize the index name
        sanitized_index_name = sanitize_name(index_name)
        
        # Check if index exists
        try:
            index_client.get_index(sanitized_index_name)
            logging.info(f"Index {sanitized_index_name} already exists")
            return sanitized_index_name  # Index already exists
        except HttpResponseError:
            pass  # Index doesn't exist, create it
            
        # Define the index fields
        fields = [
            SimpleField(name="id", type=SearchFieldDataType.String, key=True),
            SimpleField(name="metadata_storage_name", type=SearchFieldDataType.String),
            SimpleField(name="metadata_storage_path", type=SearchFieldDataType.String),
            SimpleField(name="metadata_content_type", type=SearchFieldDataType.String),
            SearchableField(name="content", type=SearchFieldDataType.String),
            SearchField(name="title", type=SearchFieldDataType.String, searchable=True, retrievable=True),
            SimpleField(name="document_id", type=SearchFieldDataType.String),
            SimpleField(name="compound_id", type=SearchFieldDataType.String),
            SimpleField(name="url", type=SearchFieldDataType.String)
        ]
        
        # Create the index
        index = SearchIndex(name=sanitized_index_name, fields=fields)
        index_client.create_index(index)
        logging.info(f"Created index: {sanitized_index_name}")
        return sanitized_index_name
    except Exception as e:
        logging.error(f"Error creating index: {str(e)}", exc_info=True)
        return None

# Function to create data source for blob container
def create_data_source(data_source_name, container_name, blob_path=None):
    """
    Create an Azure Cognitive Search data source connected to the blob container
    """
    try:
        # Sanitize the data source name
        sanitized_data_source_name = sanitize_name(data_source_name)
        
        # Check if data source exists
        try:
            indexer_client.get_data_source_connection(sanitized_data_source_name)
            logging.info(f"Data source {sanitized_data_source_name} already exists")
            return sanitized_data_source_name  # Data source already exists
        except HttpResponseError:
            pass  # Data source doesn't exist, create it
            
        # Define data source with blob path query if needed
        container_params = {
            "name": container_name
        }
        
        # Add query parameter if blob path is specified
        if blob_path:
            # For folder-based approach, we use a prefix query
            container_params["query"] = f"{blob_path}"
        
        data_source = SearchIndexerDataSourceConnection(
            name=sanitized_data_source_name,
            type="azureblob",
            connection_string=BLOB_CONNECTION_STRING,
            container=container_params
        )
        
        # Create the data source
        indexer_client.create_data_source_connection(data_source)
        logging.info(f"Created data source: {sanitized_data_source_name}")
        return sanitized_data_source_name
    except Exception as e:
        logging.error(f"Error creating data source: {str(e)}", exc_info=True)
        return None

# Function to create indexer
def create_indexer(indexer_name, data_source_name, index_name):
    """
    Create an Azure Cognitive Search indexer to process content from the data source
    """
    try:
        # Sanitize the indexer name
        sanitized_indexer_name = sanitize_name(indexer_name)
        
        # Check if indexer exists
        try:
            indexer_client.get_indexer(sanitized_indexer_name)
            logging.info(f"Indexer {sanitized_indexer_name} already exists")
            return sanitized_indexer_name  # Indexer already exists
        except HttpResponseError:
            pass  # Indexer doesn't exist, create it
            
        # Define indexer
        indexer = SearchIndexer(
            name=sanitized_indexer_name,
            data_source_name=data_source_name,
            target_index_name=index_name,
            parameters={
                "configuration": {
                    "parsingMode": "default",
                    "indexStorageMetadataOnlyForOversizedDocuments": True
                }
            },
            schedule=IndexingSchedule(interval="PT5M")  # Run every 5 minutes
        )
        
        # Create the indexer
        indexer_client.create_indexer(indexer)
        logging.info(f"Created indexer: {sanitized_indexer_name}")
        return sanitized_indexer_name
    except Exception as e:
        logging.error(f"Error creating indexer: {str(e)}", exc_info=True)
        return None

# Function to check indexer status and update database
def check_indexer_status(indexer_name, document_id, max_retries=12, delay_seconds=10):
    """
    Check indexer status periodically and update document status in database
    """
    db = DBConnectionManager.get_instance()
    
    for attempt in range(max_retries):
        try:
            # Get indexer status
            status = indexer_client.get_indexer_status(indexer_name)
            
            # Check status
            if status.last_result:
                if status.last_result.status == "success":
                    # Update document status to indexed
                    db.execute_update(
                        "UPDATE ipx_documents SET status = ? WHERE id = ?",
                        ("indexed", document_id)
                    )
                    logging.info(f"Document {document_id} successfully indexed")
                    
                    # Restart the indexer to ensure index is updated properly
                    try:
                        logging.info(f"Restarting indexer {indexer_name} to ensure index is updated")
                        # indexer_client.reset_indexer(indexer_name)
                        indexer_client.run_indexer(indexer_name)
                        logging.info(f"Successfully restarted indexer {indexer_name}")
                    except Exception as e:
                        logging.error(f"Failed to restart indexer {indexer_name}: {str(e)}")

                    return
                elif status.last_result.status == "transientFailure" or status.last_result.status == "warning":
                    # Update with warning
                    db.execute_update(
                        "UPDATE ipx_documents SET status = ?, error_message = ? WHERE id = ?",
                        ("warning", f"Indexer warning: {status.last_result.error_message if status.last_result.error_message else 'Unknown warning'}", document_id)
                    )
                    logging.warning(f"Document {document_id} indexed with warnings")
                    return
                elif status.last_result.status == "failed":
                    # Update with failure
                    db.execute_update(
                        "UPDATE ipx_documents SET status = ?, error_message = ? WHERE id = ?",
                        ("failed", f"Indexer failed: {status.last_result.error_message if status.last_result.error_message else 'Unknown error'}", document_id)
                    )
                    logging.error(f"Document {document_id} indexing failed")
                    return
            
            # Still processing
            logging.info(f"Indexer {indexer_name} still processing, checking again in {delay_seconds} seconds...")
            time.sleep(delay_seconds)
            
        except Exception as e:
            logging.error(f"Error checking indexer status: {str(e)}", exc_info=True)
            time.sleep(delay_seconds)
    
    # If we get here, we've exceeded retry attempts
    db.execute_update(
        "UPDATE ipx_documents SET status = ?, error_message = ? WHERE id = ?",
        ("timeout", "Indexer status check timed out", document_id)
    )
    print(f"Timeout waiting for document {document_id} indexing status")

def trigger_indexer(indexer_name, index_name, blob_url, document_id):
    """
    Create and run a search indexer for the specified document
    
    Args:
        indexer_name: Name for the indexer
        index_name: Name for the search index
        blob_url: URL of the blob to index
        document_id: Database ID of the document
    """
    try:
        # Extract the folder path (not the full file path)
        try:
            if CONTAINER_NAME in blob_url:
                blob_path = blob_url.split(CONTAINER_NAME + '/')[1]
                # Get just the folder path without the filename
                folder_parts = blob_path.split('/')
                if len(folder_parts) > 1:
                    blob_folder = folder_parts[0] + '/'
                    print(f"Extracted folder path: {blob_folder}")
                else:
                    blob_folder = ""
                    print("No folder structure in URL")
            else:
                # Fallback extraction method
                parts = blob_url.split('/')
                if len(parts) > 4:
                    blob_folder = parts[4] + '/'
                    print(f"Alternative folder extraction: {blob_folder}")
                else:
                    blob_folder = ""
                    print("Could not extract folder path from URL")
        except Exception as e:
            print(f"Error extracting folder path: {str(e)}")
            blob_folder = ""
            
        data_source_name = f"datasrc-doc-{document_id}"
        
        print(f"Setting up indexer for document ID {document_id}: {blob_folder}")
        
        # Create search resources with sanitized names
        sanitized_index_name = create_search_index(index_name)
        if not sanitized_index_name:
            raise Exception("Failed to create search index")
        
        # Use the folder path for indexing all files in that folder
        sanitized_data_source = create_data_source(data_source_name, CONTAINER_NAME, blob_folder)
        if not sanitized_data_source:
            raise Exception("Failed to create data source")
        
        sanitized_indexer_name = create_indexer(indexer_name, sanitized_data_source, sanitized_index_name)
        
        # Run the indexer if it was created successfully
        if sanitized_indexer_name:
            # Update database with the sanitized names
            db = DBConnectionManager.get_instance()
            db.execute_update(
                "UPDATE ipx_documents SET index_name = ?, indexer_name = ?, status = ? WHERE id = ?",
                (sanitized_index_name, sanitized_indexer_name, "processing", document_id)
            )
            
            # Run the indexer
            indexer_client.run_indexer(sanitized_indexer_name)
            print(f"Started indexer: {sanitized_indexer_name}")
            
            # Start background thread to check status
            threading.Thread(
                target=check_indexer_status,
                args=(sanitized_indexer_name, document_id),
                daemon=True
            ).start()
        
        return True
    except Exception as e:
        print(f"Error triggering indexer: {str(e)}")
        traceback.print_exc()
        return False


def upload_file(file_path, unique_filename, original_filename , size, shat256, compound_id):
    try:

        # Create the BlobServiceClient
        blob_service_client = BlobServiceClient.from_connection_string(BLOB_CONNECTION_STRING)
        
        # Get a container client
        try:
            container_client = blob_service_client.get_container_client(CONTAINER_NAME)
            container_client.get_container_properties()  # Check if container exists
        except Exception:
            # Container doesn't exist, create it
            container_client = blob_service_client.create_container(CONTAINER_NAME)
        
        # Create a folder structure using the unique_filename as folder name
        folder_name = unique_filename
        blob_name = f"{folder_name}/{original_filename}"
        print(f"Creating blob in folder structure: {blob_name}")
        
        # Create a blob client for the file in its folder
        blob_client = container_client.get_blob_client(blob_name)
        
        # Detect content type
        content_settings = None
        if '.' in original_filename:
            extension = original_filename.rsplit('.', 1)[1].lower()
            content_type = None
            if extension in ['pdf']:
                content_type = 'application/pdf'
            elif extension in ['txt']:
                content_type = 'text/plain'
            elif extension in ['docx']:
                content_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            elif extension in ['doc']:
                content_type = 'application/msword'
            elif extension in ['xlsx']:
                content_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            elif extension in ['xls']:
                content_type = 'application/vnd.ms-excel'
            elif extension in ['csv']:
                content_type = 'text/csv'
                
            if content_type:
                content_settings = ContentSettings(content_type=content_type)
        
        # Upload the file
        with open(file_path, "rb") as data:
            blob_client.upload_blob(data, content_settings=content_settings, overwrite=True)
        
        # Get the blob URL
        account_url = blob_service_client.primary_endpoint
        blob_url = f"{account_url}/{CONTAINER_NAME}/{blob_name}"
        print(f"File uploaded to folder structure: {blob_url}")
        
        # Clean up the temporary file
        os.remove(file_path)

        # Insert into document db the file
        db = DBConnectionManager.get_instance()
        
        # Using execute_update for INSERT operations ensures proper transaction handling
        # We still need to get the inserted ID using OUTPUT clause in SQL Server
        result = db.select("""
        INSERT INTO ipx_documents
            (title, url, size, sha256, compound_id, index_name, indexer_name, status)
        OUTPUT INSERTED.id
        VALUES
            (?, ?, ?, ?, ?, ?, ?, ?)
        """, (original_filename, blob_url, size, shat256, compound_id, unique_filename, unique_filename, 'processing'))
        
        # Explicitly commit the transaction to ensure data is saved
        # (This is redundant since select should commit, but ensures data persistence)
        db.execute_update("COMMIT", ())
        
        # The result from OUTPUT should be a list with one dictionary containing the ID
        inserted_id = result[0]['id'] if result and len(result) > 0 else None
        
        print(f"Document inserted with ID: {inserted_id}")
        
        # Start indexer with proper parameters
        if inserted_id:
            # Generate search-friendly resource names
            indexer_name = f"idx-doc-{inserted_id}"
            index_name = f"index-doc-{inserted_id}"
            
            threading.Thread(
                target=trigger_indexer,
                args=(indexer_name, index_name, blob_url, inserted_id),
                daemon=True
            ).start()


        return create_response(
            status='success',
            data={
                'id': inserted_id,
                'message': f'File {original_filename} uploaded successfully to Azure Blob Storage',
                'file_name': original_filename,
                'blob_name': blob_name,
                'file_url': blob_url
            }
        )
    except Exception as e:
        # If there's an error, clean up and return error message
        if os.path.exists(file_path):
            os.remove(file_path)
        
        traceback.print_exc()  # Print detailed error for debugging
        
        return create_response(
            status='error',
            error={
                'code': 'BLOB_UPLOAD_ERROR',
                'message': f'Failed to upload to Azure Blob Storage: {str(e)}'
            },
            status_code=500
        )
    pass
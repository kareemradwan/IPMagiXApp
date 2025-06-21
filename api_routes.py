from flask import Blueprint, request, jsonify
from db_helper import DBConnectionManager
from utils import extract_compound_id, create_response, APIError

# Create Blueprint for API routes
api_bp = Blueprint('api', __name__, url_prefix='/api')

# Compounds endpoints
@api_bp.route('/compounds', methods=['GET'])
def get_compounds():
    """Get all compounds from database"""
    try:
        db = DBConnectionManager.get_instance()
        compounds = db.select("SELECT id, title FROM ipx_compounds ORDER BY id", ())
        return create_response(data=compounds)
    except Exception as e:
        return create_response(
            status='error',
            error={
                'code': 'DB_ERROR',
                'message': f'Failed to fetch compounds: {str(e)}'
            },
            status_code=500
        )

@api_bp.route('/compounds', methods=['POST'])
def create_compound():
    """Create a new compound"""
    try:
        data = request.get_json()
        if not data or 'title' not in data:
            return create_response(
                status='error',
                error={
                    'code': 'INVALID_REQUEST',
                    'message': 'Title is required'
                },
                status_code=400
            )
        
        title = data['title']
        db = DBConnectionManager.get_instance()
        
        # Insert the new compound
        result = db.select(
            "INSERT INTO ipx_compounds (title) OUTPUT INSERTED.id, INSERTED.title VALUES (?)",
            (title,)
        )
        
        # Extract the inserted compound
        if result and len(result) > 0:
            return create_response(data=result[0])
        else:
            return create_response(
                status='error',
                error={
                    'code': 'DB_ERROR',
                    'message': 'Failed to create compound'
                },
                status_code=500
            )
            
    except Exception as e:
        return create_response(
            status='error',
            error={
                'code': 'SERVER_ERROR',
                'message': f'An error occurred: {str(e)}'
            },
            status_code=500
        )

# Departments endpoints
@api_bp.route('/departments', methods=['GET'])
def get_departments():
    """Get departments for a compound"""
    try:
        # Extract compound_id from headers
        compound_id = extract_compound_id(request)
        
        db = DBConnectionManager.get_instance()
        departments = db.select(
            "SELECT id, title, compound_id FROM ipx_departments WHERE compound_id = ? ORDER BY id",
            (compound_id,)
        )
        
        return create_response(data=departments)
    except APIError as e:
        # APIErrors are already formatted properly by the decorator
        raise
    except Exception as e:
        return create_response(
            status='error',
            error={
                'code': 'DB_ERROR',
                'message': f'Failed to fetch departments: {str(e)}'
            },
            status_code=500
        )

@api_bp.route('/departments', methods=['POST'])
def create_department():
    """Create a new department"""
    try:
        # Extract compound_id from headers
        compound_id = extract_compound_id(request)
        
        data = request.get_json()
        if not data or 'title' not in data:
            return create_response(
                status='error',
                error={
                    'code': 'INVALID_REQUEST',
                    'message': 'Title is required'
                },
                status_code=400
            )
        
        title = data['title']
        db = DBConnectionManager.get_instance()
        
        # Insert the new department
        result = db.select(
            "INSERT INTO ipx_departments (title, compound_id) OUTPUT INSERTED.id, INSERTED.title, INSERTED.compound_id VALUES (?, ?)",
            (title, compound_id)
        )
        
        # Extract the inserted department
        if result and len(result) > 0:
            return create_response(data=result[0])
        else:
            return create_response(
                status='error',
                error={
                    'code': 'DB_ERROR',
                    'message': 'Failed to create department'
                },
                status_code=500
            )
            
    except APIError as e:
        # APIErrors are already formatted properly by the decorator
        raise
    except Exception as e:
        return create_response(
            status='error',
            error={
                'code': 'SERVER_ERROR',
                'message': f'An error occurred: {str(e)}'
            },
            status_code=500
        )

@api_bp.route('/departments/<int:department_id>', methods=['GET'])
def get_department(department_id):
    """Get details for a specific department"""
    try:
        # Extract compound_id from headers
        compound_id = extract_compound_id(request)
        
        db = DBConnectionManager.get_instance()
        departments = db.select(
            "SELECT id, title, compound_id FROM ipx_departments WHERE id = ? AND compound_id = ?",
            (department_id, compound_id)
        )
        
        if not departments or len(departments) == 0:
            return create_response(
                status='error',
                error={
                    'code': 'NOT_FOUND',
                    'message': f'Department with id {department_id} not found'
                },
                status_code=404
            )
        
        return create_response(data=departments[0])
    except APIError as e:
        # APIErrors are already formatted properly by the decorator
        raise
    except Exception as e:
        return create_response(
            status='error',
            error={
                'code': 'DB_ERROR',
                'message': f'Failed to fetch department: {str(e)}'
            },
            status_code=500
        )

# Documents endpoints
@api_bp.route('/documents', methods=['GET'])
def get_documents():
    """Get documents for a compound"""
    try:
        # Extract compound_id from headers
        compound_id = extract_compound_id(request)
        
        db = DBConnectionManager.get_instance()
        documents = db.select(
            "SELECT id, title, url, size, sha256, status, index_name, indexer_name FROM ipx_documents WHERE compound_id = ? ORDER BY id",
            (compound_id,)
        )
        
        return create_response(data=documents)
    except APIError as e:
        # APIErrors are already formatted properly by the decorator
        raise
    except Exception as e:
        return create_response(
            status='error',
            error={
                'code': 'DB_ERROR',
                'message': f'Failed to fetch documents: {str(e)}'
            },
            status_code=500
        )

# Department-Document relationship endpoints
@api_bp.route('/departments/<int:department_id>/documents', methods=['GET'])
def get_department_documents(department_id):
    """Get documents assigned to a department"""
    try:
        # Extract compound_id from headers
        compound_id = extract_compound_id(request)
        
        db = DBConnectionManager.get_instance()
        
        # First verify the department exists and belongs to the compound
        department = db.select(
            "SELECT id FROM ipx_departments WHERE id = ? AND compound_id = ?",
            (department_id, compound_id)
        )
        
        if not department or len(department) == 0:
            return create_response(
                status='error',
                error={
                    'code': 'NOT_FOUND',
                    'message': f'Department with id {department_id} not found'
                },
                status_code=404
            )
        
        # Get documents assigned to this department
        documents = db.select(
            """
            SELECT d.id, d.title, d.url, d.size, d.sha256, d.status, d.index_name, d.indexer_name
            FROM ipx_documents d
            JOIN ipx_departments_documents dd ON d.id = dd.document_id
            WHERE dd.compound_id = ? AND d.compound_id = ?
            ORDER BY d.id
            """,
            (department_id, compound_id)
        )
        
        return create_response(data=documents)
    except APIError as e:
        # APIErrors are already formatted properly by the decorator
        raise
    except Exception as e:
        return create_response(
            status='error',
            error={
                'code': 'DB_ERROR',
                'message': f'Failed to fetch department documents: {str(e)}'
            },
            status_code=500
        )

@api_bp.route('/departments/<int:department_id>/documents', methods=['POST'])
def assign_document_to_department(department_id):
    """Assign a document to a department"""
    try:
        # Extract compound_id from headers
        compound_id = extract_compound_id(request)
        
        data = request.get_json()
        if not data or 'documentId' not in data:
            return create_response(
                status='error',
                error={
                    'code': 'INVALID_REQUEST',
                    'message': 'Document ID is required'
                },
                status_code=400
            )
        
        document_id = data['documentId']
        db = DBConnectionManager.get_instance()
        
        # First verify both department and document exist
        department = db.select(
            "SELECT id FROM ipx_departments WHERE id = ? AND compound_id = ?",
            (department_id, compound_id)
        )
        
        if not department or len(department) == 0:
            return create_response(
                status='error',
                error={
                    'code': 'NOT_FOUND',
                    'message': f'Department with id {department_id} not found'
                },
                status_code=404
            )
            
        document = db.select(
            "SELECT id FROM ipx_documents WHERE id = ? AND compound_id = ?",
            (document_id, compound_id)
        )
        
        if not document or len(document) == 0:
            return create_response(
                status='error',
                error={
                    'code': 'NOT_FOUND',
                    'message': f'Document with id {document_id} not found'
                },
                status_code=404
            )
            
        # Check if the relationship already exists
        existing = db.select(
            "SELECT compound_id, document_id FROM ipx_departments_documents WHERE compound_id = ? AND document_id = ?",
            (department_id, document_id)
        )
        
        if existing and len(existing) > 0:
            return create_response(
                status='error',
                error={
                    'code': 'ALREADY_EXISTS',
                    'message': f'Document {document_id} is already assigned to department {department_id}'
                },
                status_code=409
            )
        
        # Create the relationship
        db.execute_update(
            "INSERT INTO ipx_departments_documents (compound_id, document_id) VALUES (?, ?)",
            (department_id, document_id)
        )
        
        return create_response(
            data={
                'message': f'Document {document_id} successfully assigned to department {department_id}'
            }
        )
            
    except APIError as e:
        # APIErrors are already formatted properly by the decorator
        raise
    except Exception as e:
        return create_response(
            status='error',
            error={
                'code': 'SERVER_ERROR',
                'message': f'An error occurred: {str(e)}'
            },
            status_code=500
        )

@api_bp.route('/departments/<int:department_id>/search', methods=['POST'])
def search_department_documents(department_id):
    """Search within documents assigned to a department"""
    try:
        # Extract compound_id from headers
        compound_id = extract_compound_id(request)
        
        data = request.get_json()
        if not data or 'query' not in data:
            return create_response(
                status='error',
                error={
                    'code': 'INVALID_REQUEST',
                    'message': 'Search query is required'
                },
                status_code=400
            )
        
        query = data['query']
        db = DBConnectionManager.get_instance()
        
        # First verify the department exists
        department = db.select(
            "SELECT id FROM ipx_departments WHERE id = ? AND compound_id = ?",
            (department_id, compound_id)
        )
        
        if not department or len(department) == 0:
            return create_response(
                status='error',
                error={
                    'code': 'NOT_FOUND',
                    'message': f'Department with id {department_id} not found'
                },
                status_code=404
            )
        
        # Get document IDs assigned to this department
        document_results = db.select(
            """
            SELECT document_id
            FROM ipx_departments_documents
            WHERE compound_id = ?
            """,
            (department_id,)
        )
        
        document_ids = [doc['document_id'] for doc in document_results]
        
        if not document_ids:
            return create_response(
                status='error',
                error={
                    'code': 'NO_DOCUMENTS',
                    'message': 'No documents found for this department'
                },
                status_code=404
            )
        
        # Import search function
        from open_ai_azure import search_documents
        
        # Perform search using the document IDs
        result, sources = search_documents(query, document_ids, compound_id)
        
        return jsonify({
            'success': True,
            'message': 'Search completed',
            'query': query,
            'answer': result,
            'sources': sources
        })
            
    except APIError as e:
        # APIErrors are already formatted properly by the decorator
        raise
    except Exception as e:
        return create_response(
            status='error',
            error={
                'code': 'SERVER_ERROR',
                'message': f'An error occurred: {str(e)}'
            },
            status_code=500
        )

# 🤖 IntelliBot – AI-Powered Q&A RAG Chatbot for Business Data

A full-stack chatbot web application for managing companies, departments, and documents with RAG search capabilities. Developed during the TechBridge Hackathon @ Microsoft (June 2025) organized by PAAM (Palestinians And Allies at Microsoft) in collaboration with Wasla Connect and for IPMagiX.

## 🎯 Objective
Build an intelligent chatbot that can:
- Understand natural language queries
- Retrieve data from internal files (PDF, Word, Excel, TXT, and more)
- Fetch records from a SQL Server database
- Provide accurate, contextual answers for different departments like HR, inventory, legal, and more.

## 🛠 Tech Stack
- Azure (AI Foundry, Blob storage, AI search, Azure Open AI, Azure functions) 
- C# / .NET 8
- MS SQL Server
- RESTful APIs
- Python
- Flask

## 📂 Project Structure 

- `/frontend`: React application source code
- `/api_routes.py`: API endpoints for the dashboard
- `/app.py`: Main Flask application
- `/upload_file.py`: Document upload and indexing functionality
- `/open_ai_azure.py`: Document search functionality with OpenAI
- `/db_helper.py`: Database connectivity

## 🚀 Features

- Compound management (list/create)
- Department management (list/create)
- Document management (list/upload/search)
- Department-document assignment
- Search within documents
- Search within department-specific documents

## 📌 Team Roles
- Documentation and presentation: Rana Ziara / Karam Saidam 
- Backend Developer: Yahya Shaikhoun / Kareem Redwan
- AI/NLP Architect: Karam Saidam
- Frontend/UI: Kareem Redwan
- Data Lead: Salma Sherif 

## 🖥️ Installation and Setup

### Prerequisites

- Python 3.8+
- Node.js 14+
- npm or yarn

### Backend Setup

1. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

### Frontend Setup

1. Navigate to the frontend directory:
   ```
   cd frontend
   ```

2. Install dependencies:
   ```
   npm install
   ```

3. Build the frontend:
   ```
   npm run build
   ```

## Running the Application

1. Start the Flask backend:
   ```
   flask run
   ```
   or
   ```
   python app.py
   ```

2. Access the application at http://localhost:5000

## API Endpoints

### Compounds
- `GET /api/compounds` - List all compounds
- `POST /api/compounds` - Create a new compound

### Departments
- `GET /api/departments` - List departments for the selected compound
- `POST /api/departments` - Create a new department
- `GET /api/departments/:id` - Get department details

### Documents
- `GET /api/documents` - List documents for the selected compound
- `POST /index-documents` - Upload a new document

### Department-Document Management
- `GET /api/departments/:id/documents` - Get documents assigned to a department
- `POST /api/departments/:id/documents` - Assign a document to a department

### Search
- `POST /search-documents` - Search across documents
- `POST /api/departments/:id/search` - Search within department documents


## ✅ Status
- [x] Research phase
- [x] Document parsing module
- [x] API endpoints
- [x] SQL integration
- [x] UI frontend
- [x] RAG
- [x] LLM Integration
- [x] Front end 




## 🚀 Notes

- The current implementation uses Azure services for document storage and search functionality.
- The `X-Compound-ID` header is required for most API calls and is managed automatically by the frontend.

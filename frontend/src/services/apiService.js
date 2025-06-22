import axios from 'axios';

// Create an axios instance with direct URL to Flask backend
const api = axios.create({
  baseURL: 'http://localhost:5000/api',  // Direct URL to Flask server on port 5001
  headers: {
    'Content-Type': 'application/json'
  },
  withCredentials: false  // Disable credentials to avoid CORS issues
});

// Interceptor to add compound ID header to all requests
api.interceptors.request.use(config => {
  // Log the request before it's sent
  console.log('Making API request to:', config.url, 'with method:', config.method);
  
  // Only add the compound header if it's not already set in the request config
  // This allows individual requests to override the global header if needed
  if (!config.headers['X-Compound-ID']) {
    const selectedCompound = localStorage.getItem('selectedCompound');
    if (selectedCompound) {
      const compound = JSON.parse(selectedCompound);
      config.headers['X-Compound-ID'] = compound.id;
      console.log('Adding X-Compound-ID header:', compound.id);
    } else {
      console.warn('No compound selected in localStorage');
    }
  } else {
    console.log('X-Compound-ID already set in request config:', config.headers['X-Compound-ID']);
  }
  
  return config;
}, error => {
  console.error('Request interceptor error:', error);
  return Promise.reject(error);
});

// Interceptor to handle response and log any errors
api.interceptors.response.use(
  response => {
    console.log('API response from:', response.config.url, 'status:', response.status);
    return response;
  },
  error => {
    console.error('API response error:', error);
    if (error.response) {
      console.error('Error status:', error.response.status);
      console.error('Error data:', error.response.data);
    }
    return Promise.reject(error);
  }
);

// Compounds
export const getCompounds = () => api.get('/compounds');
export const createCompound = (data) => api.post('/compounds', data);

// Departments
export const getDepartments = (compoundId) => 
  api.get('/departments', {
    headers: { 'X-Compound-ID': compoundId }
  });
export const createDepartment = (data, compoundId) => 
  api.post('/departments', data, {
    headers: { 'X-Compound-ID': compoundId }
  });
export const getDepartment = (id, compoundId) => 
  api.get(`/departments/${id}`, {
    headers: { 'X-Compound-ID': compoundId }
  });

// Documents
export const getDocuments = (compoundId) => 
  api.get('/documents', {
    headers: { 'X-Compound-ID': compoundId }
  });
export const uploadDocument = (formData, compoundId) => 
  api.post('/index-documents', formData, {
    headers: { 
      'X-Compound-ID': compoundId,
      'Content-Type': 'multipart/form-data'
    }
  });

// Department-Document Assignments
export const assignDocumentToDepartment = (departmentId, documentId, compoundId) => 
  api.post(`/departments/${departmentId}/documents`, 
    { documentId },
    { headers: { 'X-Compound-ID': compoundId } }
  );
export const getDepartmentDocuments = (departmentId, compoundId) => 
  api.get(`/departments/${departmentId}/documents`, {
    headers: { 'X-Compound-ID': compoundId }
  });

// Search
export const searchDocuments = (query, documentIds, compoundId) => 
  api.post('/search-documents', 
    { query, documentIds }, 
    { headers: { 'X-Compound-ID': compoundId } }
  );
export const searchDepartmentDocuments = (query, departmentId, compoundId) => 
  api.post(`/departments/${departmentId}/search`, 
    { query }, 
    { headers: { 'X-Compound-ID': compoundId } }
  );
export const searchDatabase = (query, tableName, columns, summaryAnswer) => 
  api.post('/search-database', 
    { query, table_name: tableName, columns, summary: summaryAnswer }
  );

// Utility to update the selected compound in localStorage
export const setSelectedCompoundInStorage = (compound) => {
  if (compound) {
    localStorage.setItem('selectedCompound', JSON.stringify(compound));
  }
};

export default api;

import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import {
  Button,
  Card,
  CardContent,
  CardHeader,
  IconButton,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Alert,
  Tabs,
  Tab,
  Box,
  TextField,
  Checkbox,
  FormControlLabel,
  CircularProgress,
  Typography
} from '@mui/material';
import RefreshIcon from '@mui/icons-material/Refresh';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import SearchIcon from '@mui/icons-material/Search';
import { getDocuments, uploadDocument, searchDocuments } from '../services/apiService';

// TabPanel component for tab content
function TabPanel(props) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`documents-tabpanel-${index}`}
      aria-labelledby={`documents-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ p: 3 }}>
          {children}
        </Box>
      )}
    </div>
  );
}

const DocumentsPage = (props) => {
  const location = useLocation();
  const navigate = useNavigate();
  
  // Extract selectedCompound from URL, props or localStorage
  const [selectedCompoundState, setSelectedCompoundState] = useState(null);
  
  // Effect to get selectedCompound from URL or props on mount and when location/props change
  useEffect(() => {
    // First priority: Check URL query parameters
    const queryParams = new URLSearchParams(location.search);
    const compoundIdFromUrl = queryParams.get('compoundId');
    
    if (compoundIdFromUrl) {
      console.log('Documents: Found compoundId in URL:', compoundIdFromUrl);
      // If we have the compound data from props, use it
      if (props.selectedCompound && props.selectedCompound.id == compoundIdFromUrl) {
        console.log('Documents: Using matching selectedCompound from props');
        setSelectedCompoundState(props.selectedCompound);
      } else {
        // We need to fetch the compound data by ID
        console.warn('Documents: No compound data available for the compoundId in URL');
        setError('No compound data available for the specified compound ID');
        // TODO: Could implement an API call to fetch the compound by ID here
      }
    } else if (props.selectedCompound) {
      // Second priority: Use props
      console.log('Documents: No compoundId in URL, using selectedCompound from props:', props.selectedCompound);
      setSelectedCompoundState(props.selectedCompound);
      // Update URL to include compound ID
      navigate(`/documents?compoundId=${props.selectedCompound.id}`, { replace: true });
    } else {
      console.warn('Documents: No selectedCompound available from URL or props');
      setError('Please select a compound first');
      // Redirect to home page to select a compound
      navigate('/', { replace: true });
    }
  }, [location.search, props.selectedCompound, navigate]);
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [tabValue, setTabValue] = useState(0);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState(null);
  const [searching, setSearching] = useState(false);
  const [selectedDocuments, setSelectedDocuments] = useState({});
  
  const fetchDocuments = React.useCallback(async () => {
    // Use either passed props or state compound
    const compound = selectedCompoundState;
    console.log('fetchDocuments called, compound:', compound);
    
    if (!compound) {
      setError('Please select a compound first');
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      setError('');
      const response = await getDocuments(compound.id);
      // Make sure we properly handle the response structure
      if (response && response.data) {
        if (response.data.data && Array.isArray(response.data.data)) {
          setDocuments(response.data.data);
        } else if (Array.isArray(response.data)) {
          setDocuments(response.data);
        } else {
          console.error('Unexpected data format:', response.data);
          setDocuments([]);
        }
      } else {
        setDocuments([]);
      }
      setLoading(false);
    } catch (error) {
      console.error('Error fetching documents:', error);
      setError('Failed to fetch documents. Please try again.');
      setLoading(false);
      setDocuments([]);
    }
  }, [selectedCompoundState]);

  useEffect(() => {
    if (selectedCompoundState) {
      fetchDocuments();
    }
  }, [selectedCompoundState, fetchDocuments]);

  const handleFileChange = (event) => {
    setFile(event.target.files[0]);
  };

  const handleFileUpload = async () => {
    if (!file || !selectedCompoundState) {
      return;
    }

    try {
      setUploading(true);
      setError('');
      
      const formData = new FormData();
      formData.append('file', file);
      
      await uploadDocument(formData, selectedCompoundState.id);
      
      setUploading(false);
      setFile(null);
      // Reset file input
      document.getElementById('document-file').value = '';
      
      // Refresh document list
      fetchDocuments();
      
    } catch (error) {
      console.error('Error uploading document:', error);
      setError('Failed to upload document. Please try again.');
      setUploading(false);
    }
  };

  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
  };
  
  const handleDocumentSelection = (documentId) => {
    setSelectedDocuments(prev => ({
      ...prev,
      [documentId]: !prev[documentId]
    }));
  };
  
  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      return;
    }
    
    try {
      setSearching(true);
      setError('');
      
      // Get selected document IDs
      const documentIds = Object.keys(selectedDocuments)
        .filter(id => selectedDocuments[id])
        .map(id => parseInt(id));
        
      const response = await searchDocuments(
        searchQuery, 
        documentIds.length > 0 ? documentIds : [], 
        selectedCompoundState.id
      );
      
      setSearchResults(response.data);
      setSearching(false);
    } catch (error) {
      console.error('Error performing search:', error);
      setError('Search failed. Please try again.');
      setSearching(false);
    }
  };

  return (
    <div>
      <Card>
        <CardHeader
          title="Documents"
          subheader={selectedCompoundState ? `Compound: ${selectedCompoundState.title}` : 'No compound selected'}
          action={
            <div className="action-buttons">
              <IconButton onClick={fetchDocuments} color="primary" title="Refresh">
                <RefreshIcon />
              </IconButton>
            </div>
          }
        />
        <CardContent>
          {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

          <Tabs value={tabValue} onChange={handleTabChange} sx={{ borderBottom: 1, borderColor: 'divider' }}>
            <Tab label="Document List" />
            <Tab label="Document Search" />
          </Tabs>

          <TabPanel value={tabValue} index={0}>
            {!selectedCompoundState ? (
              <Alert severity="info">Please select a compound from the dropdown above to view documents</Alert>
            ) : (
              <>
                <div className="file-input">
                  <input
                    accept="application/pdf,application/msword,application/vnd.openxmlformats-officedocument.wordprocessingml.document,.txt,.xlsx"
                    style={{ display: 'none' }}
                    id="document-file"
                    type="file"
                    onChange={handleFileChange}
                  />
                  <label htmlFor="document-file">
                    <Button
                      variant="contained"
                      component="span"
                      startIcon={<CloudUploadIcon />}
                      disabled={uploading}
                    >
                      Select Document
                    </Button>
                  </label>
                  {file && (
                    <Box sx={{ mt: 1, display: 'flex', alignItems: 'center' }}>
                      <span>{file.name}</span>
                      <Button
                        variant="contained"
                        color="primary"
                        onClick={handleFileUpload}
                        disabled={uploading}
                        sx={{ ml: 2 }}
                      >
                        {uploading ? <CircularProgress size={24} /> : 'Upload'}
                      </Button>
                    </Box>
                  )}
                </div>

                {loading ? (
                  <p>Loading documents...</p>
                ) : documents.length === 0 ? (
                  <p>No documents found for this compound. Upload one to get started.</p>
                ) : (
                  <TableContainer component={Paper}>
                    <Table>
                      <TableHead>
                        <TableRow>
                          <TableCell>ID</TableCell>
                          <TableCell>Title</TableCell>
                          <TableCell>Status</TableCell>
                          <TableCell>Size</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {documents.map((document) => (
                          <TableRow key={document.id}>
                            <TableCell>{document.id}</TableCell>
                            <TableCell>{document.title}</TableCell>
                            <TableCell>{document.status}</TableCell>
                            <TableCell>{(document.size / 1024).toFixed(2)} KB</TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </TableContainer>
                )}
              </>
            )}
          </TabPanel>

          <TabPanel value={tabValue} index={1}>
            {!selectedCompoundState ? (
              <Alert severity="info">Please select a compound from the dropdown above to search documents</Alert>
            ) : (
              <>
                <Box sx={{ mb: 3 }}>
                  <Typography variant="h6" sx={{ mb: 2 }}>Select documents to search</Typography>
                  
                  {loading ? (
                    <p>Loading documents...</p>
                  ) : documents.length === 0 ? (
                    <p>No documents available for search. Please upload documents first.</p>
                  ) : (
                    <Paper sx={{ p: 2, maxHeight: 200, overflow: 'auto' }}>
                      {documents.map(document => (
                        <FormControlLabel
                          key={document.id}
                          control={
                            <Checkbox 
                              checked={!!selectedDocuments[document.id]} 
                              onChange={() => handleDocumentSelection(document.id)}
                            />
                          }
                          label={document.title}
                        />
                      ))}
                    </Paper>
                  )}
                </Box>

                <Box className="search-form">
                  <TextField
                    label="Search Query"
                    variant="outlined"
                    fullWidth
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                  />
                  <Button
                    variant="contained"
                    startIcon={<SearchIcon />}
                    onClick={handleSearch}
                    disabled={searching || documents.length === 0}
                  >
                    {searching ? <CircularProgress size={24} /> : 'Search'}
                  </Button>
                </Box>

                {searchResults && (
                  <Box sx={{ mt: 3 }}>
                    <Typography variant="h6">Search Results</Typography>
                    <Paper sx={{ p: 2, mt: 1 }}>
                      <Typography variant="subtitle1">Query: {searchResults.query}</Typography>
                      <Typography variant="body1" sx={{ mt: 1 }}>Answer: {searchResults.answer}</Typography>
                      
                      {searchResults.sources && searchResults.sources.length > 0 && (
                        <Box sx={{ mt: 2 }}>
                          <Typography variant="subtitle1">Sources:</Typography>
                          <ul>
                            {searchResults.sources.map((source, index) => (
                              <li key={index}>{source}</li>
                            ))}
                          </ul>
                        </Box>
                      )}
                    </Paper>
                  </Box>
                )}
              </>
            )}
          </TabPanel>
        </CardContent>
      </Card>
    </div>
  );
};

export default DocumentsPage;

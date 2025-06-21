import React, { useState, useEffect } from 'react';
import { useParams, Link, useLocation, useNavigate } from 'react-router-dom';
import {
  Button,
  Card,
  CardContent,
  CardHeader,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControl,
  IconButton,
  InputLabel,
  MenuItem,
  Paper,
  Select,
  Tab,
  Tabs,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Typography,
  Box,
  Alert,
  CircularProgress
} from '@mui/material';
import RefreshIcon from '@mui/icons-material/Refresh';
import AddIcon from '@mui/icons-material/Add';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import SearchIcon from '@mui/icons-material/Search';
import { 
  getDepartment,
  getDepartmentDocuments,
  getDocuments,
  assignDocumentToDepartment,
  searchDepartmentDocuments
} from '../services/apiService';

// TabPanel component for tab content
function TabPanel(props) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`department-tabpanel-${index}`}
      aria-labelledby={`department-tab-${index}`}
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

const DepartmentDetailsPage = ({ selectedCompound }) => {
  const { departmentId } = useParams();
  const location = useLocation();
  const navigate = useNavigate();
  
  // Extract compound from URL, props or localStorage
  const [selectedCompoundState, setSelectedCompoundState] = useState(null);
  const [department, setDepartment] = useState(null);
  const [departmentDocuments, setDepartmentDocuments] = useState([]);
  const [availableDocuments, setAvailableDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [openDialog, setOpenDialog] = useState(false);
  const [selectedDocumentId, setSelectedDocumentId] = useState('');
  const [tabValue, setTabValue] = useState(0);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState(null);
  const [searching, setSearching] = useState(false);

  // Effect to get selectedCompound from URL or props
  useEffect(() => {
    // First priority: Check URL query parameters
    const queryParams = new URLSearchParams(location.search);
    const compoundIdFromUrl = queryParams.get('compoundId');
    console.log("########## ", selectedCompound);
    
    if (compoundIdFromUrl) {
      console.log('DepartmentDetails: Found compoundId in URL:', compoundIdFromUrl);
      // If we have the compound data from props, use it
      if (selectedCompound && selectedCompound.id == compoundIdFromUrl) {
        console.log('DepartmentDetails: Using matching selectedCompound from props');
        setSelectedCompoundState(selectedCompound);
      } else {
        // We need to fetch the compound data by ID
        console.warn('DepartmentDetails: No compound data available for the compoundId in URL');
        setError('No compound data available for the specified compound ID');
        // TODO: Could implement an API call to fetch the compound by ID here
      }
    } else if (selectedCompound) {
      // Second priority: Use props
      console.log('DepartmentDetails: No compoundId in URL, using selectedCompound from props:', selectedCompound);
      setSelectedCompoundState(selectedCompound);
      // Update URL to include compound ID
      navigate(`/departments/${departmentId}?compoundId=${selectedCompound.id}`, { replace: true });
    } else {
      console.warn('DepartmentDetails: No selectedCompound available from URL or props');
      setError('Please select a compound first');
      // Redirect to home page to select a compound
      navigate('/', { replace: true });
    }
  }, [location.search, selectedCompound, departmentId, navigate]);
  
  // First, define fetchDepartmentDocuments with useCallback to avoid dependency changes on every render
  const fetchDepartmentDocuments = React.useCallback(async () => {
    if (!departmentId || !selectedCompoundState) return;
    
    try {
      const docsResponse = await getDepartmentDocuments(departmentId, selectedCompoundState.id);
      // Handle response structure
      if (docsResponse && docsResponse.data) {
        if (docsResponse.data.data && Array.isArray(docsResponse.data.data)) {
          setDepartmentDocuments(docsResponse.data.data);
        } else if (Array.isArray(docsResponse.data)) {
          setDepartmentDocuments(docsResponse.data);
        } else {
          console.error('Unexpected department documents format:', docsResponse.data);
          setDepartmentDocuments([]);
        }
      } else {
        setDepartmentDocuments([]);
      }
    } catch (error) {
      console.error('Error fetching department documents:', error);
      setDepartmentDocuments([]);
    }
  }, [departmentId, selectedCompoundState]);
  
  // Then define fetchDepartmentDetails that depends on fetchDepartmentDocuments
  const fetchDepartmentDetails = React.useCallback(async () => {
    if (!selectedCompoundState) {
      setError('Please select a compound first');
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      setError('');
      
      // Get department details
      const deptResponse = await getDepartment(departmentId, selectedCompoundState.id);
      if (deptResponse && deptResponse.data) {
        if (deptResponse.data.data) {
          setDepartment(deptResponse.data.data);
        } else {
          setDepartment(deptResponse.data);
        }
      } else {
        setDepartment(null);
      }
      
      // Get department documents
      fetchDepartmentDocuments();
      
      // Get available documents for assignment
      const docsResponse = await getDocuments(selectedCompoundState.id);
      if (docsResponse && docsResponse.data) {
        if (docsResponse.data.data && Array.isArray(docsResponse.data.data)) {
          setAvailableDocuments(docsResponse.data.data);
        } else if (Array.isArray(docsResponse.data)) {
          setAvailableDocuments(docsResponse.data);
        } else {
          console.error('Unexpected documents data format:', docsResponse.data);
          setAvailableDocuments([]);
        }
      } else {
        setAvailableDocuments([]);
      }
      
      setLoading(false);
    } catch (error) {
      console.error('Error fetching department details:', error);
      setError('Failed to fetch department details. Please try again.');
      setLoading(false);
    }
  }, [selectedCompoundState, departmentId, fetchDepartmentDocuments]);

  useEffect(() => {
    if (selectedCompoundState && departmentId) {
      fetchDepartmentDetails();
    }
  }, [selectedCompoundState, departmentId, fetchDepartmentDetails]);

  // fetchDepartmentDocuments is already defined above with useCallback

  const handleAssignDocument = async () => {
    if (!selectedDocumentId || !departmentId || !selectedCompoundState) {
      return;
    }

    try {
      await assignDocumentToDepartment(departmentId, selectedDocumentId, selectedCompoundState.id);
      setOpenDialog(false);
      setSelectedDocumentId('');
      
      // Refresh department documents
      fetchDepartmentDocuments();
    } catch (error) {
      console.error('Error assigning document to department:', error);
      setError('Failed to assign document. Please try again.');
    }
  };

  const handleDocumentChange = (e) => {
    setSelectedDocumentId(e.target.value);
  };
  
  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      return;
    }
    
    try {
      setSearching(true);
      setError('');
      
      const response = await searchDepartmentDocuments(
        searchQuery,
        departmentId,
        selectedCompoundState.id
      );
      
      setSearchResults(response.data);
      setSearching(false);
    } catch (error) {
      console.error('Error performing department search:', error);
      setError('Search failed. Please try again.');
      setSearching(false);
    }
  };

  // Filter out documents already assigned to the department
  const unassignedDocuments = availableDocuments.filter(doc => 
    !departmentDocuments.some(deptDoc => deptDoc.id === doc.id)
  );

  return (
    <div>
      <Button
        component={Link}
        to="/departments"
        startIcon={<ArrowBackIcon />}
        sx={{ mb: 2 }}
      >
        Back to Departments
      </Button>
      
      <Card>
        <CardHeader
          title={department ? `Department: ${department.title}` : 'Department Details'}
          subheader={selectedCompoundState ? `Compound: ${selectedCompoundState.title}` : 'No compound selected'}
          action={
            <div className="action-buttons">
              <IconButton onClick={fetchDepartmentDetails} color="primary" title="Refresh">
                <RefreshIcon />
              </IconButton>
            </div>
          }
        />
        <CardContent>
          {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

          {loading ? (
            <p>Loading department details...</p>
          ) : !department ? (
            <Alert severity="error">Department not found or you don't have permission to view it</Alert>
          ) : (
            <>
              <Tabs value={tabValue} onChange={handleTabChange} sx={{ borderBottom: 1, borderColor: 'divider' }}>
                <Tab label="Department Documents" />
                <Tab label="Search Documents" />
              </Tabs>

              <TabPanel value={tabValue} index={0}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                  <Typography variant="h6">Documents</Typography>
                  <Button
                    variant="contained"
                    startIcon={<AddIcon />}
                    onClick={() => setOpenDialog(true)}
                    disabled={unassignedDocuments.length === 0}
                  >
                    Assign Document
                  </Button>
                </Box>

                {departmentDocuments.length === 0 ? (
                  <p>No documents assigned to this department yet.</p>
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
                        {departmentDocuments.map((document) => (
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
              </TabPanel>

              <TabPanel value={tabValue} index={1}>
                <Box className="search-form">
                  <TextField
                    label="Search within department documents"
                    variant="outlined"
                    fullWidth
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                  />
                  <Button
                    variant="contained"
                    startIcon={<SearchIcon />}
                    onClick={handleSearch}
                    disabled={searching || departmentDocuments.length === 0}
                  >
                    {searching ? <CircularProgress size={24} /> : 'Search'}
                  </Button>
                </Box>

                {departmentDocuments.length === 0 && (
                  <Alert severity="info" sx={{ mt: 2 }}>
                    No documents are assigned to this department yet. Please assign documents first.
                  </Alert>
                )}

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
              </TabPanel>
            </>
          )}
        </CardContent>
      </Card>

      {/* Assign Document Dialog */}
      <Dialog open={openDialog} onClose={() => setOpenDialog(false)}>
        <DialogTitle>Assign Document to Department</DialogTitle>
        <DialogContent>
          <FormControl fullWidth sx={{ mt: 1 }}>
            <InputLabel id="document-select-label">Select Document</InputLabel>
            <Select
              labelId="document-select-label"
              id="document-select"
              value={selectedDocumentId}
              onChange={handleDocumentChange}
              label="Select Document"
            >
              {unassignedDocuments.map((document) => (
                <MenuItem key={document.id} value={document.id}>
                  {document.title}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenDialog(false)}>Cancel</Button>
          <Button 
            onClick={handleAssignDocument} 
            variant="contained"
            disabled={!selectedDocumentId}
          >
            Assign
          </Button>
        </DialogActions>
      </Dialog>
    </div>
  );
};

export default DepartmentDetailsPage;

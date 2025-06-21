import React, { useState, useEffect } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import {
  Button,
  Card,
  CardContent,
  CardHeader,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  IconButton,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Alert
} from '@mui/material';
import RefreshIcon from '@mui/icons-material/Refresh';
import AddIcon from '@mui/icons-material/Add';
import VisibilityIcon from '@mui/icons-material/Visibility';
import { getDepartments, createDepartment } from '../services/apiService';

const DepartmentsPage = (props) => {
  const location = useLocation();
  const navigate = useNavigate();
  
  // Extract selectedCompound from URL, props or localStorage
  const [selectedCompoundState, setSelectedCompoundState] = useState(null);
  const [departments, setDepartments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [openDialog, setOpenDialog] = useState(false);
  const [newDepartment, setNewDepartment] = useState({ title: '' });
  const [error, setError] = useState('');

  // Effect to get selectedCompound from URL or props on mount and when location/props change
  useEffect(() => {
    // First priority: Check URL query parameters
    const queryParams = new URLSearchParams(location.search);
    const compoundIdFromUrl = queryParams.get('compoundId');
    
    if (compoundIdFromUrl) {
      // If we have the compound data from props, use it
      if (props.selectedCompound && props.selectedCompound.id == compoundIdFromUrl) {
        console.log('Using matching selectedCompound from props');
        setSelectedCompoundState(props.selectedCompound);
      } else {
        // We need to fetch the compound data by ID
        console.warn('No compound data available for the compoundId in URL');
        setError('No compound data available for the specified compound ID');
        // TODO: Could implement an API call to fetch the compound by ID here
      }
    } else if (props.selectedCompound) {
      // Second priority: Use props
      console.log('No compoundId in URL, using selectedCompound from props:', props.selectedCompound);
      setSelectedCompoundState(props.selectedCompound);
      // Update URL to include compound ID
      navigate(`/departments?compoundId=${props.selectedCompound.id}`, { replace: true });
    } else {
      console.warn('No selectedCompound available from URL or props');
      setError('Please select a compound first');
      // Redirect to home page to select a compound
      navigate('/', { replace: true });
    }
  }, [location.search, props.selectedCompound, navigate]);

  const fetchDepartments = React.useCallback(async () => {
    // Use either passed props or state compound
    const compound = selectedCompoundState;
    console.log('fetchDepartments called, compound:', compound);
    
    if (!compound) {
      setError('Please select a compound first');
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      setError('');
      console.log('Making API request with compound ID:', compound.id);
      const response = await getDepartments(compound.id);
      console.log('API response for departments:', response);
      
      // Make sure we properly handle the response structure
      if (response && response.data) {
        if (response.data.data && Array.isArray(response.data.data)) {
          setDepartments(response.data.data);
        } else if (Array.isArray(response.data)) {
          setDepartments(response.data);
        } else {
          console.error('Unexpected data format:', response.data);
          setDepartments([]);
        }
      } else {
        setDepartments([]);
      }
      setLoading(false);
    } catch (error) {
      console.error('Error fetching departments:', error);
      setError('Failed to fetch departments. Please try again.');
      setLoading(false);
      setDepartments([]);
    }
  }, [selectedCompoundState]);

  useEffect(() => {
    if (selectedCompoundState) {
      fetchDepartments();
    }
  }, [selectedCompoundState, fetchDepartments]);

  const handleCreateDepartment = async () => {
    if (!newDepartment.title.trim() || !selectedCompoundState) {
      return;
    }

    try {
      await createDepartment(newDepartment, selectedCompoundState.id);
      setOpenDialog(false);
      setNewDepartment({ title: '' });
      fetchDepartments();
    } catch (error) {
      console.error('Error creating department:', error);
      setError('Failed to create department. Please try again.');
    }
  };

  const handleChange = (e) => {
    setNewDepartment({ ...newDepartment, [e.target.name]: e.target.value });
  };

  return (
    <div>
      <Card>
        <CardHeader
          title="Departments"
          subheader={selectedCompoundState ? `Compound: ${selectedCompoundState.title}` : 'No compound selected'}
          action={
            <div className="action-buttons">
              <IconButton onClick={fetchDepartments} color="primary" title="Refresh">
                <RefreshIcon />
              </IconButton>
              <Button
                variant="contained"
                startIcon={<AddIcon />}
                onClick={() => setOpenDialog(true)}
                disabled={!selectedCompoundState}
              >
                Create Department
              </Button>
            </div>
          }
        />
        <CardContent>
          {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

          {loading ? (
            <p>Loading departments...</p>
          ) : !selectedCompoundState ? (
            <Alert severity="info">Please select a compound from the dropdown above to view departments</Alert>
          ) : departments.length === 0 ? (
            <p>No departments found for this compound. Create one to get started.</p>
          ) : (
            <TableContainer component={Paper}>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>ID</TableCell>
                    <TableCell>Title</TableCell>
                    <TableCell>Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {departments.map((department) => (
                    <TableRow key={department.id}>
                      <TableCell>{department.id}</TableCell>
                      <TableCell>{department.title}</TableCell>
                      <TableCell>
                        <Button
                          component={Link}
                          to={`/departments/${department.id}`}
                          variant="outlined"
                          size="small"
                          startIcon={<VisibilityIcon />}
                        >
                          View Details
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}
        </CardContent>
      </Card>

      {/* Create Department Dialog */}
      <Dialog open={openDialog} onClose={() => setOpenDialog(false)}>
        <DialogTitle>Create New Department</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            name="title"
            label="Department Title"
            type="text"
            fullWidth
            variant="outlined"
            value={newDepartment.title}
            onChange={handleChange}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenDialog(false)}>Cancel</Button>
          <Button onClick={handleCreateDepartment} variant="contained">Create</Button>
        </DialogActions>
      </Dialog>
    </div>
  );
};

export default DepartmentsPage;

import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
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
  TextField 
} from '@mui/material';
import RefreshIcon from '@mui/icons-material/Refresh';
import AddIcon from '@mui/icons-material/Add';
import { getCompounds, createCompound } from '../services/apiService';

const CompoundsPage = ({ refreshCompounds, handleCompoundChange }) => {
  const navigate = useNavigate();
  const [compounds, setCompounds] = useState([]);
  const [loading, setLoading] = useState(true);
  const [openDialog, setOpenDialog] = useState(false);
  const [newCompound, setNewCompound] = useState({ title: '' });

  const fetchCompounds = React.useCallback(async () => {
    try {
      setLoading(true);
      const response = await getCompounds();
      // Make sure we properly handle the response structure
      // Flask returns { status: 'success', data: [...] } from create_response
      if (response && response.data) {
        if (response.data.data && Array.isArray(response.data.data)) {
          setCompounds(response.data.data);
        } else if (Array.isArray(response.data)) {
          setCompounds(response.data);
        } else {
          console.error('Unexpected data format:', response.data);
          setCompounds([]);
        }
      } else {
        setCompounds([]);
      }
      setLoading(false);
    } catch (error) {
      console.error('Error fetching compounds:', error);
      setLoading(false);
      setCompounds([]);
    }
  }, []);
  
  // Add useEffect to call fetchCompounds when component mounts
  useEffect(() => {
    fetchCompounds();
  }, [fetchCompounds]);

  const handleCreateCompound = async () => {
    if (!newCompound.title.trim()) {
      return;
    }

    try {
      await createCompound(newCompound);
      setOpenDialog(false);
      setNewCompound({ title: '' });
      fetchCompounds();
      
      // Also refresh the compounds in the parent component for the dropdown
      if (refreshCompounds) {
        refreshCompounds();
      }
    } catch (error) {
      console.error('Error creating compound:', error);
    }
  };

  const handleChange = (e) => {
    setNewCompound({ ...newCompound, [e.target.name]: e.target.value });
  };

  return (
    <div>
      <Card>
        <CardHeader 
          title="Compounds" 
          action={
            <div className="action-buttons">
              <IconButton onClick={fetchCompounds} color="primary" title="Refresh">
                <RefreshIcon />
              </IconButton>
              <Button 
                variant="contained" 
                startIcon={<AddIcon />} 
                onClick={() => setOpenDialog(true)}
              >
                Create Compound
              </Button>
            </div>
          }
        />
        <CardContent>
          {loading ? (
            <p>Loading compounds...</p>
          ) : compounds.length === 0 ? (
            <p>No compounds found. Create one to get started.</p>
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
                  {compounds.map((compound) => (
                    <TableRow key={compound.id}>
                      <TableCell>{compound.id}</TableCell>
                      <TableCell>{compound.title}</TableCell>
                      <TableCell>
                        <div className="action-buttons">
                          <Button 
                            variant="outlined" 
                            size="small"
                            onClick={() => {
                              // Update selected compound in parent App component and localStorage
                              handleCompoundChange(compound);
                              navigate(`/departments?compoundId=${compound.id}`);
                            }}
                          >
                            Departments
                          </Button>
                          <Button 
                            variant="outlined" 
                            size="small"
                            onClick={() => {
                              // Update selected compound in parent App component and localStorage
                              handleCompoundChange(compound);
                              navigate(`/documents?compoundId=${compound.id}`);
                            }}
                          >
                            Documents
                          </Button>
                          <Button 
                            variant="outlined" 
                            size="small"
                            onClick={() => {
                              // Update selected compound in parent App component and localStorage
                              handleCompoundChange(compound);
                              navigate(`/database-search?compoundId=${compound.id}`);
                            }}
                          >
                            Database Search
                          </Button>
                          
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}
        </CardContent>
      </Card>

      {/* Create Compound Dialog */}
      <Dialog open={openDialog} onClose={() => setOpenDialog(false)}>
        <DialogTitle>Create New Compound</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            name="title"
            label="Compound Title"
            type="text"
            fullWidth
            variant="outlined"
            value={newCompound.title}
            onChange={handleChange}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenDialog(false)}>Cancel</Button>
          <Button onClick={handleCreateCompound} variant="contained">Create</Button>
        </DialogActions>
      </Dialog>
    </div>
  );
};

export default CompoundsPage;

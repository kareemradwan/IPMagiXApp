import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import AppBar from '@mui/material/AppBar';
import Toolbar from '@mui/material/Toolbar';
import Typography from '@mui/material/Typography';
import HomeIcon from '@mui/icons-material/Home';
import IconButton from '@mui/material/IconButton';
import Container from '@mui/material/Container';
import FormControl from '@mui/material/FormControl';
import InputLabel from '@mui/material/InputLabel';
import Select from '@mui/material/Select';
import MenuItem from '@mui/material/MenuItem';

// Pages
import CompoundsPage from './pages/CompoundsPage';
import DepartmentsPage from './pages/DepartmentsPage';
import DocumentsPage from './pages/DocumentsPage';
import DepartmentDetailsPage from './pages/DepartmentDetailsPage';
import DatabaseSearchPage from './pages/DatabaseSearchPage';

// API Service
import { getCompounds } from './services/apiService';

function App() {
  const [compounds, setCompounds] = useState([]);
  const [selectedCompound, setSelectedCompound] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Fetch compounds on initial load
    fetchCompounds();
  }, []);

  const fetchCompounds = async () => {
    try {
      setLoading(true);
      const response = await getCompounds();
      
      // Handle the Flask API response structure properly
      let compoundsData = [];
      if (response && response.data) {
        if (response.data.data && Array.isArray(response.data.data)) {
          compoundsData = response.data.data;
        } else if (Array.isArray(response.data)) {
          compoundsData = response.data;
        }
      }
      
      setCompounds(compoundsData);
      
      // Set the first compound as selected by default if available
      if (compoundsData.length > 0) {
        // Store the selected compound in state
        setSelectedCompound(compoundsData[0]);
      }
      
      setLoading(false);
    } catch (error) {
      console.error('Error fetching compounds:', error);
      setLoading(false);
    }
  };

  // This function can be called from the CompoundsPage
  const handleCompoundChange = (compound) => {
    setSelectedCompound(compound);
    // State is maintained via URL parameters, no localStorage needed
  };

  return (
    <Router>
      <AppBar position="fixed">
        <Toolbar>
          <IconButton
            edge="start"
            color="inherit"
            aria-label="home"
            component={Link}
            to="/"
            sx={{ mr: 2 }}
          >
            <HomeIcon />
          </IconButton>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            Document Management Dashboard
          </Typography>
          
          {/* Compound selection has been moved to CompoundsPage */}
        </Toolbar>
      </AppBar>

      <Container className="page-content">
        <Routes>
          <Route 
            path="/" 
            element={<CompoundsPage 
              refreshCompounds={fetchCompounds} 
              handleCompoundChange={handleCompoundChange} 
            />} 
          />
          <Route 
            path="/departments" 
            element={
              <DepartmentsPage 
                selectedCompound={selectedCompound} 
              />
            } 
          />
          <Route 
            path="/departments/:departmentId" 
            element={
              <DepartmentDetailsPage 
                selectedCompound={selectedCompound} 
              />
            } 
          />
          <Route 
            path="/documents" 
            element={
              <DocumentsPage 
                selectedCompound={selectedCompound} 
              />
            } 
          />
          <Route 
            path="/database-search" 
            element={
              <DatabaseSearchPage />
            } 
          />
        </Routes>
      </Container>
    </Router>
  );
}

export default App;

import React, { useState } from 'react';
import { 
  Button, 
  Card, 
  CardContent, 
  CardHeader, 
  FormControl,
  InputLabel,
  MenuItem,
  Paper,
  Select,
  Table, 
  TableBody, 
  TableCell, 
  TableContainer, 
  TableHead, 
  TableRow, 
  TextField 
} from '@mui/material';
import SearchIcon from '@mui/icons-material/Search';
import { searchDatabase } from '../services/apiService';

const DatabaseSearchPage = () => {
  const [query, setQuery] = useState('');
  const [tableName, setTableName] = useState('');
  const [columns, setColumns] = useState([]);
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  
  // List of available tables (in a real app, these would come from an API)
  const availableTables = [
        {key: 'ipx_b_products', label: 'Products'}, 
        {key: 'ipx_b_categories', label: 'Categories' }, 
        { key: 'ipx_b_suppliers', label: 'Suppliers'}];
  
  // Available columns for each table (in a real app, these would be dynamic)
  const availableColumns = {
    ipx_b_categories: ['id', 'name', 'created_at'],
    ipx_b_suppliers: ['id', 'name', 'contact_email', 'phone_number', 'address', 'created_at'],
    ipx_b_products: ['id', 'name', 'description', 'category_id', 'supplier_id', 'price', 'stock_quantity', 'created_at'],
  };
  
  const handleTableChange = (event) => {
    const selectedTable = event.target.value;
    setTableName(selectedTable);
    setColumns([]); // Reset columns when table changes
  };
  
  const handleSearch = async () => {
    if (!query || !tableName) {
      setError('Query and Table are required fields');
      return;
    }
    
    setLoading(true);
    setError('');
    try {
      const response = await searchDatabase(query, tableName, columns.length > 0 ? columns : undefined);
      if (response && response.data && response.data.results) {
        setResults(response.data.results);
      } else {
        setResults([]);
      }
    } catch (error) {
      console.error('Database search error:', error);
      setError('Failed to execute database search. Please try again.');
    } finally {
      setLoading(false);
    }
  };
  
  // Dynamically render table headers and rows based on results
  const renderTableHeaders = () => {
    if (results.length === 0) return null;
    
    // Get all unique keys from the results
    const headers = [...new Set(results.flatMap(obj => Object.keys(obj)))];
    
    return (
      <TableHead>
        <TableRow>
          {headers.map(header => (
            <TableCell key={header}>{header}</TableCell>
          ))}
        </TableRow>
      </TableHead>
    );
  };
  
  const renderTableRows = () => {
    if (results.length === 0) return null;
    
    const headers = [...new Set(results.flatMap(obj => Object.keys(obj)))];
    
    return (
      <TableBody>
        {results.map((row, index) => (
          <TableRow key={index}>
            {headers.map(header => (
              <TableCell key={`${index}-${header}`}>{row[header]?.toString() || '-'}</TableCell>
            ))}
          </TableRow>
        ))}
      </TableBody>
    );
  };
  
  return (
    <div>
      <Card>
        <CardHeader title="Database Search" />
        <CardContent>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            {/* Query input */}
            <TextField
              label="Query"
              variant="outlined"
              fullWidth
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Enter your database query"
              required
            />
            
            {/* Table selection */}
            <FormControl fullWidth variant="outlined" required>
              <InputLabel>Table</InputLabel>
              <Select
                value={tableName}
                onChange={handleTableChange}
                label="Table"
              >
                {availableTables.map(table => (
                  <MenuItem key={table.key} value={table.key}>{table.label}</MenuItem>
                ))}
              </Select>
            </FormControl>
            
            {/* Columns selection (only if table is selected) */}
            {tableName && (
              <FormControl fullWidth variant="outlined">
                <InputLabel>Columns (optional)</InputLabel>
                <Select
                  multiple
                  value={columns}
                  onChange={(e) => setColumns(e.target.value)}
                  label="Columns (optional)"
                  renderValue={(selected) => selected.join(', ')}
                >
                  {availableColumns[tableName]?.map(column => (
                    <MenuItem key={column} value={column}>{column}</MenuItem>
                  ))}
                </Select>
              </FormControl>
            )}
            
            {/* Error message */}
            {error && <div style={{ color: 'red' }}>{error}</div>}
            
            {/* Search button */}
            <Button 
              variant="contained" 
              color="primary" 
              startIcon={<SearchIcon />}
              onClick={handleSearch}
              disabled={loading}
            >
              {loading ? 'Searching...' : 'Search'}
            </Button>
          </div>
          
          {/* Results table */}
          {results.length > 0 && (
            <div style={{ marginTop: '30px' }}>
              <h3>Search Results</h3>
              <TableContainer component={Paper}>
                <Table>
                  {renderTableHeaders()}
                  {renderTableRows()}
                </Table>
              </TableContainer>
            </div>
          )}
          
          {/* No results message */}
          {!loading && results.length === 0 && query && !error && (
            <div style={{ marginTop: '30px', textAlign: 'center' }}>
              <p>No results found. Please try a different query or table.</p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default DatabaseSearchPage;

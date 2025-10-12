import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider } from './contexts/ThemeContext';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import Research from './pages/Research';
import StockAnalysis from './pages/StockAnalysis';
import RAGEvaluation from './pages/RAGEvaluation';
import SystemStatus from './pages/SystemStatus';

function App() {
  return (
    <ThemeProvider>
      <Router>
        <Layout>
          <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/research" element={<Research />} />
          <Route path="/stocks" element={<StockAnalysis />} />
          <Route path="/evaluation" element={<RAGEvaluation />} />
          <Route path="/status" element={<SystemStatus />} />
        </Routes>
      </Layout>
    </Router>
    </ThemeProvider>
  );
}

export default App;
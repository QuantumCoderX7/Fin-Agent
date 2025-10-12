import React, { useState } from 'react';
import { TrendingUp, Plus, X, BarChart3, Info } from 'lucide-react';
import { stockAPI, parseSSEData } from '../services/api';
import LoadingSpinner from '../components/LoadingSpinner';
import StockAnalysisResults from '../components/StockAnalysisResults';

const StockAnalysis = () => {
  const [formData, setFormData] = useState({
    symbols: [''],
    analysis_type: 'comprehensive',
    include_comparison: true,
    time_period: '1y'
  });
  
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamingContent, setStreamingContent] = useState('');
  const [progress, setProgress] = useState(null);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);
  const [stockInfo, setStockInfo] = useState({});

  const handleSymbolChange = (index, value) => {
    const newSymbols = [...formData.symbols];
    newSymbols[index] = value.toUpperCase();
    setFormData(prev => ({ ...prev, symbols: newSymbols }));
  };

  const addSymbol = () => {
    if (formData.symbols.length < 5) {
      setFormData(prev => ({ 
        ...prev, 
        symbols: [...prev.symbols, ''] 
      }));
    }
  };

  const removeSymbol = (index) => {
    if (formData.symbols.length > 1) {
      const newSymbols = formData.symbols.filter((_, i) => i !== index);
      setFormData(prev => ({ ...prev, symbols: newSymbols }));
    }
  };

  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  const fetchStockInfo = async (symbol) => {
    if (!symbol || symbol.length < 1) return;
    
    try {
      const response = await stockAPI.getStockInfo(symbol);
      setStockInfo(prev => ({ ...prev, [symbol]: response.data }));
    } catch (err) {
      console.error(`Failed to fetch info for ${symbol}:`, err);
    }
  };

  const handleSubmit = async (e, useStreaming = false) => {
    e.preventDefault();
    
    const validSymbols = formData.symbols.filter(s => s.trim().length > 0);
    if (validSymbols.length === 0) {
      setError('Please enter at least one stock symbol');
      return;
    }

    const requestData = {
      ...formData,
      symbols: validSymbols
    };

    setError(null);
    setResult(null);
    setStreamingContent('');
    setProgress(null);

    if (useStreaming) {
      await handleStreamingAnalysis(requestData);
    } else {
      await handleRegularAnalysis(requestData);
    }
  };

  const handleRegularAnalysis = async (requestData) => {
    try {
      setIsAnalyzing(true);
      const response = await stockAPI.analyze(requestData);
      setResult(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Analysis failed');
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleStreamingAnalysis = async (requestData) => {
    try {
      setIsStreaming(true);
      
      const response = await fetch('/api/v1/stocks/stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'text/event-stream',
        },
        body: JSON.stringify(requestData),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = parseSSEData(line.slice(6));
              
              if (data.progress) {
                setProgress(data.progress);
              }
              
              if (data.content) {
                setStreamingContent(prev => prev + data.content);
              }
              
              if (data.error) {
                setError(data.error);
                break;
              }
            } catch (parseError) {
              console.error('Error parsing SSE data:', parseError);
            }
          }
        }
      }
    } catch (err) {
      setError(err.message || 'Streaming analysis failed');
    } finally {
      setIsStreaming(false);
    }
  };

  const analysisTypes = [
    { value: 'basic', label: 'Basic Analysis' },
    { value: 'comprehensive', label: 'Comprehensive Analysis' },
    { value: 'technical', label: 'Technical Analysis' },
    { value: 'fundamental', label: 'Fundamental Analysis' }
  ];

  const timePeriods = [
    { value: '1m', label: '1 Month' },
    { value: '3m', label: '3 Months' },
    { value: '6m', label: '6 Months' },
    { value: '1y', label: '1 Year' },
    { value: '2y', label: '2 Years' }
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="card">
        <div className="flex items-center mb-4">
          <TrendingUp className="h-8 w-8 text-primary-600 mr-3" />
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Stock Market Analysis</h1>
            <p className="text-gray-600">Individual stock analysis and multi-stock comparison</p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Analysis Form */}
        <div className="lg:col-span-2">
          <form onSubmit={(e) => handleSubmit(e, false)} className="card">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Analysis Parameters</h2>
            
            {/* Stock Symbols */}
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Stock Symbols *
              </label>
              <div className="space-y-2">
                {formData.symbols.map((symbol, index) => (
                  <div key={index} className="flex items-center space-x-2">
                    <input
                      type="text"
                      value={symbol}
                      onChange={(e) => handleSymbolChange(index, e.target.value)}
                      onBlur={() => fetchStockInfo(symbol)}
                      placeholder="e.g., AAPL, GOOGL, MSFT"
                      className="input-field flex-1"
                      required={index === 0}
                    />
                    {formData.symbols.length > 1 && (
                      <button
                        type="button"
                        onClick={() => removeSymbol(index)}
                        className="p-2 text-red-500 hover:text-red-700 hover:bg-red-50 rounded-lg"
                      >
                        <X className="h-4 w-4" />
                      </button>
                    )}
                    {symbol && stockInfo[symbol] && (
                      <button
                        type="button"
                        onClick={() => {/* Show stock info modal */}}
                        className="p-2 text-blue-500 hover:text-blue-700 hover:bg-blue-50 rounded-lg"
                        title="View stock information"
                      >
                        <Info className="h-4 w-4" />
                      </button>
                    )}
                  </div>
                ))}
                
                {formData.symbols.length < 5 && (
                  <button
                    type="button"
                    onClick={addSymbol}
                    className="flex items-center text-primary-600 hover:text-primary-700 text-sm font-medium"
                  >
                    <Plus className="h-4 w-4 mr-1" />
                    Add Another Symbol
                  </button>
                )}
              </div>
              <p className="text-xs text-gray-500 mt-1">
                Add up to 5 stock symbols for analysis and comparison
              </p>
            </div>

            {/* Analysis Type */}
            <div className="mb-6">
              <label htmlFor="analysis_type" className="block text-sm font-medium text-gray-700 mb-2">
                Analysis Type
              </label>
              <select
                id="analysis_type"
                name="analysis_type"
                value={formData.analysis_type}
                onChange={handleInputChange}
                className="select-field"
              >
                {analysisTypes.map((type) => (
                  <option key={type.value} value={type.value}>
                    {type.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Time Period */}
            <div className="mb-6">
              <label htmlFor="time_period" className="block text-sm font-medium text-gray-700 mb-2">
                Time Period
              </label>
              <select
                id="time_period"
                name="time_period"
                value={formData.time_period}
                onChange={handleInputChange}
                className="select-field"
              >
                {timePeriods.map((period) => (
                  <option key={period.value} value={period.value}>
                    {period.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Include Comparison */}
            <div className="mb-6">
              <label className="flex items-center">
                <input
                  type="checkbox"
                  name="include_comparison"
                  checked={formData.include_comparison}
                  onChange={handleInputChange}
                  className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                />
                <span className="ml-2 text-sm text-gray-700">
                  Include comparative analysis (when multiple stocks selected)
                </span>
              </label>
            </div>

            {/* Error Display */}
            {error && (
              <div className="mb-6 p-4 bg-danger-50 border border-danger-200 rounded-lg">
                <p className="text-danger-800">{error.message || error}</p>
              </div>
            )}

            {/* Submit Buttons */}
            <div className="grid grid-cols-2 gap-4">
              <button
                type="submit"
                disabled={isAnalyzing || isStreaming}
                className={`btn-primary min-w-[140px] h-10 flex items-center justify-center ${
                  isAnalyzing ? 'cursor-not-allowed opacity-75' : ''
                }`}
              >
                <div className="flex items-center justify-center w-full">
                  {isAnalyzing ? (
                    <>
                      <LoadingSpinner size="sm" className="mr-2" />
                      <span>Analyzing...</span>
                    </>
                  ) : (
                    <span>Analyze Stocks</span>
                  )}
                </div>
              </button>
              
              <button
                type="button"
                onClick={(e) => handleSubmit(e, true)}
                disabled={isAnalyzing || isStreaming}
                className={`btn-secondary min-w-[140px] h-10 flex items-center justify-center ${
                  isStreaming ? 'cursor-not-allowed opacity-75' : ''
                }`}
              >
                <div className="flex items-center justify-center w-full">
                  {isStreaming ? (
                    <>
                      <LoadingSpinner size="sm" className="mr-2" />
                      <span>Streaming...</span>
                    </>
                  ) : (
                    <span>Stream Analysis</span>
                  )}
                </div>
              </button>
            </div>
          </form>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Stock Information */}
          {Object.keys(stockInfo).length > 0 && (
            <div className="card">
              <div className="flex items-center mb-4">
                <BarChart3 className="h-5 w-5 text-blue-500 mr-2" />
                <h3 className="text-lg font-semibold text-gray-900">Stock Information</h3>
              </div>
              
              <div className="space-y-4">
                {Object.entries(stockInfo).map(([symbol, info]) => (
                  <div key={symbol} className="p-3 bg-gray-50 rounded-lg">
                    <div className="flex items-center justify-between mb-2">
                      <h4 className="font-medium text-gray-900">{symbol}</h4>
                      <span className="text-sm text-gray-500">
                        ${info.current_price || 'N/A'}
                      </span>
                    </div>
                    <div className="text-xs text-gray-600">
                      <p>Market Cap: {info.market_cap || 'N/A'}</p>
                      <p>P/E Ratio: {info.pe_ratio || 'N/A'}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Popular Stocks */}
          <div className="card">
            <div className="flex items-center mb-4">
              <TrendingUp className="h-5 w-5 text-green-500 mr-2" />
              <h3 className="text-lg font-semibold text-gray-900">Popular Stocks</h3>
            </div>
            
            <div className="space-y-2">
              {['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA', 'NVDA'].map((symbol) => (
                <button
                  key={symbol}
                  onClick={() => {
                    if (!formData.symbols.includes(symbol)) {
                      const emptyIndex = formData.symbols.findIndex(s => s === '');
                      if (emptyIndex !== -1) {
                        handleSymbolChange(emptyIndex, symbol);
                      } else if (formData.symbols.length < 5) {
                        setFormData(prev => ({ 
                          ...prev, 
                          symbols: [...prev.symbols, symbol] 
                        }));
                      }
                    }
                  }}
                  className="w-full text-left p-2 text-sm bg-gray-50 hover:bg-primary-50 hover:text-primary-700 rounded-lg transition-colors duration-200"
                >
                  {symbol}
                </button>
              ))}
            </div>
          </div>

          {/* Analysis Tips */}
          <div className="card">
            <div className="flex items-center mb-4">
              <Info className="h-5 w-5 text-blue-500 mr-2" />
              <h3 className="text-lg font-semibold text-gray-900">Analysis Tips</h3>
            </div>
            
            <div className="space-y-3 text-sm text-gray-600">
              <p>• Use multiple symbols for comparative analysis</p>
              <p>• Comprehensive analysis provides detailed insights</p>
              <p>• Technical analysis focuses on price patterns</p>
              <p>• Fundamental analysis examines company financials</p>
              <p>• Longer time periods show better trends</p>
            </div>
          </div>
        </div>
      </div>

      {/* Results */}
      {(result || streamingContent || isStreaming) && (
        <div className="card">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">Stock Analysis Results</h2>
          {error ? (
            <div className="p-4 bg-danger-50 border border-danger-200 rounded-lg">
              <p className="text-danger-800">{error}</p>
            </div>
          ) : (
            <StockAnalysisResults
              result={result}
              isStreaming={isStreaming}
              streamingContent={streamingContent}
            />
          )}
          {(isAnalyzing || isStreaming) && progress !== null && (
            <div className="mt-4">
              <div className="w-full bg-gray-200 rounded-full h-2.5">
                <div
                  className="bg-primary-600 h-2.5 rounded-full transition-all duration-300"
                  style={{ width: `${Math.min(100, Math.max(0, progress))}%` }}
                />
              </div>
              <p className="text-sm text-gray-600 mt-2">
                Analysis in progress: {Math.round(progress)}%
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default StockAnalysis;
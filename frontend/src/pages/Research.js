import React, { useState, useEffect } from 'react';
import { Search, Lightbulb, Clock, Globe } from 'lucide-react';
import { researchAPI, parseSSEData } from '../services/api';
import LoadingSpinner from '../components/LoadingSpinner';
import StreamingOutput from '../components/StreamingOutput';
import ResearchResults from '../components/ResearchResults';

const Research = () => {
  const [formData, setFormData] = useState({
    topic: '',
    sources_limit: 5,
    include_outlook: true,
    focus_areas: [],
    time_horizon: 'medium'
  });
  
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamingContent, setStreamingContent] = useState('');
  const [progress, setProgress] = useState(null);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);
  const [suggestedTopics, setSuggestedTopics] = useState([]);
  const [loadingTopics, setLoadingTopics] = useState(false);

  useEffect(() => {
    fetchSuggestedTopics();
  }, []);

  const fetchSuggestedTopics = async () => {
    try {
      setLoadingTopics(true);
      const response = await researchAPI.getTopics('finance');
      setSuggestedTopics(response.data.suggested_topics || []);
    } catch (err) {
      console.error('Failed to fetch suggested topics:', err);
    } finally {
      setLoadingTopics(false);
    }
  };

  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  const handleFocusAreaChange = (area, checked) => {
    setFormData(prev => ({
      ...prev,
      focus_areas: checked 
        ? [...prev.focus_areas, area]
        : prev.focus_areas.filter(a => a !== area)
    }));
  };

  const handleTopicSelect = (topic) => {
    setFormData(prev => ({ ...prev, topic }));
  };

  const handleSubmit = async (e, useStreaming = false) => {
    e.preventDefault();
    
    if (!formData.topic.trim()) {
      setError('Please enter a research topic');
      return;
    }

    setError(null);
    setResult(null);
    setStreamingContent('');
    setProgress(null);

    if (useStreaming) {
      await handleStreamingAnalysis();
    } else {
      await handleRegularAnalysis();
    }
  };

  const handleRegularAnalysis = async () => {
    try {
      setIsAnalyzing(true);
      const response = await researchAPI.analyze(formData);
      setResult(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Analysis failed');
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleStreamingAnalysis = async () => {
    try {
      setIsStreaming(true);
      
      const response = await fetch('/api/v1/research/stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'text/event-stream',
        },
        body: JSON.stringify(formData),
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

  const focusAreas = [
    'Market Trends',
    'Regulatory Changes',
    'Economic Indicators',
    'Company Performance',
    'Industry Analysis',
    'Risk Assessment'
  ];

  const timeHorizons = [
    { value: 'short', label: 'Short-term (1-3 months)' },
    { value: 'medium', label: 'Medium-term (3-12 months)' },
    { value: 'long', label: 'Long-term (1+ years)' }
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="card">
        <div className="flex items-center mb-4">
          <Search className="h-8 w-8 text-primary-600 mr-3" />
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Financial Research Analysis</h1>
            <p className="text-gray-600">Comprehensive market research with multi-source data aggregation</p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Research Form */}
        <div className="lg:col-span-2">
          <form onSubmit={(e) => handleSubmit(e, false)} className="card">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Research Parameters</h2>
            
            {/* Topic Input */}
            <div className="mb-6">
              <label htmlFor="topic" className="block text-sm font-medium text-gray-700 mb-2">
                Research Topic *
              </label>
              <textarea
                id="topic"
                name="topic"
                value={formData.topic}
                onChange={handleInputChange}
                placeholder="Enter your financial research topic (e.g., 'Federal Reserve interest rate policy 2024', 'Electric vehicle market trends')"
                className="textarea-field h-24"
                required
              />
            </div>

            {/* Sources Limit */}
            <div className="mb-6">
              <label htmlFor="sources_limit" className="block text-sm font-medium text-gray-700 mb-2">
                Number of Sources (1-10)
              </label>
              <input
                type="number"
                id="sources_limit"
                name="sources_limit"
                value={formData.sources_limit}
                onChange={handleInputChange}
                min="1"
                max="10"
                className="input-field"
              />
            </div>

            {/* Focus Areas */}
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Focus Areas (Optional)
              </label>
              <div className="grid grid-cols-2 gap-2">
                {focusAreas.map((area) => (
                  <label key={area} className="flex items-center">
                    <input
                      type="checkbox"
                      checked={formData.focus_areas.includes(area)}
                      onChange={(e) => handleFocusAreaChange(area, e.target.checked)}
                      className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                    />
                    <span className="ml-2 text-sm text-gray-700">{area}</span>
                  </label>
                ))}
              </div>
            </div>

            {/* Time Horizon */}
            <div className="mb-6">
              <label htmlFor="time_horizon" className="block text-sm font-medium text-gray-700 mb-2">
                Time Horizon
              </label>
              <select
                id="time_horizon"
                name="time_horizon"
                value={formData.time_horizon}
                onChange={handleInputChange}
                className="select-field"
              >
                {timeHorizons.map((horizon) => (
                  <option key={horizon.value} value={horizon.value}>
                    {horizon.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Include Outlook */}
            <div className="mb-6">
              <label className="flex items-center">
                <input
                  type="checkbox"
                  name="include_outlook"
                  checked={formData.include_outlook}
                  onChange={handleInputChange}
                  className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                />
                <span className="ml-2 text-sm text-gray-700">Include future outlook section</span>
              </label>
            </div>

            {/* Error Display */}
            {error && (
              <div className="mb-6 p-4 bg-danger-50 border border-danger-200 rounded-lg">
                <p className="text-danger-800">{error.message || error}</p>
              </div>
            )}

            {/* Submit Buttons */}
            <div className="flex space-x-4">
              <button
                type="submit"
                disabled={isAnalyzing || isStreaming}
                className="btn-primary flex-1"
              >
                {isAnalyzing ? (
                  <>
                    <LoadingSpinner size="sm" />
                    <span className="ml-2">Analyzing...</span>
                  </>
                ) : (
                  'Analyze Topic'
                )}
              </button>
              
              <button
                type="button"
                onClick={(e) => handleSubmit(e, true)}
                disabled={isAnalyzing || isStreaming}
                className="btn-secondary flex-1"
              >
                {isStreaming ? (
                  <>
                    <LoadingSpinner size="sm" />
                    <span className="ml-2">Streaming...</span>
                  </>
                ) : (
                  'Stream Analysis'
                )}
              </button>
            </div>
          </form>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Suggested Topics */}
          <div className="card">
            <div className="flex items-center mb-4">
              <Lightbulb className="h-5 w-5 text-yellow-500 mr-2" />
              <h3 className="text-lg font-semibold text-gray-900">Suggested Topics</h3>
            </div>
            
            {loadingTopics ? (
              <LoadingSpinner size="sm" text="Loading topics..." />
            ) : (
              <div className="space-y-2">
                {suggestedTopics.slice(0, 5).map((topic, index) => (
                  <button
                    key={index}
                    onClick={() => handleTopicSelect(topic)}
                    className="w-full text-left p-3 text-sm bg-gray-50 hover:bg-primary-50 hover:text-primary-700 rounded-lg transition-colors duration-200"
                  >
                    {topic}
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Tips */}
          <div className="card">
            <div className="flex items-center mb-4">
              <Globe className="h-5 w-5 text-blue-500 mr-2" />
              <h3 className="text-lg font-semibold text-gray-900">Research Tips</h3>
            </div>
            
            <div className="space-y-3 text-sm text-gray-600">
              <div className="flex items-start">
                <Clock className="h-4 w-4 text-gray-400 mr-2 mt-0.5" />
                <p>Be specific with your research topic for better results</p>
              </div>
              <div className="flex items-start">
                <Clock className="h-4 w-4 text-gray-400 mr-2 mt-0.5" />
                <p>Use 5-7 sources for comprehensive analysis</p>
              </div>
              <div className="flex items-start">
                <Clock className="h-4 w-4 text-gray-400 mr-2 mt-0.5" />
                <p>Select relevant focus areas to narrow the scope</p>
              </div>
              <div className="flex items-start">
                <Clock className="h-4 w-4 text-gray-400 mr-2 mt-0.5" />
                <p>Streaming provides real-time progress updates</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Results */}
      {isStreaming ? (
        <StreamingOutput
          isStreaming={isStreaming}
          content={streamingContent}
          progress={progress}
          error={error}
          title="Research Analysis Results"
        />
      ) : result ? (
        <ResearchResults result={result} />
      ) : null}
    </div>
  );
};

export default Research;
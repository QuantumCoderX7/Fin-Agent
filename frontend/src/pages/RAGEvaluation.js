import React, { useState, useEffect } from 'react';
import { CheckCircle, FileText, Target, Info } from 'lucide-react';
import { evaluationAPI, parseSSEData } from '../services/api';
import LoadingSpinner from '../components/LoadingSpinner';
import StreamingOutput from '../components/StreamingOutput';

const RAGEvaluation = () => {
  const [formData, setFormData] = useState({
    query: '',
    response: '',
    context: [''],
    evaluation_criteria: []
  });
  
  const [isEvaluating, setIsEvaluating] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamingContent, setStreamingContent] = useState('');
  const [progress, setProgress] = useState(null);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);
  const [metrics, setMetrics] = useState(null);
  const [loadingMetrics, setLoadingMetrics] = useState(false);

  useEffect(() => {
    fetchEvaluationMetrics();
  }, []);

  const fetchEvaluationMetrics = async () => {
    try {
      setLoadingMetrics(true);
      const response = await evaluationAPI.getMetrics();
      setMetrics(response.data);
    } catch (err) {
      console.error('Failed to fetch evaluation metrics:', err);
    } finally {
      setLoadingMetrics(false);
    }
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleContextChange = (index, value) => {
    const newContext = [...formData.context];
    newContext[index] = value;
    setFormData(prev => ({ ...prev, context: newContext }));
  };

  const addContext = () => {
    if (formData.context.length < 10) {
      setFormData(prev => ({ 
        ...prev, 
        context: [...prev.context, ''] 
      }));
    }
  };

  const removeContext = (index) => {
    if (formData.context.length > 1) {
      const newContext = formData.context.filter((_, i) => i !== index);
      setFormData(prev => ({ ...prev, context: newContext }));
    }
  };

  const handleCriteriaChange = (criterion, checked) => {
    setFormData(prev => ({
      ...prev,
      evaluation_criteria: checked 
        ? [...prev.evaluation_criteria, criterion]
        : prev.evaluation_criteria.filter(c => c !== criterion)
    }));
  };

  const handleSubmit = async (e, useStreaming = false) => {
    e.preventDefault();
    
    if (!formData.query.trim() || !formData.response.trim()) {
      setError('Please provide both query and response');
      return;
    }

    const validContext = formData.context.filter(c => c.trim().length > 0);
    if (validContext.length === 0) {
      setError('Please provide at least one context document');
      return;
    }

    const requestData = {
      ...formData,
      context: validContext
    };

    setError(null);
    setResult(null);
    setStreamingContent('');
    setProgress(null);

    if (useStreaming) {
      await handleStreamingEvaluation(requestData);
    } else {
      await handleRegularEvaluation(requestData);
    }
  };

  const handleRegularEvaluation = async (requestData) => {
    try {
      setIsEvaluating(true);
      const response = await evaluationAPI.assess(requestData);
      setResult(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Evaluation failed');
    } finally {
      setIsEvaluating(false);
    }
  };

  const handleStreamingEvaluation = async (requestData) => {
    try {
      setIsStreaming(true);
      
      const response = await fetch('/api/v1/evaluation/stream', {
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
              
              if (data.status) {
                setStreamingContent(prev => prev + `\n**Status:** ${data.status}\n`);
              }
              
              if (data.evaluation_result) {
                setStreamingContent(prev => prev + `\n**Evaluation Results:**\n${JSON.stringify(data.evaluation_result, null, 2)}\n`);
              }
              
              if (data.recommendations) {
                setStreamingContent(prev => prev + `\n**Recommendations:**\n${JSON.stringify(data.recommendations, null, 2)}\n`);
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
      setError(err.message || 'Streaming evaluation failed');
    } finally {
      setIsStreaming(false);
    }
  };

  const defaultCriteria = [
    'faithfulness',
    'relevance',
    'completeness',
    'coherence',
    'source_attribution'
  ];

  const exampleQueries = [
    "What is the current outlook for the technology sector?",
    "How do rising interest rates affect real estate investments?",
    "What are the key factors driving cryptocurrency volatility?",
    "Explain the impact of inflation on consumer spending patterns"
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="card">
        <div className="flex items-center mb-4">
          <CheckCircle className="h-8 w-8 text-primary-600 mr-3" />
          <div>
            <h1 className="text-2xl font-bold text-gray-900">RAG Response Evaluation</h1>
            <p className="text-gray-600">Quality assessment of AI-generated financial content</p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Evaluation Form */}
        <div className="lg:col-span-2">
          <form onSubmit={(e) => handleSubmit(e, false)} className="card">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Evaluation Parameters</h2>
            
            {/* Query Input */}
            <div className="mb-6">
              <label htmlFor="query" className="block text-sm font-medium text-gray-700 mb-2">
                Original Query *
              </label>
              <textarea
                id="query"
                name="query"
                value={formData.query}
                onChange={handleInputChange}
                placeholder="Enter the original question or query that was asked..."
                className="textarea-field h-24"
                required
              />
            </div>

            {/* Response Input */}
            <div className="mb-6">
              <label htmlFor="response" className="block text-sm font-medium text-gray-700 mb-2">
                AI-Generated Response *
              </label>
              <textarea
                id="response"
                name="response"
                value={formData.response}
                onChange={handleInputChange}
                placeholder="Paste the AI-generated response that you want to evaluate..."
                className="textarea-field h-32"
                required
              />
            </div>

            {/* Context Documents */}
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Context Documents *
              </label>
              <div className="space-y-2">
                {formData.context.map((context, index) => (
                  <div key={index} className="flex items-start space-x-2">
                    <textarea
                      value={context}
                      onChange={(e) => handleContextChange(index, e.target.value)}
                      placeholder={`Context document ${index + 1}...`}
                      className="textarea-field h-20 flex-1"
                      required={index === 0}
                    />
                    {formData.context.length > 1 && (
                      <button
                        type="button"
                        onClick={() => removeContext(index)}
                        className="p-2 text-red-500 hover:text-red-700 hover:bg-red-50 rounded-lg mt-1"
                      >
                        <FileText className="h-4 w-4" />
                      </button>
                    )}
                  </div>
                ))}
                
                {formData.context.length < 10 && (
                  <button
                    type="button"
                    onClick={addContext}
                    className="flex items-center text-primary-600 hover:text-primary-700 text-sm font-medium"
                  >
                    <FileText className="h-4 w-4 mr-1" />
                    Add Context Document
                  </button>
                )}
              </div>
              <p className="text-xs text-gray-500 mt-1">
                Add the source documents or context that the AI used to generate the response
              </p>
            </div>

            {/* Evaluation Criteria */}
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Evaluation Criteria (Optional)
              </label>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {defaultCriteria.map((criterion) => (
                  <label key={criterion} className="flex items-center">
                    <input
                      type="checkbox"
                      checked={formData.evaluation_criteria.includes(criterion)}
                      onChange={(e) => handleCriteriaChange(criterion, e.target.checked)}
                      className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                    />
                    <span className="ml-2 text-sm text-gray-700 capitalize">
                      {criterion.replace('_', ' ')}
                    </span>
                  </label>
                ))}
              </div>
              <p className="text-xs text-gray-500 mt-1">
                Leave empty to use all default criteria
              </p>
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
                disabled={isEvaluating || isStreaming}
                className="btn-primary flex-1"
              >
                {isEvaluating ? (
                  <>
                    <LoadingSpinner size="sm" />
                    <span className="ml-2">Evaluating...</span>
                  </>
                ) : (
                  'Evaluate Response'
                )}
              </button>
              
              <button
                type="button"
                onClick={(e) => handleSubmit(e, true)}
                disabled={isEvaluating || isStreaming}
                className="btn-secondary flex-1"
              >
                {isStreaming ? (
                  <>
                    <LoadingSpinner size="sm" />
                    <span className="ml-2">Streaming...</span>
                  </>
                ) : (
                  'Stream Evaluation'
                )}
              </button>
            </div>
          </form>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Example Queries */}
          <div className="card">
            <div className="flex items-center mb-4">
              <Target className="h-5 w-5 text-green-500 mr-2" />
              <h3 className="text-lg font-semibold text-gray-900">Example Queries</h3>
            </div>
            
            <div className="space-y-2">
              {exampleQueries.map((query, index) => (
                <button
                  key={index}
                  onClick={() => setFormData(prev => ({ ...prev, query }))}
                  className="w-full text-left p-3 text-sm bg-gray-50 hover:bg-primary-50 hover:text-primary-700 rounded-lg transition-colors duration-200"
                >
                  {query}
                </button>
              ))}
            </div>
          </div>

          {/* Evaluation Metrics */}
          {metrics && (
            <div className="card">
              <div className="flex items-center mb-4">
                <Info className="h-5 w-5 text-blue-500 mr-2" />
                <h3 className="text-lg font-semibold text-gray-900">Evaluation Criteria</h3>
              </div>
              
              {loadingMetrics ? (
                <LoadingSpinner size="sm" text="Loading metrics..." />
              ) : (
                <div className="space-y-3 text-sm text-gray-600">
                  <div>
                    <h4 className="font-medium text-gray-900">Faithfulness</h4>
                    <p>How well the response is grounded in the provided context</p>
                  </div>
                  <div>
                    <h4 className="font-medium text-gray-900">Relevance</h4>
                    <p>How well the response addresses the original query</p>
                  </div>
                  <div>
                    <h4 className="font-medium text-gray-900">Completeness</h4>
                    <p>Whether the response covers all important aspects</p>
                  </div>
                  <div>
                    <h4 className="font-medium text-gray-900">Coherence</h4>
                    <p>Logical flow and readability of the response</p>
                  </div>
                  <div>
                    <h4 className="font-medium text-gray-900">Source Attribution</h4>
                    <p>Proper citation and reference to source materials</p>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Evaluation Tips */}
          <div className="card">
            <div className="flex items-center mb-4">
              <CheckCircle className="h-5 w-5 text-purple-500 mr-2" />
              <h3 className="text-lg font-semibold text-gray-900">Evaluation Tips</h3>
            </div>
            
            <div className="space-y-3 text-sm text-gray-600">
              <p>• Provide complete context documents for accurate evaluation</p>
              <p>• Include the exact query that was originally asked</p>
              <p>• Use streaming for real-time evaluation progress</p>
              <p>• Review all criteria scores for comprehensive assessment</p>
              <p>• Consider recommendations for improvement</p>
            </div>
          </div>
        </div>
      </div>

      {/* Results */}
      {(result || streamingContent || isStreaming) && (
        <StreamingOutput
          isStreaming={isStreaming}
          content={streamingContent || (result ? JSON.stringify(result, null, 2) : '')}
          progress={progress}
          error={error}
          title="RAG Evaluation Results"
        />
      )}
    </div>
  );
};

export default RAGEvaluation;
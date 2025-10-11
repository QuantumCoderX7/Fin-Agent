import React from 'react';
import { Clock, TrendingUp, AlertTriangle, Lightbulb } from 'lucide-react';
import ResearchDataGraphs from './ResearchDataGraphs';

const ResearchResults = ({ result }) => {
  if (!result) return null;

  const {
    headline,
    executive_summary,
    analysis,
    future_outlook,
    key_insights,
    sources,
    risk_factors,
    opportunities,
    generated_at,
    processing_time,
    confidence_score
  } = result;

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString();
  };

  return (
    <div className="space-y-6 bg-white rounded-lg shadow-lg p-6">
      {/* Header Section */}
      <div className="border-b pb-4">
        <h2 className="text-2xl font-bold text-gray-900">{headline}</h2>
        <div className="flex items-center gap-4 mt-2 text-sm text-gray-600">
          <div className="flex items-center gap-1">
            <Clock className="w-4 h-4" />
            <span>Generated: {formatDate(generated_at)}</span>
          </div>
          <div className="flex items-center gap-1">
            <TrendingUp className="w-4 h-4" />
            <span>Confidence: {(confidence_score * 100).toFixed(1)}%</span>
          </div>
        </div>
      </div>

      {/* Executive Summary */}
      <div className="bg-blue-50 p-4 rounded-lg">
        <h3 className="text-lg font-semibold text-blue-900 mb-2">Executive Summary</h3>
        <p className="text-blue-800">{executive_summary}</p>
      </div>

      {/* Main Analysis */}
      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-2">Detailed Analysis</h3>
        {analysis.split('\n\n').map((paragraph, index) => (
          <p key={index} className="text-gray-700 mb-4">
            {paragraph.trim()}
          </p>
        ))}
      </div>

      {/* Key Insights */}
      <div className="bg-green-50 p-4 rounded-lg">
        <h3 className="text-lg font-semibold text-green-900 mb-2">Key Insights</h3>
        <ul className="list-disc list-inside space-y-2">
          {key_insights.map((insight, index) => (
            <li key={index} className="text-green-800 leading-relaxed">
              <span className="align-middle">{insight}</span>
            </li>
          ))}
        </ul>
      </div>

      {/* Future Outlook */}
      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-2">Future Outlook</h3>
        <p className="text-gray-700">{future_outlook}</p>
      </div>

      {/* Data Visualization */}
      <ResearchDataGraphs result={result} />

      {/* Risks and Opportunities */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="bg-red-50 p-4 rounded-lg">
          <div className="flex items-center gap-2 mb-2">
            <AlertTriangle className="w-5 h-5 text-red-600" />
            <h3 className="text-lg font-semibold text-red-900">Risk Factors</h3>
          </div>
          <ul className="list-disc list-inside space-y-2">
            {risk_factors.map((risk, index) => (
              <li key={index} className="text-red-800">{risk}</li>
            ))}
          </ul>
        </div>
        <div className="bg-emerald-50 p-4 rounded-lg">
          <div className="flex items-center gap-2 mb-2">
            <Lightbulb className="w-5 h-5 text-emerald-600" />
            <h3 className="text-lg font-semibold text-emerald-900">Opportunities</h3>
          </div>
          <ul className="list-disc list-inside space-y-2">
            {opportunities.map((opportunity, index) => (
              <li key={index} className="text-emerald-800">{opportunity}</li>
            ))}
          </ul>
        </div>
      </div>

      {/* Sources */}
      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-2">Sources</h3>
        <div className="space-y-3">
          {sources.map((source, index) => (
            <div key={index} className="border-l-4 border-gray-300 pl-4">
              <a href={source.url} target="_blank" rel="noopener noreferrer" 
                 className="text-blue-600 hover:text-blue-800 font-medium">
                {source.title}
              </a>
              <p className="text-sm text-gray-600 mt-1">{source.excerpt}</p>
              <div className="text-xs text-gray-500 mt-1">
                Published: {formatDate(source.publication_date)} | 
                Relevance: {(source.relevance_score * 100).toFixed(0)}%
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Footer */}
      <div className="text-xs text-gray-500 border-t pt-4">
        Processing time: {processing_time.toFixed(2)}s
      </div>
    </div>
  );
};

export default ResearchResults;
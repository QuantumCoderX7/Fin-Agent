import React from 'react';
import { 
  TrendingUp, TrendingDown, AlertTriangle, 
  ArrowUp, ArrowDown, Zap, Target, 
  BarChart2, ShieldAlert, CheckCircle2
} from 'lucide-react';
import ValuationCharts from './ValuationCharts';
import ComparativeAnalysisSections from './ComparativeAnalysisSections';

const StockMetrics = ({ metrics }) => {
  if (!metrics) return null;

  const formatNumber = (num) => {
    if (num === null || num === undefined) return 'N/A';
    if (typeof num === 'number') {
      // Format large numbers (e.g., market cap) in billions/millions
      if (num > 1e9) return `$${(num / 1e9).toFixed(2)}B`;
      if (num > 1e6) return `$${(num / 1e6).toFixed(2)}M`;
      // Format percentages
      if (Math.abs(num) < 100 && metrics.symbol === 'dividend_yield') return `${num.toFixed(2)}%`;
      // Format prices
      return num.toLocaleString('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
      });
    }
    return String(num);
  };

  const metricList = [
    { key: 'current_price', label: 'Current Price', icon: BarChart2 },
    { key: 'market_cap', label: 'Market Cap', icon: Target },
    { key: 'pe_ratio', label: 'P/E Ratio', icon: BarChart2 },
    { key: 'eps', label: 'EPS', icon: Target },
    { key: 'dividend_yield', label: 'Dividend Yield', icon: Zap },
    { key: 'beta', label: 'Beta', icon: BarChart2 },
    { key: 'day_change', label: 'Day Change', icon: metrics.day_change >= 0 ? TrendingUp : TrendingDown },
    { key: 'volume', label: 'Volume', icon: BarChart2 },
    { key: 'year_high', label: '52-Week High', icon: ArrowUp },
    { key: 'year_low', label: '52-Week Low', icon: ArrowDown }
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
      {metricList.map(({ key, label, icon: Icon }) => (
        <div key={key} className="bg-gray-50 p-3 rounded-lg">
          <div className="flex items-center text-gray-600 mb-1">
            <Icon className="h-4 w-4 mr-1" />
            <span className="text-sm">{label}</span>
          </div>
          <div className={`text-lg font-semibold ${key === 'day_change' ? (metrics[key] >= 0 ? 'text-green-600' : 'text-red-600') : 'text-gray-900'}`}>
            {formatNumber(metrics[key])}
          </div>
        </div>
      ))}
    </div>
  );
};

const BulletList = ({ items, icon: Icon, color }) => {
  if (!items?.length) return null;
  
  return (
    <ul className="space-y-2">
      {items.map((item, index) => (
        <li key={index} className="flex items-start">
          <Icon className={`h-5 w-5 mr-2 mt-0.5 ${color}`} />
          <span className="text-gray-700">{item}</span>
        </li>
      ))}
    </ul>
  );
};

const StockAnalysisResults = ({ 
  result,
  isStreaming = false,
  streamingContent = ''
}) => {
  if (isStreaming) {
    return (
      <div className="card prose max-w-none">
        <div dangerouslySetInnerHTML={{ __html: streamingContent.replace(/\\n/g, '<br/>') }} />
      </div>
    );
  }

  if (!result?.analyses?.length) return null;

  const { analyses, comparison_summary } = result;

  return (
    <div className="space-y-8">
      {analyses.map((analysis) => (
        <div key={analysis.symbol} className="card">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-2xl font-bold text-gray-900">
                {analysis.company_name || analysis.symbol}
              </h2>
              <p className="text-gray-500">{analysis.symbol}</p>
            </div>
            <div className="flex items-center space-x-4">
              <div className={`px-4 py-2 rounded-lg font-medium ${
                analysis.recommendation === 'BUY' ? 'bg-green-100 text-green-800' :
                analysis.recommendation === 'SELL' ? 'bg-red-100 text-red-800' :
                'bg-yellow-100 text-yellow-800'
              }`}>
                {analysis.recommendation}
              </div>
              <div className={`px-4 py-2 rounded-lg font-medium ${
                analysis.risk_level === 'LOW' ? 'bg-green-100 text-green-800' :
                analysis.risk_level === 'HIGH' ? 'bg-red-100 text-red-800' :
                'bg-yellow-100 text-yellow-800'
              }`}>
                {analysis.risk_level} Risk
              </div>
            </div>
          </div>

          <StockMetrics metrics={analysis.metrics} />

          <div className="mt-6 space-y-6">
            {analysis.analysis_summary && (
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">Analysis Summary</h3>
                <p className="text-gray-700 whitespace-pre-wrap">{analysis.analysis_summary}</p>
              </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-3">Strengths</h3>
                <BulletList 
                  items={analysis.strengths} 
                  icon={CheckCircle2}
                  color="text-green-500"
                />
              </div>

              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-3">Weaknesses</h3>
                <BulletList 
                  items={analysis.weaknesses} 
                  icon={AlertTriangle}
                  color="text-red-500"
                />
              </div>

              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-3">Catalysts</h3>
                <BulletList 
                  items={analysis.catalysts} 
                  icon={Zap}
                  color="text-blue-500"
                />
              </div>
            </div>

            {analysis.target_price && (
              <div className="mt-4 flex items-center">
                <Target className="h-5 w-5 text-primary-500 mr-2" />
                <span className="font-medium text-gray-900">
                  Target Price: {new Intl.NumberFormat('en-US', { 
                    style: 'currency', 
                    currency: 'USD' 
                  }).format(analysis.target_price)}
                </span>
              </div>
            )}
          </div>
        </div>
      ))}

      {comparison_summary && analyses.length > 1 && (
        <div className="card">
          <div className="flex items-center space-x-3 mb-6">
            <BarChart2 className="h-6 w-6 text-primary-600" />
            <h2 className="text-2xl font-bold text-gray-900">Comparative Analysis</h2>
          </div>

          {/* Visual comparison section */}
          {analyses.length > 1 && (
            <div className="mb-8">
              <ValuationCharts analyses={analyses} />
            </div>
          )}

          {/* Text analysis sections */}
          <ComparativeAnalysisSections content={comparison_summary} />
        </div>
      )}

      {/* Quick Stats Summary */}
      {analyses.length > 1 && (
        <div className="mt-8 pt-8 border-t border-gray-200">
          <h4 className="text-lg font-semibold text-gray-900 mb-4">Quick Comparison</h4>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Stock</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Price</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">P/E Ratio</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Market Cap</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Risk</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Target</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {analyses.map((analysis) => (
                  <tr key={analysis.symbol} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="font-medium text-gray-900">{analysis.symbol}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {new Intl.NumberFormat('en-US', {
                        style: 'currency',
                        currency: 'USD'
                      }).format(analysis.metrics.current_price)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {analysis.metrics.pe_ratio?.toFixed(2) || 'N/A'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {analysis.metrics.market_cap > 1e9
                        ? `$${(analysis.metrics.market_cap / 1e9).toFixed(2)}B`
                        : analysis.metrics.market_cap > 1e6
                        ? `$${(analysis.metrics.market_cap / 1e6).toFixed(2)}M`
                        : 'N/A'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                        analysis.risk_level === 'LOW' ? 'bg-green-100 text-green-800' :
                        analysis.risk_level === 'HIGH' ? 'bg-red-100 text-red-800' :
                        'bg-yellow-100 text-yellow-800'
                      }`}>
                        {analysis.risk_level}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {analysis.target_price
                        ? new Intl.NumberFormat('en-US', {
                            style: 'currency',
                            currency: 'USD'
                          }).format(analysis.target_price)
                        : 'N/A'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};

export default StockAnalysisResults;
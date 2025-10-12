import React from 'react';
import { BarChart2, TrendingUp, LineChart } from 'lucide-react';

const ValuationCharts = ({ analyses }) => {
  // Sort and prepare data for P/E ratio comparison
  const peData = analyses
    .map(a => ({
      symbol: a.symbol,
      pe: a.metrics.pe_ratio,
      color: a.metrics.pe_ratio > 50 ? 'bg-red-500' : 
             a.metrics.pe_ratio > 30 ? 'bg-yellow-500' : 
             'bg-green-500'
    }))
    .sort((a, b) => a.pe - b.pe);

  // Sort and prepare data for Market Cap comparison
  const mcapData = analyses
    .map(a => ({
      symbol: a.symbol,
      mcap: a.metrics.market_cap,
      formatted: a.metrics.market_cap > 1e12 
        ? `$${(a.metrics.market_cap / 1e12).toFixed(2)}T`
        : `$${(a.metrics.market_cap / 1e9).toFixed(2)}B`
    }))
    .sort((a, b) => b.mcap - a.mcap);

  return (
    <div className="space-y-6">
      <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-100">
        <h3 className="text-lg font-semibold text-gray-900 mb-2 flex items-center">
          <LineChart className="h-5 w-5 mr-2 text-primary-500" />
          Price-to-Earnings (P/E) Ratio
        </h3>
        <p className="text-sm text-gray-600 mb-4">
          Comparing valuation multiples across companies
        </p>
        <div className="space-y-3">
          {peData.map(({ symbol, pe, color }) => (
            <div key={symbol} className="relative">
              <div className="flex justify-between text-sm mb-1">
                <span className="font-medium">{symbol}</span>
                <span className={pe > 50 ? 'text-red-600' : pe > 30 ? 'text-yellow-600' : 'text-green-600'}>
                  {pe?.toFixed(2) || 'N/A'}
                </span>
              </div>
              <div className="h-2 w-full bg-gray-100 rounded">
                <div 
                  className={`h-2 rounded ${color} transition-all duration-500`}
                  style={{ 
                    width: `${Math.min(100, (pe / Math.max(...peData.map(d => d.pe))) * 100)}%`
                  }}
                />
              </div>
            </div>
          ))}
        </div>
        <div className="mt-4 text-xs text-gray-500 flex items-center gap-4">
          <div className="flex items-center">
            <div className="w-3 h-3 rounded bg-green-500 mr-1" />
            &lt;30x P/E
          </div>
          <div className="flex items-center">
            <div className="w-3 h-3 rounded bg-yellow-500 mr-1" />
            30-50x P/E
          </div>
          <div className="flex items-center">
            <div className="w-3 h-3 rounded bg-red-500 mr-1" />
            &gt;50x P/E
          </div>
        </div>
      </div>

      <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-100">
        <h3 className="text-lg font-semibold text-gray-900 mb-2 flex items-center">
          <BarChart2 className="h-5 w-5 mr-2 text-primary-500" />
          Market Capitalization
        </h3>
        <p className="text-sm text-gray-600 mb-4">
          Relative size and market value comparison
        </p>
        <div className="space-y-3">
          {mcapData.map(({ symbol, mcap, formatted }) => (
            <div key={symbol} className="relative">
              <div className="flex justify-between text-sm mb-1">
                <span className="font-medium">{symbol}</span>
                <span>{formatted}</span>
              </div>
              <div className="h-2 w-full bg-gray-100 rounded">
                <div 
                  className="h-2 rounded bg-blue-500 transition-all duration-500"
                  style={{ 
                    width: `${(mcap / Math.max(...mcapData.map(d => d.mcap))) * 100}%`
                  }}
                />
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Additional Metrics Table */}
      <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-100">
        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
          <TrendingUp className="h-5 w-5 mr-2 text-primary-500" />
          Key Valuation Metrics
        </h3>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead>
              <tr className="bg-gray-50">
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Stock</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">P/E Ratio</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">EPS</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Div. Yield</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Beta</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {analyses.map((analysis) => (
                <tr key={analysis.symbol} className="hover:bg-gray-50">
                  <td className="px-4 py-3 whitespace-nowrap font-medium text-gray-900">
                    {analysis.symbol}
                  </td>
                  <td className={`px-4 py-3 text-right whitespace-nowrap ${
                    analysis.metrics.pe_ratio > 50 ? 'text-red-600' :
                    analysis.metrics.pe_ratio > 30 ? 'text-yellow-600' :
                    'text-green-600'
                  }`}>
                    {analysis.metrics.pe_ratio?.toFixed(2) || 'N/A'}
                  </td>
                  <td className="px-4 py-3 text-right whitespace-nowrap text-gray-900">
                    ${analysis.metrics.eps?.toFixed(2) || 'N/A'}
                  </td>
                  <td className="px-4 py-3 text-right whitespace-nowrap text-gray-900">
                    {analysis.metrics.dividend_yield
                      ? `${(analysis.metrics.dividend_yield * 100).toFixed(2)}%`
                      : 'N/A'}
                  </td>
                  <td className="px-4 py-3 text-right whitespace-nowrap text-gray-900">
                    {analysis.metrics.beta?.toFixed(2) || 'N/A'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default ValuationCharts;
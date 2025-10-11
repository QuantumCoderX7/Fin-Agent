import React from 'react';
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell
} from 'recharts';

const COLORS = {
  primary: ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8'],
  success: ['#10B981', '#34D399', '#6EE7B7', '#A7F3D0', '#D1FAE5'],
  warning: ['#F59E0B', '#FBBF24', '#FCD34D', '#FDE68A', '#FEF3C7'],
  info: ['#3B82F6', '#60A5FA', '#93C5FD', '#BFDBFE', '#DBEAFE']
};

const formatValue = (value) => {
  if (value >= 1000) {
    return `${(value / 1000).toFixed(1)}K`;
  }
  return value;
};

const formatPercentage = (value) => `${value}%`;

const ResearchDataGraphs = ({ result }) => {
  if (!result) return null;

  // Check if result contains visualization data
  const hasVisualizationData = result.visualization_data && 
    (result.visualization_data.charts || result.visualization_data.metrics);

  // If no visualization data is available, don't render anything
  if (!hasVisualizationData) {
    return null;
  }

  // Extract visualization data from result
  const { charts = [], metrics = [] } = result.visualization_data || {};

  return (
    <div className="space-y-8 bg-white rounded-lg shadow-lg p-6">
      <h2 className="text-2xl font-bold text-gray-900 mb-6">Market Analysis Visualization</h2>

      {/* Render dynamic charts based on result data */}
      {charts.map((chart, index) => {
        if (chart.type === 'pie' && chart.data) {
          return (
            <div key={index}>
              <h3 className="text-lg font-semibold text-gray-900 mb-4">{chart.title}</h3>
              <div className="h-[300px]">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={chart.data}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ name, value }) => `${name} (${formatPercentage(value)})`}
                      outerRadius={100}
                      innerRadius={60}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {chart.data.map((entry, idx) => (
                        <Cell key={`cell-${idx}`} fill={COLORS.primary[idx % COLORS.primary.length]} />
                      ))}
                    </Pie>
                    <Tooltip formatter={formatPercentage} />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </div>
          );
        }

        if (chart.type === 'line' && chart.data) {
          return (
            <div key={index}>
              <h3 className="text-lg font-semibold text-gray-900 mb-4">{chart.title}</h3>
              <div className="h-[300px]">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart
                    data={chart.data}
                    margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey={chart.xKey || 'x'} />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Line
                      type="monotone"
                      dataKey={chart.yKey || 'y'}
                      stroke={COLORS.info[0]}
                      name={chart.yLabel || 'Value'}
                      strokeWidth={2}
                      dot={{ fill: COLORS.info[0], strokeWidth: 2 }}
                      activeDot={{ r: 8 }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
              {chart.note && <p className="text-sm text-gray-600 mt-2">{chart.note}</p>}
            </div>
          );
        }

        if (chart.type === 'bar' && chart.data) {
          return (
            <div key={index}>
              <h3 className="text-lg font-semibold text-gray-900 mb-4">{chart.title}</h3>
              <div className="h-[300px]">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart
                    data={chart.data}
                    margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey={chart.xKey || 'category'} />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Bar
                      dataKey={chart.yKey || 'value'}
                      fill={COLORS.success[0]}
                      name={chart.yLabel || 'Value'}
                      radius={[4, 4, 0, 0]}
                    >
                      {chart.data.map((entry, idx) => (
                        <Cell key={`cell-${idx}`} fill={COLORS.success[idx % COLORS.success.length]} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          );
        }

        return null;
      })}

      {/* Display metrics if available */}
      {metrics.length > 0 && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {metrics.map((metric, index) => (
            <div key={index} className="bg-gray-50 p-4 rounded-lg">
              <p className="text-sm text-gray-600">{metric.label}</p>
              <p className="text-2xl font-bold text-gray-900">{metric.value}</p>
              {metric.change && (
                <p className={`text-sm ${metric.change > 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {metric.change > 0 ? '+' : ''}{metric.change}%
                </p>
              )}
            </div>
          ))}
        </div>
      )}

      {result.visualization_data?.notes && (
        <div className="text-sm text-gray-600 mt-4 space-y-1">
          {result.visualization_data.notes.map((note, index) => (
            <p key={index}>* {note}</p>
          ))}
        </div>
      )}
    </div>
  );
};

export default ResearchDataGraphs;
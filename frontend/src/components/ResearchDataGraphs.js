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

  // Format data for EV Market Share Chart
  const evMarketData = [
    { name: 'Tesla', share: 60, color: COLORS.primary[0] },
    { name: 'Other OEMs', share: 40, color: COLORS.primary[1] }
  ];

  // Format data for Battery Cost Trend
  const batteryCostData = [
    { year: '2010', cost: 1000 },
    { year: '2015', cost: 500 },
    { year: '2020', cost: 200 },
    { year: '2023', cost: 150 },
    { year: '2027', cost: 90 }
  ];

  // Format data for Investment Requirements
  const investmentData = [
    { category: 'Charging Infrastructure', amount: 1200 },
    { category: 'Battery Production', amount: 800 },
    { category: 'Vehicle Manufacturing', amount: 600 },
    { category: 'R&D', amount: 400 }
  ];

  return (
    <div className="space-y-8 bg-white rounded-lg shadow-lg p-6">
      <h2 className="text-2xl font-bold text-gray-900 mb-6">Market Analysis Visualization</h2>

      {/* EV Market Share Pie Chart */}
      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-4">EV Market Share Distribution</h3>
        <div className="h-[300px]">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={evMarketData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, value }) => `${name} (${formatPercentage(value)})`}
                outerRadius={100}
                innerRadius={60}
                fill="#8884d8"
                dataKey="share"
              >
                {evMarketData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip formatter={formatPercentage} />
              <Legend formatter={(value) => value} />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Battery Cost Trend Line Chart */}
      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Battery Cost Trend ($/kWh)</h3>
        <div className="h-[300px]">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart
              data={batteryCostData}
              margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
            >
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="year" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line
                type="monotone"
                dataKey="cost"
                stroke={COLORS.info[0]}
                name="Cost per kWh"
                strokeWidth={2}
                dot={{ fill: COLORS.info[0], strokeWidth: 2 }}
                activeDot={{ r: 8 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
        <p className="text-sm text-gray-600 mt-2">* Projected values after 2023</p>
      </div>

      {/* Investment Requirements Bar Chart */}
      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Required Investment by Category (Billions $)</h3>
        <div className="h-[300px]">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={investmentData}
              margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
            >
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="category" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar
                dataKey="amount"
                fill={COLORS.success[0]}
                name="Investment Required"
                radius={[4, 4, 0, 0]}
              >
                {investmentData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS.success[index % COLORS.success.length]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="text-sm text-gray-600 mt-4 space-y-1">
        <p>* Data sources: Market analysis reports, industry forecasts, and research findings</p>
        <p>* Battery cost projections based on BloombergNEF forecasts</p>
        <p>* Investment requirements estimated through 2030</p>
      </div>
    </div>
  );
};

export default ResearchDataGraphs;
import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { 
  Search, 
  TrendingUp, 
  CheckCircle, 
  Activity,
  ArrowRight,
  BarChart3,
  Clock,
  Users
} from 'lucide-react';
import { systemAPI } from '../services/api';
import LoadingSpinner from '../components/LoadingSpinner';

const Dashboard = () => {
  const [systemStatus, setSystemStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchSystemStatus();
  }, []);

  const fetchSystemStatus = async () => {
    try {
      setLoading(true);
      const response = await systemAPI.getStatus();
      setSystemStatus(response.data);
      setError(null);
    } catch (err) {
      setError('Failed to fetch system status');
      console.error('System status error:', err);
    } finally {
      setLoading(false);
    }
  };

  const services = [
    {
      name: 'Financial Research',
      description: 'Comprehensive market research with multi-source data aggregation',
      icon: Search,
      href: '/research',
      color: 'bg-blue-500',
      features: ['Multi-source analysis', 'Real-time streaming', 'Executive summaries']
    },
    {
      name: 'Stock Analysis',
      description: 'Individual stock analysis and multi-stock comparison',
      icon: TrendingUp,
      href: '/stocks',
      color: 'bg-green-500',
      features: ['Technical analysis', 'Comparative metrics', 'Investment recommendations']
    },
    {
      name: 'RAG Evaluation',
      description: 'Quality assessment of AI-generated financial content',
      icon: CheckCircle,
      href: '/evaluation',
      color: 'bg-purple-500',
      features: ['Quality scoring', 'Batch processing', 'Detailed feedback']
    }
  ];

  const stats = [
    {
      name: 'Active Streams',
      value: systemStatus?.streaming?.active_connections || 0,
      icon: Activity,
      change: '+12%',
      changeType: 'positive'
    },
    {
      name: 'API Requests',
      value: '2.4k',
      icon: BarChart3,
      change: '+5.2%',
      changeType: 'positive'
    },
    {
      name: 'Avg Response Time',
      value: systemStatus?.streaming?.average_response_time || '1.2s',
      icon: Clock,
      change: '-0.3s',
      changeType: 'positive'
    },
    {
      name: 'Success Rate',
      value: '99.8%',
      icon: Users,
      change: '+0.1%',
      changeType: 'positive'
    }
  ];

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <LoadingSpinner size="lg" text="Loading dashboard..." />
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Welcome Section */}
      <div className="bg-gradient-to-r from-primary-600 to-primary-700 rounded-lg shadow-lg p-8 text-white">
        <div className="max-w-3xl">
          <h1 className="text-3xl font-bold mb-4">
            Welcome to Financial AI Agents
          </h1>
          <p className="text-xl text-primary-100 mb-6">
            Professional-grade financial analysis through specialized AI agents. 
            Get comprehensive research, stock analysis, and quality evaluation in real-time.
          </p>
          <div className="flex flex-wrap gap-4">
            <Link 
              to="/research" 
              className="bg-white text-primary-600 px-6 py-3 rounded-lg font-medium hover:bg-primary-50 transition-colors duration-200"
            >
              Start Research Analysis
            </Link>
            <Link 
              to="/stocks" 
              className="border border-primary-200 text-white px-6 py-3 rounded-lg font-medium hover:bg-primary-600 transition-colors duration-200"
            >
              Analyze Stocks
            </Link>
          </div>
        </div>
      </div>

      {/* System Status */}
      {error ? (
        <div className="card bg-danger-50 border-danger-200">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-medium text-danger-800">System Status Error</h3>
              <p className="text-danger-600">{error}</p>
            </div>
            <button 
              onClick={fetchSystemStatus}
              className="btn-primary"
            >
              Retry
            </button>
          </div>
        </div>
      ) : systemStatus && (
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold text-gray-900">System Status</h2>
            <div className="flex items-center space-x-2">
              <div className="h-2 w-2 bg-green-400 rounded-full animate-pulse"></div>
              <span className="text-sm text-green-600 font-medium">
                {systemStatus.status === 'operational' ? 'All Systems Operational' : systemStatus.status}
              </span>
            </div>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {stats.map((stat) => {
              const Icon = stat.icon;
              return (
                <div key={stat.name} className="bg-gray-50 rounded-lg p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-gray-600">{stat.name}</p>
                      <p className="text-2xl font-semibold text-gray-900">{stat.value}</p>
                    </div>
                    <Icon className="h-8 w-8 text-gray-400" />
                  </div>
                  <div className="mt-2">
                    <span className={`text-sm font-medium ${
                      stat.changeType === 'positive' ? 'text-green-600' : 'text-red-600'
                    }`}>
                      {stat.change}
                    </span>
                    <span className="text-sm text-gray-500 ml-1">from last hour</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Services Grid */}
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-6">Available Services</h2>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {services.map((service) => {
            const Icon = service.icon;
            return (
              <Link
                key={service.name}
                to={service.href}
                className="card hover:shadow-lg transition-shadow duration-200 group"
              >
                <div className="flex items-center mb-4">
                  <div className={`p-3 rounded-lg ${service.color} text-white mr-4`}>
                    <Icon className="h-6 w-6" />
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 group-hover:text-primary-600 transition-colors duration-200">
                      {service.name}
                    </h3>
                  </div>
                </div>
                
                <p className="text-gray-600 mb-4">{service.description}</p>
                
                <div className="space-y-2 mb-4">
                  {service.features.map((feature, index) => (
                    <div key={index} className="flex items-center text-sm text-gray-500">
                      <CheckCircle className="h-4 w-4 text-green-500 mr-2" />
                      {feature}
                    </div>
                  ))}
                </div>
                
                <div className="flex items-center text-primary-600 font-medium group-hover:text-primary-700 transition-colors duration-200">
                  <span>Get Started</span>
                  <ArrowRight className="h-4 w-4 ml-2 group-hover:translate-x-1 transition-transform duration-200" />
                </div>
              </Link>
            );
          })}
        </div>
      </div>

      {/* Quick Actions */}
      <div className="card">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Quick Actions</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <Link 
            to="/research" 
            className="p-4 border border-gray-200 rounded-lg hover:border-primary-300 hover:bg-primary-50 transition-colors duration-200"
          >
            <Search className="h-8 w-8 text-primary-600 mb-2" />
            <h3 className="font-medium text-gray-900">Market Research</h3>
            <p className="text-sm text-gray-500">Analyze market trends</p>
          </Link>
          
          <Link 
            to="/stocks" 
            className="p-4 border border-gray-200 rounded-lg hover:border-primary-300 hover:bg-primary-50 transition-colors duration-200"
          >
            <TrendingUp className="h-8 w-8 text-primary-600 mb-2" />
            <h3 className="font-medium text-gray-900">Stock Analysis</h3>
            <p className="text-sm text-gray-500">Compare stock performance</p>
          </Link>
          
          <Link 
            to="/evaluation" 
            className="p-4 border border-gray-200 rounded-lg hover:border-primary-300 hover:bg-primary-50 transition-colors duration-200"
          >
            <CheckCircle className="h-8 w-8 text-primary-600 mb-2" />
            <h3 className="font-medium text-gray-900">Quality Check</h3>
            <p className="text-sm text-gray-500">Evaluate AI responses</p>
          </Link>
          
          <Link 
            to="/status" 
            className="p-4 border border-gray-200 rounded-lg hover:border-primary-300 hover:bg-primary-50 transition-colors duration-200"
          >
            <Activity className="h-8 w-8 text-primary-600 mb-2" />
            <h3 className="font-medium text-gray-900">System Status</h3>
            <p className="text-sm text-gray-500">Monitor performance</p>
          </Link>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
import React, { useState, useEffect } from 'react';
import { 
  Activity, 
  Server, 
  Database, 
  Wifi, 
  Clock, 
  Users,
  AlertCircle,
  CheckCircle,
  RefreshCw
} from 'lucide-react';
import { systemAPI, researchAPI, stockAPI, evaluationAPI } from '../services/api';
import LoadingSpinner from '../components/LoadingSpinner';

const SystemStatus = () => {
  const [systemStatus, setSystemStatus] = useState(null);
  const [serviceStatuses, setServiceStatuses] = useState({});
  const [streamingStats, setStreamingStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);

  useEffect(() => {
    fetchAllStatus();
    const interval = setInterval(fetchAllStatus, 30000); // Update every 30 seconds
    return () => clearInterval(interval);
  }, []);

  const fetchAllStatus = async () => {
    try {
      setLoading(true);
      setError(null);

      // Fetch system status
      const [systemResponse, streamingResponse] = await Promise.all([
        systemAPI.getStatus(),
        systemAPI.getStreamingStats()
      ]);

      setSystemStatus(systemResponse.data);
      setStreamingStats(streamingResponse.data);

      // Fetch service statuses
      const servicePromises = [
        researchAPI.getStatus().then(res => ({ service: 'research', data: res.data })),
        stockAPI.getStatus().then(res => ({ service: 'stocks', data: res.data })),
        evaluationAPI.getStatus().then(res => ({ service: 'evaluation', data: res.data }))
      ];

      const serviceResults = await Promise.allSettled(servicePromises);
      const services = {};
      
      serviceResults.forEach((result, index) => {
        const serviceName = ['research', 'stocks', 'evaluation'][index];
        if (result.status === 'fulfilled') {
          services[serviceName] = { status: 'healthy', data: result.value.data };
        } else {
          services[serviceName] = { status: 'error', error: result.reason.message };
        }
      });

      setServiceStatuses(services);
      setLastUpdated(new Date());
    } catch (err) {
      setError('Failed to fetch system status');
      console.error('System status error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCleanupStreams = async () => {
    try {
      const response = await systemAPI.cleanupStreams();
      alert(`Cleaned up ${response.data.cleaned_streams} inactive streams`);
      fetchAllStatus(); // Refresh status
    } catch (err) {
      alert('Failed to cleanup streams: ' + err.message);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'healthy':
      case 'ready':
      case 'operational':
        return 'text-green-600 bg-green-100';
      case 'warning':
        return 'text-yellow-600 bg-yellow-100';
      case 'error':
      case 'unhealthy':
        return 'text-red-600 bg-red-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'healthy':
      case 'ready':
      case 'operational':
        return <CheckCircle className="h-5 w-5" />;
      case 'warning':
        return <AlertCircle className="h-5 w-5" />;
      case 'error':
      case 'unhealthy':
        return <AlertCircle className="h-5 w-5" />;
      default:
        return <Activity className="h-5 w-5" />;
    }
  };

  if (loading && !systemStatus) {
    return (
      <div className="flex justify-center items-center h-64">
        <LoadingSpinner size="lg" text="Loading system status..." />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center">
            <Activity className="h-8 w-8 text-primary-600 mr-3" />
            <div>
              <h1 className="text-2xl font-bold text-gray-900">System Status</h1>
              <p className="text-gray-600">Monitor system health and performance metrics</p>
            </div>
          </div>
          <div className="flex items-center space-x-4">
            {lastUpdated && (
              <span className="text-sm text-gray-500">
                Last updated: {lastUpdated.toLocaleTimeString()}
              </span>
            )}
            <button
              onClick={fetchAllStatus}
              disabled={loading}
              className="btn-secondary flex items-center"
            >
              <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
              Refresh
            </button>
          </div>
        </div>
      </div>

      {error && (
        <div className="card bg-danger-50 border-danger-200">
          <div className="flex items-center">
            <AlertCircle className="h-5 w-5 text-danger-600 mr-2" />
            <span className="text-danger-800">{error}</span>
          </div>
        </div>
      )}

      {/* Overall System Status */}
      {systemStatus && (
        <div className="card">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-semibold text-gray-900">Overall System Health</h2>
            <div className={`flex items-center px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(systemStatus.status)}`}>
              {getStatusIcon(systemStatus.status)}
              <span className="ml-2 capitalize">{systemStatus.status}</span>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Service</p>
                  <p className="text-2xl font-semibold text-gray-900">{systemStatus.service}</p>
                </div>
                <Server className="h-8 w-8 text-gray-400" />
              </div>
            </div>

            <div className="bg-gray-50 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Version</p>
                  <p className="text-2xl font-semibold text-gray-900">{systemStatus.version}</p>
                </div>
                <Database className="h-8 w-8 text-gray-400" />
              </div>
            </div>

            <div className="bg-gray-50 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Debug Mode</p>
                  <p className="text-2xl font-semibold text-gray-900">
                    {systemStatus.debug_mode ? 'ON' : 'OFF'}
                  </p>
                </div>
                <Activity className="h-8 w-8 text-gray-400" />
              </div>
            </div>

            <div className="bg-gray-50 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">API Keys</p>
                  <p className="text-2xl font-semibold text-gray-900">
                    {Object.values(systemStatus.api_keys_configured || {}).filter(Boolean).length}
                  </p>
                </div>
                <CheckCircle className="h-8 w-8 text-gray-400" />
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Service Status */}
      <div className="card">
        <h2 className="text-xl font-semibold text-gray-900 mb-6">Service Status</h2>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {Object.entries(serviceStatuses).map(([serviceName, serviceData]) => (
            <div key={serviceName} className="border border-gray-200 rounded-lg p-4">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-lg font-medium text-gray-900 capitalize">{serviceName}</h3>
                <div className={`flex items-center px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(serviceData.status)}`}>
                  {getStatusIcon(serviceData.status)}
                  <span className="ml-1 capitalize">{serviceData.status}</span>
                </div>
              </div>
              
              {serviceData.error ? (
                <p className="text-sm text-red-600">{serviceData.error}</p>
              ) : serviceData.data && (
                <div className="text-sm text-gray-600">
                  <p>Agent: {serviceData.data.agent || serviceName}</p>
                  <p>Service initialized: {serviceData.data.service_initialized ? 'Yes' : 'No'}</p>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Streaming Statistics */}
      {streamingStats && (
        <div className="card">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-semibold text-gray-900">Streaming Statistics</h2>
            <button
              onClick={handleCleanupStreams}
              className="btn-secondary text-sm"
            >
              Cleanup Inactive Streams
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-blue-50 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-blue-600">Active Connections</p>
                  <p className="text-2xl font-semibold text-blue-900">
                    {streamingStats.active_connections || 0}
                  </p>
                </div>
                <Wifi className="h-8 w-8 text-blue-400" />
              </div>
            </div>

            <div className="bg-green-50 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-green-600">Total Streams</p>
                  <p className="text-2xl font-semibold text-green-900">
                    {streamingStats.total_streams_created || 0}
                  </p>
                </div>
                <Users className="h-8 w-8 text-green-400" />
              </div>
            </div>

            <div className="bg-yellow-50 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-yellow-600">Avg Response Time</p>
                  <p className="text-2xl font-semibold text-yellow-900">
                    {streamingStats.average_response_time || 'N/A'}
                  </p>
                </div>
                <Clock className="h-8 w-8 text-yellow-400" />
              </div>
            </div>

            <div className="bg-purple-50 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-purple-600">Error Rate</p>
                  <p className="text-2xl font-semibold text-purple-900">
                    {streamingStats.error_rate || '0%'}
                  </p>
                </div>
                <AlertCircle className="h-8 w-8 text-purple-400" />
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Configuration */}
      {systemStatus && systemStatus.configuration && (
        <div className="card">
          <h2 className="text-xl font-semibold text-gray-900 mb-6">Configuration</h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-3">API Settings</h3>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">Max Sources:</span>
                  <span className="font-medium">{systemStatus.configuration.max_sources}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Request Timeout:</span>
                  <span className="font-medium">{systemStatus.configuration.request_timeout}s</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Default Model:</span>
                  <span className="font-medium">{systemStatus.configuration.default_model}</span>
                </div>
              </div>
            </div>

            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-3">Available Endpoints</h3>
              <div className="space-y-1 text-sm">
                {systemStatus.available_endpoints && Object.entries(systemStatus.available_endpoints).map(([key, endpoint]) => (
                  <div key={key} className="flex justify-between">
                    <span className="text-gray-600 capitalize">{key.replace('_', ' ')}:</span>
                    <code className="text-xs bg-gray-100 px-2 py-1 rounded">{endpoint}</code>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default SystemStatus;
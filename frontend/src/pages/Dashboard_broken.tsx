import React, { useState, useEffect } from 'react';
import { useQuery, useQueryClient } from 'react-query';
import { 
  AlertTriangle, 
  Activity, 
  TrendingUp, 
  MapPin, 
  Clock,
  Eye,
  Zap
} from 'lucide-react';
import toast from 'react-hot-toast';

// Components
import MapView from '../components/MapView.tsx';
import RiskChart from '../components/RiskChart.tsx';
import DataTable from '../components/DataTable.tsx';
import AlertCard from '../components/AlertCard.tsx';
import StatCard from '../components/StatCard.tsx';

// API
import { fetchCoastalData, getAlertHistory, fetchStatistics, fetchTrends } from '../api/coastalData.ts';

const Dashboard: React.FC = () => {
  const [selectedRegion, setSelectedRegion] = useState<string>('all');
  const [timeRange, setTimeRange] = useState<string>('24h');
  const [wsStatus, setWsStatus] = useState<'connecting' | 'connected' | 'disconnected'>('disconnected');
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);
  
  // React Query client for cache invalidation
  const queryClient = useQueryClient();

  // WebSocket connection for real-time updates
  useEffect(() => {
    let ws: WebSocket | null = null;
    let reconnectTimer: NodeJS.Timeout | null = null;
    let isComponentMounted = true;
    
    const connectWebSocket = () => {
      if (!isComponentMounted) return;
      
      // Clean up existing connection
      if (ws) {
        ws.close();
      }
      
      setWsStatus('connecting');
      ws = new WebSocket('ws://localhost:8000/ws');
      
      ws.onopen = () => {
        if (!isComponentMounted) return;
        console.log('✅ WebSocket connected');
        setWsStatus('connected');
        toast.success('Real-time connection established', { duration: 2000 });
        
        // Subscribe to real-time updates
        ws?.send(JSON.stringify({
          type: 'subscribe',
          topics: ['coastal_data', 'alerts', 'statistics']
        }));
      };
      
      ws.onmessage = (event) => {
        if (!isComponentMounted) return;
        
        try {
          const message = JSON.parse(event.data);
          console.log('📨 WebSocket message received:', message);
          setLastUpdate(new Date());
          
          if (message.type === 'topic_update') {
            // Handle real-time data updates
            if (message.topic === 'coastal_data') {
              // Trigger refetch of coastal data
              queryClient.invalidateQueries(['coastalData']);
              queryClient.invalidateQueries(['statistics']);
              queryClient.invalidateQueries(['trends']);
            } else if (message.topic === 'alerts') {
              // Trigger refetch of alerts
              queryClient.invalidateQueries(['alerts']);
              toast.error('🚨 New high-risk alert detected!', { duration: 4000 });
            }
          }
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };
      
      ws.onclose = (event) => {
        if (!isComponentMounted) return;
        
        console.log('❌ WebSocket disconnected', event.code, event.reason);
        setWsStatus('disconnected');
        
        // Only show error toast if it wasn't a normal closure
        if (event.code !== 1000) {
          toast.error('Real-time connection lost', { duration: 3000 });
        }
        
        // Clear any existing reconnect timer
        if (reconnectTimer) {
          clearTimeout(reconnectTimer);
        }
        
        // Attempt to reconnect after 3 seconds if not a normal closure
        if (event.code !== 1000 && isComponentMounted) {
          reconnectTimer = setTimeout(() => {
            if (isComponentMounted) {
              connectWebSocket();
            }
          }, 3000);
        }
      };
      
      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        if (isComponentMounted) {
          setWsStatus('disconnected');
        }
      };
    };
    
    // Initial connection
    connectWebSocket();
    
    // Cleanup function
    return () => {
      isComponentMounted = false;
      if (reconnectTimer) {
        clearTimeout(reconnectTimer);
      }
      if (ws) {
        ws.close(1000, 'Component unmounting');
      }
    };
  }, [queryClient]);
      };
      
      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        if (isComponentMounted) {
          setWsStatus('disconnected');
        }
      };
    };
    
    // Initial connection
    connectWebSocket();
    
    // Cleanup function
    return () => {
      isComponentMounted = false;
      if (reconnectTimer) {
        clearTimeout(reconnectTimer);
      }
      if (ws) {
        ws.close(1000, 'Component unmounting');
      }
    };
  }, [queryClient]);

  // Fetch data
  const { data: coastalData, isLoading: dataLoading } = useQuery(
    ['coastalData', selectedRegion],
    () => fetchCoastalData({ region: selectedRegion === 'all' ? undefined : selectedRegion }),
    { refetchInterval: 30000 } // Refetch every 30 seconds
  );

  const { data: statistics } = useQuery(
    ['statistics', selectedRegion],
    () => fetchStatistics(selectedRegion === 'all' ? undefined : selectedRegion)
  );

  const { data: trends } = useQuery(
    ['trends', selectedRegion, timeRange],
    () => fetchTrends({ region: selectedRegion === 'all' ? undefined : selectedRegion, hours: timeRange === '24h' ? 24 : 168 })
  );

  // Real-time alerts from API
  const { data: alertsData } = useQuery(
    ['alerts'],
    () => getAlertHistory({ limit: 10 }),
    { 
      refetchInterval: 10000, // Refetch every 10 seconds
      onSuccess: (data) => {
        if (data && data.alerts && data.alerts.length > 0) {
          // Transform backend alert format to frontend format
          const transformedAlerts = data.alerts.map((alert: any) => ({
            id: alert.id,
            type: alert.alert_type,
            severity: alert.severity.toLowerCase(),
            message: alert.message,
            location: alert.location_data?.region || 'Unknown',
            timestamp: alert.triggered_at,
            risk_score: alert.risk_score
          }));
          setAlerts(transformedAlerts);
        }
      }
    }
  );

  const [alerts, setAlerts] = useState<any[]>([]);

  // WebSocket connection for real-time updates
  useEffect(() => {
    const ws = new WebSocket('ws://localhost:8000/ws');
    
    ws.onopen = () => {
      console.log('WebSocket connected for real-time data');
      toast.success('Real-time monitoring connected');
    };
    
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        console.log('Real-time update received:', data);
        
        if (data.type === 'coastal_data_update') {
          // Refetch coastal data when new data arrives
          toast(`New coastal data received: ${data.location}`, { icon: 'ℹ️' });
          // Trigger refetch of queries
          window.location.reload(); // For demo purposes - in production, use query invalidation
        } else if (data.type === 'alert_triggered') {
          // Handle new alert
          toast.error(`New alert: ${data.message}`);
          const newAlert = {
            id: data.id || Math.random().toString(),
            type: data.alert_type || 'system',
            severity: data.severity || 'medium',
            message: data.message,
            location: data.location || 'Unknown',
            timestamp: new Date().toISOString(),
            risk_score: data.risk_score || 0.5
          };
          setAlerts(prev => [newAlert, ...prev.slice(0, 9)]); // Keep only latest 10
        }
      } catch (error) {
        console.error('WebSocket message parsing error:', error);
      }
    };
    
    ws.onerror = (error) => {
      console.error('WebSocket connection error:', error);
      toast.error('Real-time connection lost');
    };
    
    ws.onclose = () => {
      console.log('WebSocket connection closed');
      toast('Real-time monitoring disconnected', { icon: '⚠️' });
    };
    
    return () => {
      ws.close();
    };
  }, []);

  const handleRegionChange = (region: string) => {
    setSelectedRegion(region);
  };

  const handleTimeRangeChange = (range: string) => {
    setTimeRange(range);
  };

  if (dataLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Coastal Threat Dashboard</h1>
          <p className="mt-1 text-sm text-gray-500">
            Real-time monitoring of coastal threats and risk assessment
          </p>
          {/* Connection Status */}
          <div className="mt-2 flex items-center space-x-2">
            <div className={`w-2 h-2 rounded-full ${
              wsStatus === 'connected' ? 'bg-green-500' : 
              wsStatus === 'connecting' ? 'bg-yellow-500' : 'bg-red-500'
            }`}></div>
            <span className="text-xs text-gray-600">
              {wsStatus === 'connected' ? 'Real-time connected' : 
               wsStatus === 'connecting' ? 'Connecting...' : 'Connection lost'}
            </span>
            {lastUpdate && (
              <span className="text-xs text-gray-500">
                Last update: {lastUpdate.toLocaleTimeString()}
              </span>
            )}
          </div>
        </div>
        
        <div className="mt-4 sm:mt-0 flex items-center space-x-4">
          {/* Region Selector */}
          <select
            title="Select Region"
            value={selectedRegion}
            onChange={(e) => handleRegionChange(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="all">All Regions</option>
            <option value="Mumbai">Mumbai</option>
            <option value="Gujarat">Gujarat</option>
          </select>
          
          {/* Time Range Selector */}
          <select
            title="Select Time Range"
            value={timeRange}
            onChange={(e) => handleTimeRangeChange(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="24h">Last 24 Hours</option>
            <option value="7d">Last 7 Days</option>
          </select>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="Total Data Points"
          value={statistics?.total_records || 0}
          change="+12%"
          changeType="positive"
          icon={Activity}
        />
        <StatCard
          title="Active Alerts"
          value={alerts.length}
          change={`${alerts.filter(a => a.severity === 'critical').length > 0 ? '+' : ''}${alerts.filter(a => a.severity === 'critical').length}`}
          changeType={alerts.filter(a => a.severity === 'critical').length > 0 ? "negative" : "positive"}
          icon={AlertTriangle}
        />
        <StatCard
          title="Average Risk Score"
          value={`${((statistics?.statistics?.risk_score?.mean || 0) * 100).toFixed(1)}%`}
          change={`${((statistics?.statistics?.risk_score?.mean || 0) > 0.7) ? '+' : ''}${(((statistics?.statistics?.risk_score?.mean || 0) - 0.65) * 100).toFixed(1)}%`}
          changeType={((statistics?.statistics?.risk_score?.mean || 0) > 0.7) ? "negative" : "positive"}
          icon={TrendingUp}
        />
        <StatCard
          title="Anomalies Detected"
          value={statistics?.statistics?.anomaly_count || 0}
          change={`+${Math.floor((statistics?.statistics?.anomaly_count || 0) * 0.1)}`}
          changeType={(statistics?.statistics?.anomaly_count || 0) > 5 ? "negative" : "positive"}
          icon={Zap}
        />
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Map View */}
        <div className="lg:col-span-2">
          <div className="bg-white rounded-lg shadow-sm border border-gray-200">
            <div className="px-6 py-4 border-b border-gray-200">
              <h2 className="text-lg font-semibold text-gray-900 flex items-center">
                <MapPin className="w-5 h-5 mr-2 text-blue-600" />
                Live Map View
              </h2>
              <p className="text-sm text-gray-500 mt-1">
                Real-time coastal threat visualization
              </p>
            </div>
            <div className="p-4">
              <MapView 
                data={coastalData?.data || []}
                selectedRegion={selectedRegion}
              />
            </div>
          </div>
        </div>

        {/* Alerts Panel */}
        <div className="space-y-6">
          {/* Active Alerts */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900 flex items-center">
                <AlertTriangle className="w-5 h-5 mr-2 text-red-600" />
                Active Alerts
              </h3>
            </div>
            <div className="p-4 space-y-3">
              {alerts.map((alert) => (
                <AlertCard key={alert.id} alert={alert} />
              ))}
              {alerts.length === 0 && (
                <p className="text-sm text-gray-500 text-center py-4">
                  No active alerts
                </p>
              )}
            </div>
          </div>

          {/* Quick Actions */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900">Quick Actions</h3>
            </div>
            <div className="p-4 space-y-3">
              <button className="w-full px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors text-sm font-medium">
                Send Manual Alert
              </button>
              <button className="w-full px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors text-sm font-medium">
                Retrain ML Model
              </button>
              <button className="w-full px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 transition-colors text-sm font-medium">
                Export Report
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Charts and Data */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Risk Trend Chart */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900 flex items-center">
              <TrendingUp className="w-5 h-5 mr-2 text-green-600" />
              Risk Trend Analysis
            </h3>
            <p className="text-sm text-gray-500 mt-1">
              Risk score trends over time
            </p>
          </div>
          <div className="p-4">
            <RiskChart data={trends?.data || []} />
          </div>
        </div>

        {/* Recent Data Table */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900 flex items-center">
              <Eye className="w-5 h-5 mr-2 text-blue-600" />
              Recent Data Points
            </h3>
            <p className="text-sm text-gray-500 mt-1">
              Latest coastal monitoring data
            </p>
          </div>
          <div className="p-4">
            <DataTable 
              data={coastalData?.data?.slice(0, 10) || []}
              columns={['timestamp', 'location', 'risk_score', 'anomaly_detected']}
            />
          </div>
        </div>
      </div>

      {/* System Status */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900 flex items-center">
            <Activity className="w-5 h-5 mr-2 text-green-600" />
            System Status
          </h3>
        </div>
        <div className="p-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="text-center">
              <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-3">
                <Activity className="w-8 h-8 text-green-600" />
              </div>
              <h4 className="font-medium text-gray-900">Backend API</h4>
              <p className="text-sm text-green-600">Online</p>
            </div>
            <div className="text-center">
              <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-3">
                <Clock className="w-8 h-8 text-green-600" />
              </div>
              <h4 className="font-medium text-gray-900">Data Pipeline</h4>
              <p className="text-sm text-green-600">Active</p>
            </div>
            <div className="text-center">
              <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-3">
                <Zap className="w-8 h-8 text-green-600" />
              </div>
              <h4 className="font-medium text-gray-900">ML Models</h4>
              <p className="text-sm text-green-600">Running</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;

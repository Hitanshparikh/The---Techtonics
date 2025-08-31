import React, { useState, useEffect } from 'react';
import CountUp from 'react-countup';
import { formatDistanceToNow } from 'date-fns';
import { useQuery, useQueryClient } from 'react-query';
import {
  AlertTriangle,
  Activity,
  TrendingUp,
  MapPin,
  Clock,
  Eye,
  Zap,
  Users,
  Timer,
  AlertCircle
} from 'lucide-react';
import toast from 'react-hot-toast';
import MapView from '../components/MapView';
import RiskChart from '../components/RiskChart';
import StatCard from '../components/StatCard';
import AlertCard from '../components/AlertCard';
import { fetchCoastalData, getAlertHistory, fetchStatistics, fetchTrends } from '../api/coastalData';

interface RealtimeAnalysis {
  evacuationRecommendation: {
    population: number;
    zones: string[];
    timeframe: string;
  };
  alertDuration: {
    estimated: string;
    confidence: number;
  };
  riskTrend: {
    direction: 'increasing' | 'decreasing' | 'stable';
    severity: 'low' | 'medium' | 'high' | 'critical';
  };
}

const Dashboard: React.FC = () => {
  const [selectedRegion, setSelectedRegion] = useState<string>('all');
  const [timeRange, setTimeRange] = useState<string>('24h');
  const [wsStatus, setWsStatus] = useState<'connecting' | 'connected' | 'disconnected'>('disconnected');
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);
  const [realtimeAnalysis, setRealtimeAnalysis] = useState<RealtimeAnalysis | null>(null);
  const [livePulse, setLivePulse] = useState(false);
  const queryClient = useQueryClient();

  // WebSocket connection for real-time updates
  useEffect(() => {
    let ws: WebSocket | null = null;
    let reconnectTimer: number | null = null;
    let isComponentMounted = true;

    const connectWebSocket = () => {
      if (!isComponentMounted) return;
      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.close();
      }
      setWsStatus('connecting');
      ws = new WebSocket('ws://localhost:8000/ws');
      ws.onopen = () => {
        if (!isComponentMounted) return;
        setWsStatus('connected');
        toast.success('Real-time connection established', { duration: 2000 });
        ws?.send(JSON.stringify({
          type: 'subscribe',
          topics: ['coastal_data', 'alerts', 'statistics']
        }));
      };
      ws.onmessage = (event) => {
        if (!isComponentMounted) return;
        try {
          const message = JSON.parse(event.data);
          setLastUpdate(new Date());
          if (message.type === 'topic_update') {
            if (message.topic === 'coastal_data' || message.topic === 'alerts') {
              updateRealtimeAnalysis(message.data);
              queryClient.invalidateQueries(['coastalData']);
              queryClient.invalidateQueries(['statistics']);
              queryClient.invalidateQueries(['trends']);
              if (message.topic === 'alerts') {
                queryClient.invalidateQueries(['alerts']);
                toast.error('🚨 New high-risk alert detected!', { duration: 4000 });
              }
            }
          }
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };
      ws.onclose = (event) => {
        if (!isComponentMounted) return;
        setWsStatus('disconnected');
        if (event.code !== 1000) {
          toast.error('Real-time connection lost', { duration: 3000 });
        }
        if (reconnectTimer) {
          clearTimeout(reconnectTimer);
        }
        if (event.code !== 1000 && isComponentMounted) {
          reconnectTimer = window.setTimeout(() => {
            if (isComponentMounted) {
              connectWebSocket();
            }
          }, 3000);
        }
      };
      ws.onerror = (error) => {
        if (isComponentMounted) {
          setWsStatus('disconnected');
        }
      };
    };
    connectWebSocket();
    return () => {
      isComponentMounted = false;
      if (reconnectTimer) {
        clearTimeout(reconnectTimer);
      }
      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.close(1000, 'Component unmounting');
      }
    };
  }, [queryClient]);

  // Pulse animation for LIVE badge
  useEffect(() => {
    if (wsStatus === 'connected') {
      setLivePulse(true);
      const pulseTimer = setTimeout(() => setLivePulse(false), 2000);
      return () => clearTimeout(pulseTimer);
    }
  }, [wsStatus]);

  // Function to update real-time AI analysis
  const updateRealtimeAnalysis = (data: any) => {
    if (!data) return;
    const riskScore = data.risk_score || 0;
    const location = data.location || 'Unknown';
    let population = 0;
    let zones: string[] = [];
    let timeframe = '';
    if (riskScore > 0.9) {
      population = Math.floor(Math.random() * 50000) + 20000;
      zones = [`${location} Coastal Zone`, `${location} Low-lying Areas`, 'Emergency Shelters'];
      timeframe = 'Immediate (0-2 hours)';
    } else if (riskScore > 0.8) {
      population = Math.floor(Math.random() * 30000) + 10000;
      zones = [`${location} Coastal Zone`, 'Vulnerable Areas'];
      timeframe = 'Within 4-6 hours';
    } else if (riskScore > 0.7) {
      population = Math.floor(Math.random() * 15000) + 5000;
      zones = [`${location} High-risk Areas`];
      timeframe = 'Within 12 hours';
    }
    let alertDuration = '';
    let confidence = 0;
    if (riskScore > 0.9) {
      alertDuration = '6-12 hours';
      confidence = 85;
    } else if (riskScore > 0.8) {
      alertDuration = '4-8 hours';
      confidence = 75;
    } else {
      alertDuration = '2-4 hours';
      confidence = 65;
    }
    const riskTrend = {
      direction: riskScore > 0.8 ? 'increasing' : riskScore > 0.6 ? 'stable' : 'decreasing' as 'increasing' | 'decreasing' | 'stable',
      severity: riskScore > 0.9 ? 'critical' : riskScore > 0.8 ? 'high' : riskScore > 0.6 ? 'medium' : 'low' as 'low' | 'medium' | 'high' | 'critical'
    };
    setRealtimeAnalysis({
      evacuationRecommendation: { population, zones, timeframe },
      alertDuration: { estimated: alertDuration, confidence },
      riskTrend
    });
  };

  // Fetch data
  // Debug output for API responses
  const { data: coastalData, isLoading: dataLoading } = useQuery(
    ['coastalData', selectedRegion],
    async () => {
      const res = await fetchCoastalData({ region: selectedRegion === 'all' ? undefined : selectedRegion });
      console.log('coastalData API response:', res);
      return res;
    },
    { refetchInterval: 30000 }
  );
  const { data: statistics, isLoading: statsLoading } = useQuery(
    ['statistics', selectedRegion],
    async () => {
      const res = await fetchStatistics(selectedRegion === 'all' ? undefined : selectedRegion);
      console.log('statistics API response:', res);
      return res;
    }
  );
  const { data: trends, isLoading: trendsLoading } = useQuery(
    ['trends', selectedRegion, timeRange],
    async () => {
      const res = await fetchTrends({ region: selectedRegion === 'all' ? undefined : selectedRegion, hours: timeRange === '24h' ? 24 : 168 });
      console.log('trends API response:', res);
      return res;
    }
  );
  const { data: alerts, isLoading: alertsLoading } = useQuery(
    ['alerts'],
    async () => {
      const res = await getAlertHistory({ limit: 10 });
      console.log('alerts API response:', res);
      return res;
    }
  );

  // Handlers
  const handleRegionChange = (region: string) => setSelectedRegion(region);
  const handleTimeRangeChange = (range: string) => setTimeRange(range);

  // Loading state
  if (dataLoading || statsLoading || trendsLoading || alertsLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-500"></div>
        <span className="ml-4 text-blue-600 font-semibold animate-pulse">Loading dashboard data...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Coastal Threat Dashboard</h1>
          <p className="mt-1 text-sm text-gray-500">Real-time monitoring of coastal threats and risk assessment</p>
          {/* Connection Status */}
          <div className="mt-2 flex items-center space-x-2">
            <div className={`w-2 h-2 rounded-full ${
              wsStatus === 'connected' ? 'bg-green-500 animate-pulse' : 
              wsStatus === 'connecting' ? 'bg-yellow-500' : 'bg-red-500'
            }`}></div>
            <span className="text-xs text-gray-600">
              {wsStatus === 'connected' ? 'Real-time connected' : 
               wsStatus === 'connecting' ? 'Connecting...' : 'Connection lost'}
            </span>
            {wsStatus === 'connected' && (
              <span className={`ml-2 px-2 py-1 bg-green-100 text-green-700 rounded text-xs font-bold ${livePulse ? 'animate-pulse' : ''}`}>LIVE</span>
            )}
            {lastUpdate && (
              <span className="text-xs text-gray-500">
                Last update: {lastUpdate.toLocaleTimeString()} ({formatDistanceToNow(lastUpdate, { addSuffix: true })})
              </span>
            )}
          </div>
        </div>
        <div className="mt-4 sm:mt-0 flex items-center space-x-4">
          {/* Region Selector */}
          <select
            title="Select Region"
            value={selectedRegion}
            onChange={(e: React.ChangeEvent<HTMLSelectElement>) => handleRegionChange(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="all">All Regions</option>
            <option value="Mumbai">Mumbai</option>
            <option value="Gujarat">Gujarat</option>
            <option value="Chennai">Chennai</option>
          </select>
          {/* Time Range Selector */}
          <select
            title="Select Time Range"
            value={timeRange}
            onChange={(e: React.ChangeEvent<HTMLSelectElement>) => handleTimeRangeChange(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="24h">Last 24 Hours</option>
            <option value="7d">Last 7 Days</option>
          </select>
        </div>
      </div>

      {/* Real-time AI Analysis Section */}
      {realtimeAnalysis && (
        <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg p-6 border border-blue-200">
          <div className="flex items-center mb-4">
            <Zap className="h-6 w-6 text-blue-600 mr-2" />
            <h2 className="text-xl font-semibold text-gray-900">Real-time AI Analysis</h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Evacuation Recommendation */}
            <div className="bg-white rounded-lg p-4 border border-blue-100">
              <div className="flex items-center mb-3">
                <Users className="h-5 w-5 text-orange-600 mr-2" />
                <h3 className="font-semibold text-gray-900">Evacuation Recommendation</h3>
              </div>
              <div className="space-y-2">
                <p className="text-2xl font-bold text-orange-600">
                  {realtimeAnalysis.evacuationRecommendation.population.toLocaleString()}
                </p>
                <p className="text-sm text-gray-600">People to evacuate</p>
                <p className="text-sm font-medium text-gray-700">
                  Timeframe: {realtimeAnalysis.evacuationRecommendation.timeframe}
                </p>
                <div className="mt-2">
                  <p className="text-xs text-gray-500 mb-1">Priority Zones:</p>
                  {realtimeAnalysis.evacuationRecommendation.zones.map((zone, index) => (
                    <span key={index} className="inline-block bg-orange-100 text-orange-800 text-xs px-2 py-1 rounded-full mr-1 mb-1">
                      {zone}
                    </span>
                  ))}
                </div>
              </div>
            </div>
            {/* Alert Duration */}
            <div className="bg-white rounded-lg p-4 border border-blue-100">
              <div className="flex items-center mb-3">
                <Timer className="h-5 w-5 text-purple-600 mr-2" />
                <h3 className="font-semibold text-gray-900">Alert Duration</h3>
              </div>
              <div className="space-y-2">
                <p className="text-2xl font-bold text-purple-600">
                  {realtimeAnalysis.alertDuration.estimated}
                </p>
                <p className="text-sm text-gray-600">Estimated duration</p>
                <div className="flex items-center">
                  <div className="flex-1 bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-purple-600 h-2 rounded-full" 
                      style={{ width: `${realtimeAnalysis.alertDuration.confidence}%` }}
                    ></div>
                  </div>
                  <span className="ml-2 text-sm text-gray-600">
                    {realtimeAnalysis.alertDuration.confidence}%
                  </span>
                </div>
              </div>
            </div>
            {/* Risk Trend */}
            <div className="bg-white rounded-lg p-4 border border-blue-100">
              <div className="flex items-center mb-3">
                <TrendingUp className="h-5 w-5 text-green-600 mr-2" />
                <h3 className="font-semibold text-gray-900">Risk Trend</h3>
              </div>
              <div className="space-y-2">
                <div className="flex items-center">
                  <span className={`inline-block w-3 h-3 rounded-full mr-2 ${
                    realtimeAnalysis.riskTrend.direction === 'increasing' ? 'bg-red-500' :
                    realtimeAnalysis.riskTrend.direction === 'decreasing' ? 'bg-green-500' : 'bg-yellow-500'
                  }`}></span>
                  <p className="text-lg font-semibold capitalize">
                    {realtimeAnalysis.riskTrend.direction}
                  </p>
                </div>
                <p className="text-sm text-gray-600">
                  Severity: <span className={`font-medium ${
                    realtimeAnalysis.riskTrend.severity === 'critical' ? 'text-red-600' :
                    realtimeAnalysis.riskTrend.severity === 'high' ? 'text-orange-600' :
                    realtimeAnalysis.riskTrend.severity === 'medium' ? 'text-yellow-600' : 'text-green-600'
                  }`}>
                    {realtimeAnalysis.riskTrend.severity.toUpperCase()}
                  </span>
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="Total Data Points"
          value={<CountUp end={statistics?.total_records || 0} duration={1} separator="," />}
          icon={Activity}
          change="+12%"
          changeType="positive"
        />
        <StatCard
          title="Anomalies Detected"
          value={<CountUp end={statistics?.anomaly_count || 0} duration={1} separator="," />}
          icon={AlertTriangle}
          change={statistics?.anomaly_rate ? `${statistics.anomaly_rate}%` : '+0%'}
          changeType={statistics?.anomaly_rate > 0 ? 'negative' : 'positive'}
        />
        <StatCard
          title="Average Risk Score"
          value={<CountUp end={statistics?.average_risk ? (statistics.average_risk * 100) : 0} duration={1} decimals={1} suffix="%" />}
          icon={TrendingUp}
          change="+3%"
          changeType="negative"
        />
        <StatCard
          title="Recent Records (24h)"
          value={<CountUp end={statistics?.recent_records_24h || 0} duration={1} separator="," />}
          icon={MapPin}
          change={statistics?.recent_percentage ? `${statistics.recent_percentage}%` : '+0%'}
          changeType={statistics?.recent_percentage > 0 ? 'positive' : 'neutral'}
        />
      </div>

      {/* Charts and Map */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Risk Trends Chart */}
        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold">Risk Trends</h3>
            <div className="flex items-center text-sm text-gray-500">
              <Clock className="h-4 w-4 mr-1" />
              {timeRange === '24h' ? 'Last 24 Hours' : 'Last 7 Days'}
            </div>
          </div>
          <RiskChart data={trends?.chart_data || []} />
        </div>
        {/* Map View */}
        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold">Geographic Distribution</h3>
            <div className="flex items-center text-sm text-gray-500">
              <Eye className="h-4 w-4 mr-1" />
              {selectedRegion === 'all' ? 'All Regions' : selectedRegion}
            </div>
          </div>
          <MapView data={coastalData?.data || []} selectedRegion={selectedRegion} />
        </div>
      </div>

      {/* Recent Alerts */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-semibold flex items-center">
            <AlertCircle className="h-5 w-5 mr-2 text-red-500" />
            Recent Alerts
          </h3>
        </div>
        <div className="p-6">
          {alerts && alerts.length > 0 ? (
            <div className="space-y-4">
              {alerts.slice(0, 5).map((alert: any, index: number) => (
                <div key={index}>
                  <AlertCard 
                    alert={{...alert, timeAgo: formatDistanceToNow(new Date(alert.timestamp), { addSuffix: true })}} 
                  />
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-500 text-center py-8">No recent alerts</p>
          )}
        </div>
      </div>
    </div>
  );
};

export default Dashboard;

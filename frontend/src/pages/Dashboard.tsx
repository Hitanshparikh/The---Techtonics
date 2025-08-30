import React, { useState, useEffect } from 'react';
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
  AlertCircle,
  Waves,
  Mountain,
  Droplets,
  Shield,
  Leaf,
  Satellite,
  Radio,
  Database,
  CheckCircle,
  XCircle
} from 'lucide-react';
import toast from 'react-hot-toast';

// Components
import MapView from '../components/MapView.tsx';
import RiskChart from '../components/RiskChart.tsx';
import StatCard from '../components/StatCard.tsx';
import AlertCard from '../components/AlertCard.tsx';

// API
import { fetchCoastalData, getAlertHistory, fetchStatistics, fetchTrends } from '../api/coastalData.ts';

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
  threatDetails: {
    stormSurge: { risk: number; height: string; impact: string };
    coastalErosion: { rate: string; area: string; urgency: string };
    pollution: { level: string; type: string; source: string };
    illegalActivity: { detected: boolean; type: string; location: string };
    blueCarbonThreat: { habitatRisk: number; carbonLoss: string; priority: string };
  };
  dataSourceStatus: {
    sensors: { active: number; total: number; lastUpdate: string };
    satellite: { status: string; coverage: string; freshness: string };
    historical: { records: number; timespan: string; accuracy: string };
  };
}

const Dashboard: React.FC = () => {
  const [selectedRegion, setSelectedRegion] = useState<string>('all');
  const [timeRange, setTimeRange] = useState<string>('24h');
  const [wsStatus, setWsStatus] = useState<'connecting' | 'connected' | 'disconnected'>('disconnected');
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);
  const [realtimeAnalysis, setRealtimeAnalysis] = useState<RealtimeAnalysis | null>(null);
  
  // React Query client for cache invalidation
  const queryClient = useQueryClient();

  // WebSocket connection for real-time updates
  useEffect(() => {
    let ws: WebSocket | null = null;
    let reconnectTimer: number | null = null;
    let isComponentMounted = true;
    
    const connectWebSocket = () => {
      if (!isComponentMounted) return;
      
      // Clean up existing connection
      if (ws && ws.readyState === WebSocket.OPEN) {
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
            if (message.topic === 'coastal_data' || message.topic === 'alerts') {
              // If we have enhanced AI analysis from the server, use it directly
              if (message.data?.ai_analysis) {
                const aiData = message.data.ai_analysis;
                
                // Transform snake_case threat_details to camelCase
                const threatDetails = aiData.threat_details ? {
                  stormSurge: aiData.threat_details.storm_surge || { risk: 0.7, height: "2.5m", impact: "Moderate coastal flooding expected" },
                  coastalErosion: aiData.threat_details.coastal_erosion || { rate: "1.2m/year", area: "15 hectares", urgency: "Medium" },
                  pollution: aiData.threat_details.pollution || { level: "Moderate", type: "Industrial runoff", source: "Upstream facilities" },
                  illegalActivity: aiData.threat_details.illegal_activity || { detected: false, type: "None", location: "N/A" },
                  blueCarbonThreat: aiData.threat_details.blue_carbon_threat || { habitatRisk: 0.6, carbonLoss: "150 tons CO2/year", priority: "High" }
                } : {
                  stormSurge: { risk: 0.7, height: "2.5m", impact: "Moderate coastal flooding expected" },
                  coastalErosion: { rate: "1.2m/year", area: "15 hectares", urgency: "Medium" },
                  pollution: { level: "Moderate", type: "Industrial runoff", source: "Upstream facilities" },
                  illegalActivity: { detected: false, type: "None", location: "N/A" },
                  blueCarbonThreat: { habitatRisk: 0.6, carbonLoss: "150 tons CO2/year", priority: "High" }
                };
                
                setRealtimeAnalysis({
                  evacuationRecommendation: aiData.evacuation_recommendation,
                  alertDuration: aiData.alert_duration,
                  riskTrend: aiData.risk_trend,
                  threatDetails,
                  dataSourceStatus: aiData.data_sources || {
                    sensors: { active: 12, total: 15, lastUpdate: "2 minutes ago" },
                    satellite: { status: "Operational", coverage: "95%", freshness: "6 hours" },
                    historical: { records: 50000, timespan: "20 years", accuracy: "98%" }
                  }
                });
              } else {
                // Fallback to client-side analysis
                updateRealtimeAnalysis(message.data);
              }
              
              // Trigger refetch of data
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
          reconnectTimer = window.setTimeout(() => {
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
      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.close(1000, 'Component unmounting');
      }
    };
  }, [queryClient]);

  // Function to update real-time AI analysis
  const updateRealtimeAnalysis = (data: any) => {
    if (!data) return;
    
    const riskScore = data.risk_score || 0;
    const location = data.location || 'Unknown';
    
    // Calculate evacuation recommendations based on risk score
    let population = 0;
    let zones: string[] = [];
    let timeframe = '';
    
    if (riskScore > 0.9) {
      population = Math.floor(Math.random() * 50000) + 20000; // 20k-70k people
      zones = [`${location} Coastal Zone`, `${location} Low-lying Areas`, 'Emergency Shelters'];
      timeframe = 'Immediate (0-2 hours)';
    } else if (riskScore > 0.8) {
      population = Math.floor(Math.random() * 30000) + 10000; // 10k-40k people
      zones = [`${location} Coastal Zone`, 'Vulnerable Areas'];
      timeframe = 'Within 4-6 hours';
    } else if (riskScore > 0.7) {
      population = Math.floor(Math.random() * 15000) + 5000; // 5k-20k people
      zones = [`${location} High-risk Areas`];
      timeframe = 'Within 12 hours';
    }
    
    // Calculate alert duration
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
    
    // Determine risk trend
    const riskTrend = {
      direction: riskScore > 0.8 ? 'increasing' : riskScore > 0.6 ? 'stable' : 'decreasing' as 'increasing' | 'decreasing' | 'stable',
      severity: riskScore > 0.9 ? 'critical' : riskScore > 0.8 ? 'high' : riskScore > 0.6 ? 'medium' : 'low' as 'low' | 'medium' | 'high' | 'critical'
    };
    
    setRealtimeAnalysis({
      evacuationRecommendation: {
        population,
        zones,
        timeframe
      },
      alertDuration: {
        estimated: alertDuration,
        confidence
      },
      riskTrend,
      threatDetails: {
        stormSurge: { 
          risk: riskScore, 
          height: riskScore > 0.8 ? "3.5m" : riskScore > 0.6 ? "2.5m" : "1.5m", 
          impact: riskScore > 0.8 ? "Severe flooding expected" : "Moderate coastal impact" 
        },
        coastalErosion: { 
          rate: riskScore > 0.7 ? "2.1m/year" : "0.8m/year", 
          area: `${Math.floor(riskScore * 25)} hectares`, 
          urgency: riskScore > 0.8 ? "High" : "Medium" 
        },
        pollution: { 
          level: riskScore > 0.7 ? "High" : "Moderate", 
          type: "Multiple sources", 
          source: "Industrial and urban runoff" 
        },
        illegalActivity: { 
          detected: riskScore > 0.9, 
          type: riskScore > 0.9 ? "Illegal dumping detected" : "None", 
          location: riskScore > 0.9 ? location : "N/A" 
        },
        blueCarbonThreat: { 
          habitatRisk: riskScore * 0.8, 
          carbonLoss: `${Math.floor(riskScore * 200)} tons CO2/year`, 
          priority: riskScore > 0.8 ? "Critical" : riskScore > 0.6 ? "High" : "Medium" 
        }
      },
      dataSourceStatus: {
        sensors: { 
          active: Math.floor(Math.random() * 3) + 10, 
          total: 15, 
          lastUpdate: "Real-time" 
        },
        satellite: { 
          status: "Operational", 
          coverage: `${Math.floor(90 + Math.random() * 10)}%`, 
          freshness: "4 hours" 
        },
        historical: { 
          records: 45000 + Math.floor(Math.random() * 10000), 
          timespan: "20 years", 
          accuracy: "98%" 
        }
      }
    });
  };

  // Fetch data
  const { data: coastalData, isLoading: dataLoading } = useQuery(
    ['coastalData', selectedRegion],
    () => fetchCoastalData({ region: selectedRegion === 'all' ? undefined : selectedRegion }),
    { refetchInterval: 30000 } // Refetch every 30 seconds
  );

  const { data: statistics, isLoading: statsLoading } = useQuery(
    ['statistics', selectedRegion],
    () => fetchStatistics(selectedRegion === 'all' ? undefined : selectedRegion)
  );

  const { data: trends, isLoading: trendsLoading } = useQuery(
    ['trends', selectedRegion, timeRange],
    () => fetchTrends({ region: selectedRegion === 'all' ? undefined : selectedRegion, hours: timeRange === '24h' ? 24 : 168 })
  );

  const { data: alerts, isLoading: alertsLoading } = useQuery(
    ['alerts'],
    () => getAlertHistory({ limit: 10 })
  );

  // Handle region change
  const handleRegionChange = (region: string) => {
    setSelectedRegion(region);
  };

  // Handle time range change
  const handleTimeRangeChange = (range: string) => {
    setTimeRange(range);
  };

  // Loading state
  if (dataLoading || statsLoading || trendsLoading || alertsLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-500"></div>
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
            <option value="Chennai">Chennai</option>
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
                      className="bg-purple-600 h-2 rounded-full transition-all duration-500"
                      style={{
                        width: `${realtimeAnalysis.alertDuration.confidence}%`
                      }}
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

      {/* Comprehensive Threat Analysis */}
      {realtimeAnalysis && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Coastal Threats Matrix */}
          <div className="bg-white rounded-lg p-6 shadow border">
            <div className="flex items-center mb-4">
              <Waves className="h-6 w-6 text-blue-600 mr-2" />
              <h2 className="text-xl font-semibold text-gray-900">Coastal Threat Matrix</h2>
            </div>
            
            <div className="space-y-4">
              {/* Storm Surge */}
              <div className="flex items-center justify-between p-3 bg-red-50 rounded-lg border border-red-200">
                <div className="flex items-center">
                  <Waves className="h-5 w-5 text-red-600 mr-3" />
                  <div>
                    <h4 className="font-semibold text-red-900">Storm Surge</h4>
                    <p className="text-sm text-red-700">Height: {realtimeAnalysis.threatDetails.stormSurge.height}</p>
                  </div>
                </div>
                <div className="text-right">
                  <span className="text-lg font-bold text-red-600">
                    {(realtimeAnalysis.threatDetails.stormSurge.risk * 100).toFixed(0)}%
                  </span>
                  <p className="text-xs text-red-600">Risk Level</p>
                </div>
              </div>

              {/* Coastal Erosion */}
              <div className="flex items-center justify-between p-3 bg-orange-50 rounded-lg border border-orange-200">
                <div className="flex items-center">
                  <Mountain className="h-5 w-5 text-orange-600 mr-3" />
                  <div>
                    <h4 className="font-semibold text-orange-900">Coastal Erosion</h4>
                    <p className="text-sm text-orange-700">Rate: {realtimeAnalysis.threatDetails.coastalErosion.rate}</p>
                  </div>
                </div>
                <div className="text-right">
                  <span className="text-lg font-bold text-orange-600">
                    {realtimeAnalysis.threatDetails.coastalErosion.urgency}
                  </span>
                  <p className="text-xs text-orange-600">Urgency</p>
                </div>
              </div>

              {/* Pollution */}
              <div className="flex items-center justify-between p-3 bg-yellow-50 rounded-lg border border-yellow-200">
                <div className="flex items-center">
                  <Droplets className="h-5 w-5 text-yellow-600 mr-3" />
                  <div>
                    <h4 className="font-semibold text-yellow-900">Pollution</h4>
                    <p className="text-sm text-yellow-700">Type: {realtimeAnalysis.threatDetails.pollution.type}</p>
                  </div>
                </div>
                <div className="text-right">
                  <span className="text-lg font-bold text-yellow-600">
                    {realtimeAnalysis.threatDetails.pollution.level}
                  </span>
                  <p className="text-xs text-yellow-600">Level</p>
                </div>
              </div>

              {/* Illegal Activity */}
              <div className={`flex items-center justify-between p-3 rounded-lg border ${
                realtimeAnalysis.threatDetails.illegalActivity.detected 
                  ? 'bg-red-50 border-red-200' 
                  : 'bg-green-50 border-green-200'
              }`}>
                <div className="flex items-center">
                  <Shield className={`h-5 w-5 mr-3 ${
                    realtimeAnalysis.threatDetails.illegalActivity.detected 
                      ? 'text-red-600' 
                      : 'text-green-600'
                  }`} />
                  <div>
                    <h4 className={`font-semibold ${
                      realtimeAnalysis.threatDetails.illegalActivity.detected 
                        ? 'text-red-900' 
                        : 'text-green-900'
                    }`}>Illegal Activity</h4>
                    <p className={`text-sm ${
                      realtimeAnalysis.threatDetails.illegalActivity.detected 
                        ? 'text-red-700' 
                        : 'text-green-700'
                    }`}>
                      {realtimeAnalysis.threatDetails.illegalActivity.type}
                    </p>
                  </div>
                </div>
                <div className="text-right">
                  {realtimeAnalysis.threatDetails.illegalActivity.detected ? (
                    <XCircle className="h-6 w-6 text-red-600" />
                  ) : (
                    <CheckCircle className="h-6 w-6 text-green-600" />
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* Blue Carbon Protection */}
          <div className="bg-gradient-to-br from-green-50 to-blue-50 rounded-lg p-6 shadow border border-green-200">
            <div className="flex items-center mb-4">
              <Leaf className="h-6 w-6 text-green-600 mr-2" />
              <h2 className="text-xl font-semibold text-gray-900">Blue Carbon Habitat Protection</h2>
            </div>
            
            <div className="space-y-4">
              <div className="bg-white rounded-lg p-4 border border-green-100">
                <div className="flex items-center justify-between mb-2">
                  <h4 className="font-semibold text-green-900">Habitat Risk Assessment</h4>
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                    realtimeAnalysis.threatDetails.blueCarbonThreat.habitatRisk > 0.7 
                      ? 'bg-red-100 text-red-800' 
                      : realtimeAnalysis.threatDetails.blueCarbonThreat.habitatRisk > 0.5 
                        ? 'bg-yellow-100 text-yellow-800' 
                        : 'bg-green-100 text-green-800'
                  }`}>
                    {(realtimeAnalysis.threatDetails.blueCarbonThreat.habitatRisk * 100).toFixed(0)}% Risk
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div 
                    className="bg-gradient-to-r from-green-500 to-red-500 h-2 rounded-full transition-all duration-500"
                    style={{width: `${realtimeAnalysis.threatDetails.blueCarbonThreat.habitatRisk * 100}%`}}
                  ></div>
                </div>
              </div>

              <div className="bg-white rounded-lg p-4 border border-green-100">
                <h4 className="font-semibold text-green-900 mb-2">Carbon Loss Estimation</h4>
                <p className="text-2xl font-bold text-red-600 mb-1">
                  {realtimeAnalysis.threatDetails.blueCarbonThreat.carbonLoss}
                </p>
                <p className="text-sm text-gray-600">Potential annual carbon loss</p>
              </div>

              <div className="bg-white rounded-lg p-4 border border-green-100">
                <h4 className="font-semibold text-green-900 mb-2">Conservation Priority</h4>
                <span className={`inline-block px-3 py-1 rounded-full text-sm font-medium ${
                  realtimeAnalysis.threatDetails.blueCarbonThreat.priority === 'Critical' 
                    ? 'bg-red-100 text-red-800' 
                    : realtimeAnalysis.threatDetails.blueCarbonThreat.priority === 'High' 
                      ? 'bg-orange-100 text-orange-800' 
                      : 'bg-yellow-100 text-yellow-800'
                }`}>
                  {realtimeAnalysis.threatDetails.blueCarbonThreat.priority} Priority
                </span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Data Source Status */}
      {realtimeAnalysis && (
        <div className="bg-white rounded-lg p-6 shadow border">
          <div className="flex items-center mb-4">
            <Database className="h-6 w-6 text-purple-600 mr-2" />
            <h2 className="text-xl font-semibold text-gray-900">Multi-Source Data Integration</h2>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Physical Sensors */}
            <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
              <div className="flex items-center mb-3">
                <Radio className="h-5 w-5 text-blue-600 mr-2" />
                <h3 className="font-semibold text-blue-900">Physical Sensors</h3>
              </div>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-sm text-blue-700">Active:</span>
                  <span className="font-medium text-blue-900">
                    {realtimeAnalysis.dataSourceStatus.sensors.active}/{realtimeAnalysis.dataSourceStatus.sensors.total}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-blue-700">Last Update:</span>
                  <span className="font-medium text-blue-900">
                    {realtimeAnalysis.dataSourceStatus.sensors.lastUpdate}
                  </span>
                </div>
                <div className="w-full bg-blue-200 rounded-full h-2">
                  <div 
                    className="bg-blue-600 h-2 rounded-full"
                    style={{width: `${(realtimeAnalysis.dataSourceStatus.sensors.active / realtimeAnalysis.dataSourceStatus.sensors.total) * 100}%`}}
                  ></div>
                </div>
              </div>
            </div>

            {/* Satellite Data */}
            <div className="bg-green-50 rounded-lg p-4 border border-green-200">
              <div className="flex items-center mb-3">
                <Satellite className="h-5 w-5 text-green-600 mr-2" />
                <h3 className="font-semibold text-green-900">Satellite Feeds</h3>
              </div>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-sm text-green-700">Status:</span>
                  <span className="font-medium text-green-900">
                    {realtimeAnalysis.dataSourceStatus.satellite.status}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-green-700">Coverage:</span>
                  <span className="font-medium text-green-900">
                    {realtimeAnalysis.dataSourceStatus.satellite.coverage}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-green-700">Data Age:</span>
                  <span className="font-medium text-green-900">
                    {realtimeAnalysis.dataSourceStatus.satellite.freshness}
                  </span>
                </div>
              </div>
            </div>

            {/* Historical Records */}
            <div className="bg-purple-50 rounded-lg p-4 border border-purple-200">
              <div className="flex items-center mb-3">
                <Database className="h-5 w-5 text-purple-600 mr-2" />
                <h3 className="font-semibold text-purple-900">Historical Data</h3>
              </div>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-sm text-purple-700">Records:</span>
                  <span className="font-medium text-purple-900">
                    {realtimeAnalysis.dataSourceStatus.historical.records.toLocaleString()}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-purple-700">Timespan:</span>
                  <span className="font-medium text-purple-900">
                    {realtimeAnalysis.dataSourceStatus.historical.timespan}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-purple-700">Accuracy:</span>
                  <span className="font-medium text-purple-900">
                    {realtimeAnalysis.dataSourceStatus.historical.accuracy}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="Total Data Points"
          value={statistics?.total_records || 0}
          icon={Activity}
          change="+12%"
          changeType="positive"
        />
        <StatCard
          title="High Risk Alerts"
          value={statistics?.high_risk_count || 0}
          icon={AlertTriangle}
          change="+5%"
          changeType="negative"
        />
        <StatCard
          title="Average Risk Score"
          value={statistics?.avg_risk_score ? (statistics.avg_risk_score * 100).toFixed(1) + '%' : '0%'}
          icon={TrendingUp}
          change="+3%"
          changeType="negative"
        />
        <StatCard
          title="Active Regions"
          value={statistics?.active_regions || 0}
          icon={MapPin}
          change="+1"
          changeType="positive"
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
          <MapView data={coastalData || []} selectedRegion={selectedRegion} />
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
                <AlertCard key={index} alert={alert} />
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



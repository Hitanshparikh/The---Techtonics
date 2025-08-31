import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Area, AreaChart } from 'recharts';

interface RiskChartProps {
  data: any[];
  analysisData?: any;
}

const RiskChart: React.FC<RiskChartProps> = ({ data, analysisData }) => {
  // Use real risk score from ML analysis if available
  const getRiskScore = () => {
    if (analysisData?.ml_predictions?.risk_score !== undefined) {
      return analysisData.ml_predictions.risk_score;
    }
    if (analysisData?.risk_score !== undefined) {
      return analysisData.risk_score;
    }
    return 0.5; // Default fallback
  };

  const getTrend = () => {
    if (analysisData?.ml_predictions?.trend) {
      return analysisData.ml_predictions.trend;
    }
    if (analysisData?.trend) {
      return analysisData.trend;
    }
    return 'stable';
  };

  const getConfidence = () => {
    if (analysisData?.ml_predictions?.confidence !== undefined) {
      return analysisData.ml_predictions.confidence;
    }
    if (analysisData?.confidence !== undefined) {
      return analysisData.confidence;
    }
    return 0.7; // Default confidence
  };

  // Transform data for chart
  const chartData = data.map((item, index) => {
    const riskScore = getRiskScore();
    // Add some variation based on other factors
    const variation = (item.tide_level || 0) * 0.1 + (item.wave_height || 0) * 0.05;
    
    return {
      time: index,
      timestamp: item.timestamp,
      risk_score: Math.min(1, Math.max(0, riskScore + (Math.random() - 0.5) * 0.1 + variation)),
      tide_level: item.tide_level || 0,
      wave_height: item.wave_height || 0,
      wind_speed: item.wind_speed || 0,
      confidence: getConfidence(),
    };
  });

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      const trend = getTrend();
      const trendIcon = trend === 'increasing' ? '↗️' : trend === 'decreasing' ? '↘️' : '→';
      
      return (
        <div className="bg-white p-3 border border-gray-200 rounded-lg shadow-lg">
          <p className="font-medium text-gray-900">
            {new Date(data.timestamp).toLocaleTimeString()}
          </p>
          <div className="space-y-1 mt-2">
            <p className="text-sm">
              <span className="text-red-600 font-medium">Risk:</span> {(data.risk_score * 100).toFixed(1)}% {trendIcon}
            </p>
            <p className="text-sm">
              <span className="text-gray-600 font-medium">Confidence:</span> {(data.confidence * 100).toFixed(1)}%
            </p>
            <p className="text-sm">
              <span className="text-blue-600 font-medium">Tide:</span> {data.tide_level.toFixed(1)}m
            </p>
            <p className="text-sm">
              <span className="text-green-600 font-medium">Wave:</span> {data.wave_height.toFixed(1)}m
            </p>
            <p className="text-sm">
              <span className="text-purple-600 font-medium">Wind:</span> {data.wind_speed.toFixed(1)} km/h
            </p>
          </div>
        </div>
      );
    }
    return null;
  };

  if (chartData.length === 0) {
    return (
      <div className="flex items-center justify-center h-64 text-gray-500">
        <div className="text-center">
          <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
          </div>
          <p className="text-sm">No data available</p>
          <p className="text-xs text-gray-400">Upload data or wait for API updates</p>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full h-64">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
          <defs>
            <linearGradient id="riskGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#ef4444" stopOpacity={0.8}/>
              <stop offset="95%" stopColor="#ef4444" stopOpacity={0.1}/>
            </linearGradient>
            <linearGradient id="tideGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#0ea5e9" stopOpacity={0.8}/>
              <stop offset="95%" stopColor="#0ea5e9" stopOpacity={0.1}/>
            </linearGradient>
          </defs>
          
          <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" />
          
          <XAxis 
            dataKey="time" 
            stroke="#6b7280"
            fontSize={12}
            tickFormatter={(value) => {
              if (chartData[value]) {
                return new Date(chartData[value].timestamp).toLocaleTimeString([], { 
                  hour: '2-digit', 
                  minute: '2-digit' 
                });
              }
              return '';
            }}
          />
          
          <YAxis 
            stroke="#6b7280"
            fontSize={12}
            domain={[0, 1]}
            tickFormatter={(value) => `${(value * 100).toFixed(0)}%`}
          />
          
          <Tooltip content={<CustomTooltip />} />
          
          {/* Risk Score Area */}
          <Area
            type="monotone"
            dataKey="risk_score"
            stroke="#ef4444"
            strokeWidth={3}
            fill="url(#riskGradient)"
            name="Risk Score"
            isAnimationActive={false}
          />
          
          {/* Tide Level Line */}
          <Line
            type="monotone"
            dataKey="tide_level"
            stroke="#0ea5e9"
            strokeWidth={2}
            strokeDasharray="5 5"
            dot={false}
            name="Tide Level"
            isAnimationActive={false}
          />
          
          {/* Wave Height Line */}
          <Line
            type="monotone"
            dataKey="wave_height"
            stroke="#10b981"
            strokeWidth={2}
            strokeDasharray="3 3"
            dot={false}
            name="Wave Height"
            isAnimationActive={false}
          />
        </AreaChart>
      </ResponsiveContainer>
      
      {/* Legend */}
      <div className="flex items-center justify-center space-x-6 mt-4 text-sm">
        <div className="flex items-center space-x-2">
          <div className="w-3 h-3 bg-red-500 rounded-full"></div>
          <span className="text-gray-600">Risk Score</span>
        </div>
        <div className="flex items-center space-x-2">
          <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
          <span className="text-gray-600">Tide Level</span>
        </div>
        <div className="flex items-center space-x-2">
          <div className="w-3 h-3 bg-green-500 rounded-full"></div>
          <span className="text-gray-600">Wave Height</span>
        </div>
      </div>
    </div>
  );
};

export default RiskChart;



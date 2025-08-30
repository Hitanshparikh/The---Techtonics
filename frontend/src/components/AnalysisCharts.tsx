import React from 'react';
import {
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
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

interface AnalysisChartsProps {
  analysisData: any;
}

const AnalysisCharts: React.FC<AnalysisChartsProps> = ({ analysisData }) => {
  // Generate sample time series data for visualization
  const generateTimeSeriesData = () => {
    return analysisData.predictions?.map((pred: any, index: number) => ({
      time: pred.time_horizon,
      riskScore: pred.predicted_value,
      confidence: pred.confidence,
      timeIndex: index
    })) || [];
  };

  // Generate risk factor data
  const generateRiskFactorData = () => {
    return analysisData.risk_analysis?.risk_factors?.map((factor: any) => ({
      name: factor.factor.replace(/_/g, ' ').replace(/\b\w/g, (l: string) => l.toUpperCase()),
      correlation: Math.abs(factor.correlation),
      impact: factor.impact === 'HIGH' ? 0.8 : factor.impact === 'MEDIUM' ? 0.5 : 0.3
    })) || [];
  };

  // Generate anomaly distribution data
  const generateAnomalyData = () => {
    const totalRecords = analysisData.total_records || 100;
    const anomalies = analysisData.anomalies?.total_anomalies || 0;
    return [
      { name: 'Normal Data', value: totalRecords - anomalies, color: '#10B981' },
      { name: 'Anomalies', value: anomalies, color: '#EF4444' }
    ];
  };

  // Generate statistical overview data
  const generateStatisticalData = () => {
    const stats = analysisData.statistical_summary || {};
    return Object.keys(stats).slice(0, 6).map(key => ({
      metric: key.replace(/_/g, ' ').replace(/\b\w/g, (l: string) => l.toUpperCase()),
      mean: stats[key]?.mean || 0,
      std: stats[key]?.std || 0,
      min: stats[key]?.min || 0,
      max: stats[key]?.max || 0
    }));
  };

  const timeSeriesData = generateTimeSeriesData();
  const riskFactorData = generateRiskFactorData();
  const anomalyData = generateAnomalyData();
  const statisticalData = generateStatisticalData();

  return (
    <div className="space-y-8">
      {/* Risk Prediction Timeline */}
      <div className="bg-white p-6 rounded-lg shadow-sm border">
        <h3 className="text-lg font-semibold mb-4 text-gray-800">
          Risk Prediction Timeline
        </h3>
        <ResponsiveContainer width="100%" height={300}>
          <AreaChart data={timeSeriesData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="time" />
            <YAxis domain={[0, 1]} />
            <Tooltip 
              formatter={(value: number, name: string) => [
                `${(value * 100).toFixed(1)}%`,
                name === 'riskScore' ? 'Risk Score' : 'Confidence'
              ]}
            />
            <Legend />
            <Area
              type="monotone"
              dataKey="riskScore"
              stroke="#EF4444"
              fill="#FEE2E2"
              strokeWidth={2}
              name="Risk Score"
            />
            <Line
              type="monotone"
              dataKey="confidence"
              stroke="#10B981"
              strokeWidth={2}
              name="Confidence"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Risk Factors Analysis */}
      <div className="bg-white p-6 rounded-lg shadow-sm border">
        <h3 className="text-lg font-semibold mb-4 text-gray-800">
          Risk Factor Correlation
        </h3>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={riskFactorData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="name" />
            <YAxis domain={[0, 1]} />
            <Tooltip formatter={(value: number) => [`${(value * 100).toFixed(1)}%`, 'Correlation']} />
            <Bar dataKey="correlation" fill="#8B5CF6" />
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Anomaly Distribution */}
        <div className="bg-white p-6 rounded-lg shadow-sm border">
          <h3 className="text-lg font-semibold mb-4 text-gray-800">
            Data Quality Distribution
          </h3>
          <ResponsiveContainer width="100%" height={250}>
            <PieChart>
              <Pie
                data={anomalyData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {anomalyData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Statistical Summary */}
        <div className="bg-white p-6 rounded-lg shadow-sm border">
          <h3 className="text-lg font-semibold mb-4 text-gray-800">
            Statistical Summary
          </h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={statisticalData} layout="horizontal">
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis type="number" />
              <YAxis dataKey="metric" type="category" width={80} />
              <Tooltip />
              <Bar dataKey="mean" fill="#06B6D4" name="Mean" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Trend Analysis */}
      <div className="bg-white p-6 rounded-lg shadow-sm border">
        <h3 className="text-lg font-semibold mb-4 text-gray-800">
          Trend Analysis Summary
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="text-center p-4 bg-blue-50 rounded-lg">
            <div className="text-2xl font-bold text-blue-600">
              {analysisData.trend_analysis?.trend_direction || 'STABLE'}
            </div>
            <div className="text-sm text-blue-700">Overall Trend</div>
          </div>
          <div className="text-center p-4 bg-green-50 rounded-lg">
            <div className="text-2xl font-bold text-green-600">
              {analysisData.trend_analysis?.increasing_metrics?.length || 0}
            </div>
            <div className="text-sm text-green-700">Increasing Metrics</div>
          </div>
          <div className="text-center p-4 bg-red-50 rounded-lg">
            <div className="text-2xl font-bold text-red-600">
              {analysisData.trend_analysis?.decreasing_metrics?.length || 0}
            </div>
            <div className="text-sm text-red-700">Decreasing Metrics</div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AnalysisCharts;

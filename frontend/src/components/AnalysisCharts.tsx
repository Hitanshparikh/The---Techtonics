import React, { useEffect, useState } from 'react';
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
  const [correlationData, setCorrelationData] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  // Fetch real-time correlation data
  useEffect(() => {
    const fetchCorrelationData = async () => {
      if (analysisData?.dataset_id) {
        setLoading(true);
        try {
          const response = await fetch(`/api/ml/correlations/${analysisData.dataset_id}`);
          if (response.ok) {
            const data = await response.json();
            setCorrelationData(data);
          }
        } catch (error) {
          console.error('Error fetching correlation data:', error);
        } finally {
          setLoading(false);
        }
      }
    };

    fetchCorrelationData();
  }, [analysisData?.dataset_id]);
  // Generate sample time series data for visualization with real ML predictions
  const generateTimeSeriesData = () => {
    // First try to use forecast data from ml_predictions
    if (analysisData.ml_predictions?.forecast && analysisData.ml_predictions.forecast.length > 0) {
      return analysisData.ml_predictions.forecast.map((pred: any) => ({
        time: `Period ${pred.period}`,
        riskScore: pred.predicted_value,
        confidence: pred.confidence_interval ? 
          (pred.confidence_interval[1] - pred.confidence_interval[0]) / 2 : 
          analysisData.ml_predictions.confidence || 0.7,
        timeIndex: pred.period
      }));
    }
    
    // Fallback to predictions array
    return analysisData.predictions?.slice(0, 10).map((pred: any, index: number) => ({
      time: pred.time_horizon || `Period ${index + 1}`,
      riskScore: pred.predicted_value || pred.risk_score || 0.5,
      confidence: pred.confidence || 0.7,
      timeIndex: index
    })) || [];
  };

  // Generate risk factor data from real-time correlations
  const generateRiskFactorData = () => {
    if (correlationData?.risk_impacts && correlationData.risk_impacts.length > 0) {
      return correlationData.risk_impacts.slice(0, 10).map((factor: any) => ({
        name: factor.factor.replace(/_/g, ' ').replace(/\b\w/g, (l: string) => l.toUpperCase()),
        correlation: Math.abs(factor.risk_correlation),
        impact: factor.risk_level === 'HIGH' ? 0.8 : factor.risk_level === 'MEDIUM' ? 0.5 : 0.3,
        direction: factor.impact_direction,
        confidence: factor.confidence
      }));
    }
    
    // Fallback to original data if real-time not available
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

  // Generate statistical overview data with real values
  const generateStatisticalData = () => {
    const stats = analysisData.statistical_summary || {};
    const data: Array<{
      metric: string;
      mean: number;
      std: number;
      min: number;
      max: number;
    }> = [];
    
    // Process each statistical feature
    Object.keys(stats).forEach(key => {
      if (stats[key] && typeof stats[key] === 'object' && stats[key].mean !== undefined) {
        data.push({
          metric: key.replace(/_/g, ' ').replace(/\b\w/g, (l: string) => l.toUpperCase()),
          mean: Number(stats[key].mean) || 0,
          std: Number(stats[key].std) || 0,
          min: Number(stats[key].min) || 0,
          max: Number(stats[key].max) || 0
        });
      }
    });
    
    // If no statistical data, create from correlation data
    if (data.length === 0 && correlationData?.correlations) {
      correlationData.correlations.slice(0, 6).forEach((corr: any) => {
        data.push({
          metric: corr.factor1,
          mean: Math.abs(corr.correlation),
          std: Math.abs(corr.correlation) * 0.2,
          min: 0,
          max: 1
        });
      });
    }
    
    return data.slice(0, 6);
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

      {/* Risk Factors Analysis - Real-time */}
      <div className="bg-white p-6 rounded-lg shadow-sm border">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold text-gray-800">
            Risk Factor Correlation {correlationData && '(Real-time)'}
          </h3>
          {loading && (
            <div className="text-sm text-blue-600">
              Loading real-time data...
            </div>
          )}
        </div>
        
        {correlationData?.error ? (
          <div className="text-red-600 text-sm">
            {correlationData.error}
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={riskFactorData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="name" 
                angle={-45}
                textAnchor="end"
                height={100}
                interval={0}
              />
              <YAxis domain={[0, 1]} />
              <Tooltip 
                formatter={(value: number, name: string) => {
                  if (name === 'correlation') {
                    return [`${(value * 100).toFixed(1)}%`, 'Correlation Strength'];
                  }
                  return [value, name];
                }}
                labelFormatter={(label) => `Factor: ${label}`}
              />
              <Bar 
                dataKey="correlation" 
                fill="#8B5CF6"
                name="correlation"
              />
            </BarChart>
          </ResponsiveContainer>
        )}
        
        {correlationData?.analysis_summary && (
          <div className="mt-4 text-sm text-gray-600">
            <div className="grid grid-cols-3 gap-4">
              <div>Total Factors: {correlationData.analysis_summary.total_factors}</div>
              <div>Significant Correlations: {correlationData.analysis_summary.significant_correlations}</div>
              <div>High Risk Factors: {correlationData.analysis_summary.high_risk_factors}</div>
            </div>
          </div>
        )}
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

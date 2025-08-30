import React, { useState, useEffect } from 'react';
import { Database, FileText, BarChart3, AlertTriangle, TrendingUp, Calendar, MapPin } from 'lucide-react';
import AnalysisCharts from '../components/AnalysisCharts.tsx';

interface Dataset {
  id: string;
  name: string;
  description: string;
  source_type: string;
  total_records: number;
  status: string;
  created_at: string;
  region: string;
}

const Datasets: React.FC = () => {
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [selectedDataset, setSelectedDataset] = useState<string | null>(null);
  const [analysisData, setAnalysisData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [analysisLoading, setAnalysisLoading] = useState(false);

  useEffect(() => {
    fetchDatasets();
  }, []);

  const fetchDatasets = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/v1/upload/datasets');
      const data = await response.json();
      setDatasets(data.datasets || []);
    } catch (error) {
      console.error('Error fetching datasets:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchAnalysis = async (datasetId: string) => {
    setAnalysisLoading(true);
    try {
      const response = await fetch(`http://localhost:8000/api/v1/ml/analyze-dataset/${datasetId}`);
      const data = await response.json();
      setAnalysisData(data);
      setSelectedDataset(datasetId);
    } catch (error) {
      console.error('Error fetching analysis:', error);
    } finally {
      setAnalysisLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
      case 'completed':
        return 'bg-green-100 text-green-800';
      case 'processing':
        return 'bg-yellow-100 text-yellow-800';
      case 'failed':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getRiskLevelColor = (riskLevel: string) => {
    switch (riskLevel?.toUpperCase()) {
      case 'HIGH':
        return 'text-red-600 bg-red-50 border-red-200';
      case 'MEDIUM':
        return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      case 'LOW':
        return 'text-green-600 bg-green-50 border-green-200';
      default:
        return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Dataset Management</h1>
        <p className="mt-1 text-sm text-gray-500">
          View and analyze your uploaded coastal monitoring datasets
        </p>
      </div>

      {/* Dataset Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-1">
          <h2 className="text-lg font-semibold mb-4">Datasets</h2>
          <div className="space-y-4">
            {datasets.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <Database className="mx-auto h-12 w-12 text-gray-400 mb-4" />
                <p>No datasets uploaded yet</p>
                <p className="text-sm">Upload your first dataset to get started</p>
              </div>
            ) : (
              datasets.map((dataset) => (
                <div
                  key={dataset.id}
                  className={`p-4 border rounded-lg cursor-pointer transition-all hover:shadow-md ${
                    selectedDataset === dataset.id
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                  onClick={() => fetchAnalysis(dataset.id)}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <h3 className="font-medium text-gray-900">{dataset.name}</h3>
                      <p className="text-sm text-gray-600 mt-1">{dataset.description}</p>
                      
                      <div className="mt-3 flex items-center space-x-4 text-xs text-gray-500">
                        <div className="flex items-center">
                          <FileText className="w-3 h-3 mr-1" />
                          {dataset.total_records} records
                        </div>
                        <div className="flex items-center">
                          <MapPin className="w-3 h-3 mr-1" />
                          {dataset.region}
                        </div>
                        <div className="flex items-center">
                          <Calendar className="w-3 h-3 mr-1" />
                          {new Date(dataset.created_at).toLocaleDateString()}
                        </div>
                      </div>
                    </div>
                    <span
                      className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(
                        dataset.status
                      )}`}
                    >
                      {dataset.status}
                    </span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Analysis Panel */}
        <div className="lg:col-span-2">
          {!selectedDataset ? (
            <div className="text-center py-16 text-gray-500">
              <BarChart3 className="mx-auto h-16 w-16 text-gray-400 mb-4" />
              <h3 className="text-lg font-medium mb-2">Select a Dataset</h3>
              <p>Choose a dataset from the left panel to view its AI analysis and visualizations</p>
            </div>
          ) : analysisLoading ? (
            <div className="flex items-center justify-center py-16">
              <div className="text-center">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
                <p className="text-gray-600">Analyzing dataset...</p>
              </div>
            </div>
          ) : analysisData ? (
            <div className="space-y-6">
              {/* Analysis Summary */}
              <div className="bg-white p-6 rounded-lg border border-gray-200">
                <h2 className="text-xl font-semibold mb-4">Analysis Summary</h2>
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                  <div className="text-center p-4 bg-blue-50 rounded-lg">
                    <div className="text-2xl font-bold text-blue-600">
                      {analysisData.data_quality_score}%
                    </div>
                    <div className="text-sm text-blue-700">Data Quality</div>
                  </div>
                  <div className={`text-center p-4 rounded-lg border ${getRiskLevelColor(analysisData.risk_level)}`}>
                    <div className="text-2xl font-bold">
                      {analysisData.risk_level}
                    </div>
                    <div className="text-sm">Risk Level</div>
                  </div>
                  <div className="text-center p-4 bg-purple-50 rounded-lg">
                    <div className="text-2xl font-bold text-purple-600">
                      {analysisData.anomalies?.total_anomalies || 0}
                    </div>
                    <div className="text-sm text-purple-700">Anomalies</div>
                  </div>
                  <div className="text-center p-4 bg-green-50 rounded-lg">
                    <div className="text-2xl font-bold text-green-600">
                      {analysisData.predictions_count || 0}
                    </div>
                    <div className="text-sm text-green-700">Predictions</div>
                  </div>
                </div>
              </div>

              {/* Key Insights */}
              {analysisData.insights && (
                <div className="bg-white p-6 rounded-lg border border-gray-200">
                  <h3 className="text-lg font-semibold mb-4 flex items-center">
                    <TrendingUp className="w-5 h-5 text-blue-600 mr-2" />
                    Key Insights
                  </h3>
                  <ul className="space-y-2">
                    {analysisData.insights.map((insight: string, index: number) => (
                      <li key={index} className="flex items-start">
                        <span className="text-blue-600 mr-2 mt-1">•</span>
                        <span className="text-gray-700">{insight}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Alerts */}
              {analysisData.alerts && analysisData.alerts.length > 0 && (
                <div className="bg-white p-6 rounded-lg border border-gray-200">
                  <h3 className="text-lg font-semibold mb-4 flex items-center text-red-600">
                    <AlertTriangle className="w-5 h-5 mr-2" />
                    Active Alerts
                  </h3>
                  <div className="space-y-3">
                    {analysisData.alerts.map((alert: any, index: number) => (
                      <div key={index} className="p-4 bg-red-50 border border-red-200 rounded-lg">
                        <div className="flex items-start justify-between">
                          <div>
                            <div className="font-medium text-red-800">{alert.type}</div>
                            <div className="text-red-700 mt-1">{alert.message}</div>
                          </div>
                          <div className="text-sm text-red-600">
                            Risk: {(alert.risk_score * 100).toFixed(0)}%
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Analysis Charts */}
              <div className="bg-white p-6 rounded-lg border border-gray-200">
                <h3 className="text-lg font-semibold mb-6 flex items-center">
                  <BarChart3 className="w-5 h-5 text-blue-600 mr-2" />
                  Data Visualizations
                </h3>
                <AnalysisCharts analysisData={analysisData} />
              </div>
            </div>
          ) : null}
        </div>
      </div>
    </div>
  );
};

export default Datasets;

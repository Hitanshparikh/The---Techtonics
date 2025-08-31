import React, { useState } from 'react';
import { Upload as UploadIcon, Link, FileText, Database, AlertCircle, BarChart3, TrendingUp, Brain } from 'lucide-react';
import toast from 'react-hot-toast';
import AnalysisCharts from '../components/AnalysisCharts';

const Upload: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'file' | 'api'>('file');
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [analysisResult, setAnalysisResult] = useState<any>(null);
  const [showAnalysis, setShowAnalysis] = useState(false);

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    // Validate file type
    const allowedTypes = ['.csv', '.xlsx', '.xls'];
    const fileExtension = file.name.toLowerCase().slice(file.name.lastIndexOf('.'));
    
    if (!allowedTypes.includes(fileExtension)) {
      toast.error('Please upload a CSV or Excel file');
      return;
    }

    // Validate file size (50MB)
    if (file.size > 50 * 1024 * 1024) {
      toast.error('File size must be less than 50MB');
      return;
    }

    setIsUploading(true);
    setUploadProgress(0);
    setShowAnalysis(false);
    
    try {
      // Create form data
      const formData = new FormData();
      formData.append('file', file);
      formData.append('dataset_name', `Uploaded Dataset - ${new Date().toLocaleString()}`);
      formData.append('description', 'Coastal data uploaded via web interface');
      formData.append('region', 'All');

      // Simulate progress
      const progressInterval = setInterval(() => {
        setUploadProgress(prev => {
          if (prev >= 90) {
            clearInterval(progressInterval);
            return 90;
          }
          return prev + 10;
        });
      }, 200);

      // Upload file
      const response = await fetch('http://localhost:8000/api/v1/upload/file', {
        method: 'POST',
        body: formData,
      });

      clearInterval(progressInterval);

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Upload failed');
      }

      const result = await response.json();
      setUploadProgress(100);
      
      toast.success('File uploaded successfully! Processing...');
      
      // Poll for processing progress
      const pollProgress = async (datasetId: string) => {
        try {
          const statusResponse = await fetch(`http://localhost:8000/api/v1/upload/status/${datasetId}`);
          if (statusResponse.ok) {
            const status = await statusResponse.json();
            
            if (status.progress_percentage !== undefined) {
              setUploadProgress(Math.max(90, status.progress_percentage));
            }
            
            if (status.status === 'completed') {
              setUploadProgress(100);
              toast.success('Processing completed!');
              
              // Get analysis after completion
              setTimeout(async () => {
                try {
                  const analysisResponse = await fetch(`http://localhost:8000/api/v1/ml/analyze-dataset/${datasetId}`);
                  if (analysisResponse.ok) {
                    const analysis = await analysisResponse.json();
                    setAnalysisResult(analysis);
                    setShowAnalysis(true);
                    toast.success('AI analysis completed!');
                  }
                } catch (error) {
                  console.error('Analysis error:', error);
                }
              }, 1000);
              
              return true; // Stop polling
            } else if (status.status === 'failed') {
              toast.error('Processing failed');
              return true; // Stop polling
            } else {
              // Continue polling
              setTimeout(() => pollProgress(datasetId), 1000);
            }
          }
        } catch (error) {
          console.error('Status check error:', error);
          setTimeout(() => pollProgress(datasetId), 2000);
        }
        return false;
      };
      
      // Start polling
      await pollProgress(result.dataset_id);

    } catch (error: any) {
      console.error('Upload error:', error);
      toast.error(error.message || 'Upload failed');
    } finally {
      setIsUploading(false);
    }
  };

  const handleApiSetup = async (event: React.FormEvent) => {
    event.preventDefault();
    setIsUploading(true);
    
    // Simulate API setup
    setTimeout(() => {
      setIsUploading(false);
      toast.success('API ingestion setup successfully!');
    }, 2000);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Data Upload & API Setup</h1>
        <p className="mt-1 text-sm text-gray-500">
          Upload CSV/Excel files or configure API endpoints for data ingestion
        </p>
      </div>

      {/* Tab Navigation */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          <button
            onClick={() => setActiveTab('file')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'file'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            <FileText className="w-4 h-4 inline mr-2" />
            File Upload
          </button>
          <button
            onClick={() => setActiveTab('api')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'api'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            <Link className="w-4 h-4 inline mr-2" />
            API Setup
          </button>
        </nav>
      </div>

      {/* AI Analysis Results */}
      {showAnalysis && analysisResult && (
        <div className="mb-8 p-6 bg-gradient-to-r from-green-50 to-blue-50 rounded-lg border border-green-200">
          <div className="flex items-center mb-4">
            <Brain className="w-6 h-6 text-green-600 mr-3" />
            <h2 className="text-xl font-semibold text-gray-800">AI Analysis Results</h2>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <div className="bg-white p-4 rounded-lg shadow-sm">
              <div className="flex items-center mb-2">
                <Database className="w-5 h-5 text-blue-600 mr-2" />
                <span className="font-semibold">Data Quality</span>
              </div>
              <div className="text-2xl font-bold text-blue-600">{analysisResult.data_quality_score || 95}%</div>
              <p className="text-sm text-gray-600">Quality Score</p>
            </div>
            
            <div className="bg-white p-4 rounded-lg shadow-sm">
              <div className="flex items-center mb-2">
                <AlertCircle className="w-5 h-5 text-red-600 mr-2" />
                <span className="font-semibold">Risk Level</span>
              </div>
              <div className="text-2xl font-bold text-red-600">{analysisResult.risk_level || 'MEDIUM'}</div>
              <p className="text-sm text-gray-600">Threat Assessment</p>
            </div>
            
            <div className="bg-white p-4 rounded-lg shadow-sm">
              <div className="flex items-center mb-2">
                <TrendingUp className="w-5 h-5 text-green-600 mr-2" />
                <span className="font-semibold">Predictions</span>
              </div>
              <div className="text-2xl font-bold text-green-600">{analysisResult.predictions_count || 12}</div>
              <p className="text-sm text-gray-600">Generated</p>
            </div>
          </div>

          {analysisResult.insights && (
            <div className="bg-white p-4 rounded-lg shadow-sm">
              <h3 className="font-semibold mb-2 flex items-center">
                <BarChart3 className="w-5 h-5 text-purple-600 mr-2" />
                Key Insights
              </h3>
              <ul className="space-y-2">
                {analysisResult.insights.map((insight: string, index: number) => (
                  <li key={index} className="text-gray-700 flex items-start">
                    <span className="text-purple-600 mr-2">•</span>
                    {insight}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {analysisResult.alerts && analysisResult.alerts.length > 0 && (
            <div className="bg-white p-4 rounded-lg shadow-sm mt-4">
              <h3 className="font-semibold mb-2 flex items-center text-red-600">
                <AlertCircle className="w-5 h-5 mr-2" />
                Generated Alerts
              </h3>
              <div className="space-y-2">
                {analysisResult.alerts.map((alert: any, index: number) => (
                  <div key={index} className="p-3 bg-red-50 border border-red-200 rounded">
                    <div className="font-medium text-red-800">{alert.type}</div>
                    <div className="text-red-700">{alert.message}</div>
                    <div className="text-sm text-red-600 mt-1">Risk Score: {alert.risk_score}</div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Analysis Charts */}
      {showAnalysis && analysisResult && (
        <div className="mb-8">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-semibold text-gray-800 flex items-center">
              <BarChart3 className="w-6 h-6 text-blue-600 mr-3" />
              Real-time Analysis Visualizations
            </h2>
          </div>
          <AnalysisCharts analysisData={analysisResult} />
        </div>
      )}

      {/* File Upload Tab */}
      {activeTab === 'file' && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="text-center">
            <UploadIcon className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">Upload Coastal Data</h3>
            <p className="mt-1 text-sm text-gray-500">
              Upload CSV or Excel files containing coastal monitoring data
            </p>
          </div>

          <div className="mt-6">
            <div className="flex justify-center">
              <div className="w-full max-w-lg">
                <label className="block w-full">
                  <div className="mt-1 flex justify-center px-6 pt-5 pb-6 border-2 border-gray-300 border-dashed rounded-md hover:border-gray-400 transition-colors duration-200">
                    <div className="space-y-1 text-center">
                      <UploadIcon className="mx-auto h-12 w-12 text-gray-400" />
                      <div className="flex text-sm text-gray-600">
                        <label className="relative cursor-pointer bg-white rounded-md font-medium text-blue-600 hover:text-blue-500 focus-within:outline-none focus-within:ring-2 focus-within:ring-offset-2 focus-within:ring-blue-500">
                          <span>Upload a file</span>
                          <input
                            type="file"
                            className="sr-only"
                            accept=".csv,.xlsx,.xls"
                            onChange={handleFileUpload}
                            disabled={isUploading}
                          />
                        </label>
                        <p className="pl-1">or drag and drop</p>
                      </div>
                      <p className="text-xs text-gray-500">CSV, Excel up to 50MB</p>
                    </div>
                  </div>
                </label>
              </div>
            </div>
          </div>

          {/* Upload Progress */}
          {isUploading && (
            <div className="mt-6">
              <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
                <div className="flex items-center">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600 mr-3"></div>
                  <span className="text-sm text-blue-800">Processing file...</span>
                </div>
                <div className="mt-2 w-full bg-blue-200 rounded-full h-2">
                                  <div className="bg-gray-200 rounded-full h-2">
                  <div 
                    className="bg-blue-600 h-2 rounded-full animate-pulse transition-all duration-300" 
                    style={{ width: `${uploadProgress}%` }}
                  ></div>
                </div>
                </div>
              </div>
            </div>
          )}

          {/* File Requirements */}
          <div className="mt-6 bg-gray-50 rounded-md p-4">
            <h4 className="text-sm font-medium text-gray-900 mb-2">File Requirements</h4>
            <ul className="text-sm text-gray-600 space-y-1">
              <li>• Supported formats: CSV, Excel (.xlsx, .xls)</li>
              <li>• Maximum file size: 50MB</li>
              <li>• Required columns: timestamp, latitude, longitude</li>
              <li>• Optional columns: tide_level, wave_height, wind_speed, etc.</li>
              <li>• Data will be automatically analyzed for risk assessment</li>
            </ul>
          </div>
        </div>
      )}

      {/* API Setup Tab */}
      {activeTab === 'api' && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="text-center mb-6">
            <Database className="mx-auto h-12 w-12 text-blue-600" />
            <h3 className="mt-2 text-lg font-medium text-gray-900">API Endpoint Setup</h3>
            <p className="mt-1 text-sm text-gray-500">
              Configure API endpoints for continuous data ingestion
            </p>
          </div>

          <form onSubmit={handleApiSetup} className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                API Endpoint URL
              </label>
              <input
                type="url"
                required
                placeholder="https://api.example.com/coastal-data"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Dataset Name
                </label>
                <input
                  type="text"
                  required
                  placeholder="Gujarat Weather API"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Refresh Interval (minutes)
                </label>
                <select 
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  aria-label="Select API method"
                >
                  <option value="5">5 minutes</option>
                  <option value="15">15 minutes</option>
                  <option value="30">30 minutes</option>
                  <option value="60" selected>1 hour</option>
                  <option value="240">4 hours</option>
                </select>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Description (Optional)
              </label>
              <textarea
                rows={3}
                placeholder="Describe the data source and what it monitors..."
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Region
              </label>
              <select 
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                aria-label="Select refresh interval"
              >
                <option value="">Select region</option>
                <option value="Mumbai">Mumbai</option>
                <option value="Gujarat">Gujarat</option>
                <option value="Other">Other</option>
              </select>
            </div>

            <div className="flex justify-end">
              <button
                type="submit"
                disabled={isUploading}
                className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200"
              >
                {isUploading ? 'Setting up...' : 'Setup API Ingestion'}
              </button>
            </div>
          </form>

          {/* API Status */}
          {isUploading && (
            <div className="mt-6">
              <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
                <div className="flex items-center">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600 mr-3"></div>
                  <span className="text-sm text-blue-800">Configuring API endpoint...</span>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Recent Uploads */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">Recent Uploads</h3>
        </div>
        <div className="p-6">
          <div className="text-center text-gray-500 py-8">
            <Database className="mx-auto h-12 w-12 text-gray-300 mb-4" />
            <p className="text-sm">No recent uploads</p>
            <p className="text-xs text-gray-400">Upload your first file or setup an API endpoint</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Upload;



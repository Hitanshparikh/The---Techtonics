const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Helper function for API calls
async function apiCall(endpoint: string, options: RequestInit = {}) {
  const url = `${API_BASE_URL}/api/v1${endpoint}`;
  
  try {
    const response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    });

    if (!response.ok) {
      throw new Error(`API call failed: ${response.status} ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error('API call error:', error);
    throw error;
  }
}

// Coastal Data API
export const fetchCoastalData = async (params: {
  limit?: number;
  offset?: number;
  region?: string;
  start_date?: string;
  end_date?: string;
  min_risk?: number;
  max_risk?: number;
}) => {
  const searchParams = new URLSearchParams();
  
  if (params.limit) searchParams.append('limit', params.limit.toString());
  if (params.offset) searchParams.append('offset', params.offset.toString());
  if (params.region) searchParams.append('region', params.region);
  if (params.start_date) searchParams.append('start_date', params.start_date);
  if (params.end_date) searchParams.append('end_date', params.end_date);
  if (params.min_risk) searchParams.append('min_risk', params.min_risk.toString());
  if (params.max_risk) searchParams.append('max_risk', params.max_risk.toString());

  const endpoint = `/data?${searchParams.toString()}`;
  return apiCall(endpoint);
};

export const fetchLatestData = async (limit: number = 10) => {
  return apiCall(`/data/latest?limit=${limit}`);
};

export const fetchRegions = async () => {
  return apiCall('/data/regions');
};

export const fetchStatistics = async (region?: string) => {
  const endpoint = region ? `/data/statistics?region=${region}` : '/data/statistics';
  return apiCall(endpoint);
};

export const fetchTrends = async (params: {
  region?: string;
  hours: number;
}) => {
  const searchParams = new URLSearchParams();
  if (params.region) searchParams.append('region', params.region);
  searchParams.append('hours', params.hours.toString());

  const endpoint = `/data/trends?${searchParams.toString()}`;
  return apiCall(endpoint);
};

export const fetchAnomalies = async (params: {
  region?: string;
  limit?: number;
}) => {
  const searchParams = new URLSearchParams();
  if (params.region) searchParams.append('region', params.region);
  if (params.limit) searchParams.append('limit', params.limit.toString());

  const endpoint = `/data/anomalies?${searchParams.toString()}`;
  return apiCall(endpoint);
};

export const fetchHeatmapData = async (region?: string) => {
  const endpoint = region ? `/data/heatmap?region=${region}` : '/data/heatmap';
  return apiCall(endpoint);
};

// Upload API
export const uploadFile = async (formData: FormData) => {
  const url = `${API_BASE_URL}/api/v1/upload/file`;
  
  try {
    const response = await fetch(url, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`Upload failed: ${response.status} ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Upload error:', error);
    throw error;
  }
};

export const setupApiIngestion = async (data: {
  api_url: string;
  dataset_name: string;
  description?: string;
  region?: string;
  refresh_interval: number;
}) => {
  const formData = new FormData();
  formData.append('api_url', data.api_url);
  formData.append('dataset_name', data.dataset_name);
  if (data.description) formData.append('description', data.description);
  if (data.region) formData.append('region', data.region);
  formData.append('refresh_interval', data.refresh_interval.toString());

  const url = `${API_BASE_URL}/api/v1/upload/api`;
  
  try {
    const response = await fetch(url, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`API setup failed: ${response.status} ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error('API setup error:', error);
    throw error;
  }
};

export const getUploadStatus = async (datasetId: string) => {
  return apiCall(`/upload/status/${datasetId}`);
};

export const listDatasets = async (params: {
  limit?: number;
  offset?: number;
}) => {
  const searchParams = new URLSearchParams();
  if (params.limit) searchParams.append('limit', params.limit.toString());
  if (params.offset) searchParams.append('offset', params.offset.toString());

  const endpoint = `/upload/datasets?${searchParams.toString()}`;
  return apiCall(endpoint);
};

export const deleteDataset = async (datasetId: string) => {
  return apiCall(`/upload/dataset/${datasetId}`, { method: 'DELETE' });
};

// ML Models API
export const trainModel = async (data: {
  model_name?: string;
  dataset_id?: string;
}) => {
  const formData = new FormData();
  if (data.model_name) formData.append('model_name', data.model_name);
  if (data.dataset_id) formData.append('dataset_id', data.dataset_id);

  const url = `${API_BASE_URL}/api/v1/ml/train`;
  
  try {
    const response = await fetch(url, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`Model training failed: ${response.status} ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Model training error:', error);
    throw error;
  }
};

export const makePrediction = async (data: {
  data: Record<string, any>;
  model_name?: string;
}) => {
  return apiCall('/ml/predict', {
    method: 'POST',
    body: JSON.stringify(data),
  });
};

export const retrainModel = async (data: {
  model_name?: string;
  new_data_size?: number;
}) => {
  const formData = new FormData();
  if (data.model_name) formData.append('model_name', data.model_name);
  if (data.new_data_size) formData.append('new_data_size', data.new_data_size.toString());

  const url = `${API_BASE_URL}/api/v1/ml/retrain`;
  
  try {
    const response = await fetch(url, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`Model retraining failed: ${response.status} ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Model retraining error:', error);
    throw error;
  }
};

export const listModels = async () => {
  return apiCall('/ml/models');
};

export const getModelInfo = async (modelName: string) => {
  return apiCall(`/ml/models/${modelName}`);
};

export const getModelPerformance = async (modelName: string = 'default') => {
  return apiCall(`/ml/performance?model_name=${modelName}`);
};

export const detectAnomalies = async (data: {
  data: Record<string, any>[];
  features: string[];
}) => {
  return apiCall('/ml/anomaly-detection', {
    method: 'POST',
    body: JSON.stringify(data),
  });
};

// Alerts API
export const sendAlert = async (data: {
  message: string;
  alert_type: string;
  severity: string;
  channels: string[];
  region?: string;
}) => {
  const formData = new FormData();
  formData.append('message', data.message);
  formData.append('alert_type', data.alert_type);
  formData.append('severity', data.severity);
  data.channels.forEach(channel => formData.append('channels', channel));
  if (data.region) formData.append('region', data.region);

  const url = `${API_BASE_URL}/api/v1/alerts/send`;
  
  try {
    const response = await fetch(url, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`Alert sending failed: ${response.status} ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Alert sending error:', error);
    throw error;
  }
};

export const importContacts = async (file: File) => {
  const formData = new FormData();
  formData.append('file', file);

  const url = `${API_BASE_URL}/api/v1/alerts/contacts/import`;
  
  try {
    const response = await fetch(url, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`Contact import failed: ${response.status} ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Contact import error:', error);
    throw error;
  }
};

export const listContacts = async (params: {
  region?: string;
  limit?: number;
  offset?: number;
}) => {
  const searchParams = new URLSearchParams();
  if (params.region) searchParams.append('region', params.region);
  if (params.limit) searchParams.append('limit', params.limit.toString());
  if (params.offset) searchParams.append('offset', params.offset.toString());

  const endpoint = `/alerts/contacts?${searchParams.toString()}`;
  return apiCall(endpoint);
};

export const createContact = async (data: {
  name: string;
  phone?: string;
  email?: string;
  region?: string;
}) => {
  const formData = new FormData();
  formData.append('name', data.name);
  if (data.phone) formData.append('phone', data.phone);
  if (data.email) formData.append('email', data.email);
  if (data.region) formData.append('region', data.region);

  const url = `${API_BASE_URL}/api/v1/alerts/contacts`;
  
  try {
    const response = await fetch(url, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`Contact creation failed: ${response.status} ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Contact creation error:', error);
    throw error;
  }
};

export const getAlertHistory = async (params: {
  limit?: number;
  offset?: number;
  status?: string;
  alert_type?: string;
}) => {
  const searchParams = new URLSearchParams();
  if (params.limit) searchParams.append('limit', params.limit.toString());
  if (params.offset) searchParams.append('offset', params.offset.toString());
  if (params.status) searchParams.append('status', params.status);
  if (params.alert_type) searchParams.append('alert_type', params.alert_type);

  const endpoint = `/alerts/history?${searchParams.toString()}`;
  return apiCall(endpoint);
};

export const getAlertStatistics = async () => {
  return apiCall('/alerts/statistics');
};

export const testAlertSystem = async (data: {
  phone?: string;
  email?: string;
}) => {
  const formData = new FormData();
  if (data.phone) formData.append('phone', data.phone);
  if (data.email) formData.append('email', data.email);

  const url = `${API_BASE_URL}/api/v1/alerts/test`;
  
  try {
    const response = await fetch(url, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`Test alert failed: ${response.status} ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Test alert error:', error);
    throw error;
  }
};



import React from 'react';
import { AlertTriangle, Clock, MapPin } from 'lucide-react';

interface Alert {
  id: string;
  type: string;
  severity: string;
  message: string;
  location: string;
  timestamp: string;
  risk_score: number;
}

interface AlertCardProps {
  alert: Alert;
}

const AlertCard: React.FC<AlertCardProps> = ({ alert }) => {
  const getSeverityColor = (severity: string) => {
    switch (severity.toLowerCase()) {
      case 'critical':
        return 'bg-red-100 text-red-800 border-red-200';
      case 'high':
        return 'bg-orange-100 text-orange-800 border-orange-200';
      case 'medium':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'low':
        return 'bg-green-100 text-green-800 border-green-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getSeverityIcon = (severity: string) => {
    switch (severity.toLowerCase()) {
      case 'critical':
        return '🔴';
      case 'high':
        return '🟠';
      case 'medium':
        return '🟡';
      case 'low':
        return '🟢';
      default:
        return '⚪';
    }
  };

  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffInMinutes = Math.floor((now.getTime() - date.getTime()) / (1000 * 60));
    
    if (diffInMinutes < 1) return 'Just now';
    if (diffInMinutes < 60) return `${diffInMinutes}m ago`;
    if (diffInMinutes < 1440) return `${Math.floor(diffInMinutes / 60)}h ago`;
    return date.toLocaleDateString();
  };

  return (
    <div className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow duration-200">
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center space-x-2">
          <span className="text-lg">{getSeverityIcon(alert.severity)}</span>
          <span className={`px-2 py-1 text-xs font-medium rounded-full border ${getSeverityColor(alert.severity)}`}>
            {alert.severity.toUpperCase()}
          </span>
        </div>
        <div className="flex items-center space-x-1 text-xs text-gray-500">
          <Clock className="w-3 h-3" />
          <span>{formatTime(alert.timestamp)}</span>
        </div>
      </div>
      
      <h4 className="font-medium text-gray-900 mb-2 capitalize">
        {alert.type.replace('_', ' ')}
      </h4>
      
      <p className="text-sm text-gray-600 mb-3 line-clamp-2">
        {alert.message}
      </p>
      
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-1 text-xs text-gray-500">
          <MapPin className="w-3 h-3" />
          <span>{alert.location}</span>
        </div>
        
        <div className="flex items-center space-x-2">
          <span className="text-xs text-gray-500">Risk:</span>
          <span className={`px-2 py-1 text-xs font-medium rounded ${
            alert.risk_score > 0.8 ? 'bg-red-100 text-red-800' :
            alert.risk_score > 0.6 ? 'bg-orange-100 text-orange-800' :
            alert.risk_score > 0.4 ? 'bg-yellow-100 text-yellow-800' :
            'bg-green-100 text-green-800'
          }`}>
            {(alert.risk_score * 100).toFixed(0)}%
          </span>
        </div>
      </div>
    </div>
  );
};

export default AlertCard;



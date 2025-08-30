import React from 'react';
import { Bell, AlertTriangle } from 'lucide-react';

const Alerts: React.FC = () => {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Alert Management</h1>
        <p className="mt-1 text-sm text-gray-500">
          Manage notifications and alert configurations
        </p>
      </div>
      
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-12 text-center">
        <Bell className="mx-auto h-12 w-12 text-gray-400 mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">Alert Management</h3>
        <p className="text-gray-500">This page will contain alert management features.</p>
      </div>
    </div>
  );
};

export default Alerts;



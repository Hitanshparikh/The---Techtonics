import React from 'react';
import { Settings as SettingsIcon, Cog } from 'lucide-react';

const Settings: React.FC = () => {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
        <p className="mt-1 text-sm text-gray-500">
          Configure system settings and preferences
        </p>
      </div>
      
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-12 text-center">
        <SettingsIcon className="mx-auto h-12 w-12 text-gray-400 mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">System Settings</h3>
        <p className="text-gray-500">This page will contain system configuration options.</p>
      </div>
    </div>
  );
};

export default Settings;



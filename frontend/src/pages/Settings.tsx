import React, { useState, useEffect } from "react";
import { Settings as SettingsIcon, Bell, AlertTriangle, Sun, Moon, Save, RefreshCcw } from "lucide-react";

const SETTINGS_KEY = "coastal_settings_v1";

const defaultSettings = {
  threshold: 70,
  emergencyEnabled: true,
  notifications: {
    email: true,
    sms: false,
    whatsapp: true,
  },
  theme: "light" as "light" | "dark",
};

const Settings: React.FC = () => {
  const [threshold, setThreshold] = useState(defaultSettings.threshold);
  const [emergencyEnabled, setEmergencyEnabled] = useState(defaultSettings.emergencyEnabled);
  const [notifications, setNotifications] = useState(defaultSettings.notifications);
  const [theme, setTheme] = useState<"light" | "dark">(defaultSettings.theme);
  const [adminMode, setAdminMode] = useState(true);
  const [showUserModal, setShowUserModal] = useState(false);

  // Load settings from localStorage on mount
  useEffect(() => {
    const saved = localStorage.getItem(SETTINGS_KEY);
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        setThreshold(parsed.threshold ?? defaultSettings.threshold);
        setEmergencyEnabled(parsed.emergencyEnabled ?? defaultSettings.emergencyEnabled);
        setNotifications(parsed.notifications ?? defaultSettings.notifications);
        setTheme(parsed.theme ?? defaultSettings.theme);
      } catch {}
    }
  }, []);

  // Save settings to localStorage
  const handleSave = () => {
    const settings = { threshold, emergencyEnabled, notifications, theme };
    localStorage.setItem(SETTINGS_KEY, JSON.stringify(settings));
    alert("Settings saved!");
  };

  // Reset to defaults and save
  const handleReset = () => {
    setThreshold(defaultSettings.threshold);
    setEmergencyEnabled(defaultSettings.emergencyEnabled);
    setNotifications(defaultSettings.notifications);
    setTheme(defaultSettings.theme);
    localStorage.setItem(SETTINGS_KEY, JSON.stringify(defaultSettings));
    alert("Settings reset to default.");
  };

  // Admin Controls
  const handleResetAlerts = () => {
    // Here you would call your backend to reset alerts
    alert("All alerts have been reset!");
  };

  const handleExportLogs = () => {
    // Simulate log export (replace with real backend call if needed)
    const logs = "System Log\n============\nAll systems operational.\n...";
    const blob = new Blob([logs], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "system_logs.txt";
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleManageUsers = () => {
    setShowUserModal(true);
  };

  return (
    <div className="max-w-2xl mx-auto py-10 px-4 space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-2">
          <SettingsIcon className="h-8 w-8 text-blue-500" />
          System Settings
        </h1>
        <p className="mt-2 text-gray-500">
          Configure system preferences, thresholds, alerts, and more.
        </p>
      </div>

      {/* Threshold Picker */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center gap-3 mb-2">
          <AlertTriangle className="text-red-500" />
          <h2 className="text-lg font-semibold text-gray-900">Threat Threshold</h2>
        </div>
        <p className="text-gray-500 mb-4">
          Set the threshold for triggering red alerts/emergencies. If a threat score exceeds this value, an alert will be sent.
        </p>
        <div className="flex items-center gap-4">
          <input
            type="range"
            min={0}
            max={100}
            value={threshold}
            onChange={e => setThreshold(Number(e.target.value))}
            className="w-full accent-red-500"
          />
          <input
            type="number"
            min={0}
            max={100}
            value={threshold}
            onChange={e => setThreshold(Number(e.target.value))}
            className="w-20 border border-gray-300 rounded px-2 py-1 text-center"
          />
          <span className="font-semibold text-red-600">{threshold}%</span>
        </div>
      </div>

      {/* Emergency Toggle */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2">
            <Bell className="text-green-500" />
            <h2 className="text-lg font-semibold text-gray-900">Enable Emergency Alerts</h2>
          </div>
          <p className="text-gray-500">
            Automatically send alerts when threats exceed the threshold.
          </p>
        </div>
        <label className="inline-flex items-center cursor-pointer ml-4">
          <input
            type="checkbox"
            checked={emergencyEnabled}
            onChange={e => setEmergencyEnabled(e.target.checked)}
            className="sr-only peer"
          />
          <div className="w-11 h-6 bg-gray-200 rounded-full peer peer-checked:bg-green-500 transition-all"></div>
          <div className={`absolute ml-1 mt-1 w-4 h-4 bg-white rounded-full shadow transform transition-all ${emergencyEnabled ? "translate-x-5" : ""}`}></div>
        </label>
      </div>

      {/* Notification Preferences */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-2">Notification Preferences</h2>
        <div className="flex flex-col gap-3">
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={notifications.email}
              onChange={e => setNotifications(n => ({ ...n, email: e.target.checked }))}
              className="accent-blue-500"
            />
            Email Alerts
          </label>
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={notifications.sms}
              onChange={e => setNotifications(n => ({ ...n, sms: e.target.checked }))}
              className="accent-blue-500"
            />
            SMS Alerts
          </label>
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={notifications.whatsapp}
              onChange={e => setNotifications(n => ({ ...n, whatsapp: e.target.checked }))}
              className="accent-blue-500"
            />
            WhatsApp Alerts
          </label>
        </div>
      </div>

      {/* Theme Switcher */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 flex items-center justify-between">
        <div className="flex items-center gap-2">
          {theme === "light" ? <Sun className="text-yellow-400" /> : <Moon className="text-gray-700" />}
          <h2 className="text-lg font-semibold text-gray-900">Theme</h2>
        </div>
        <div className="flex items-center gap-2">
          <button
            type="button"
            className={`px-4 py-1 rounded ${theme === "light" ? "bg-blue-500 text-white" : "bg-gray-200 text-gray-700"}`}
            onClick={() => setTheme("light")}
          >
            Light
          </button>
          <button
            type="button"
            className={`px-4 py-1 rounded ${theme === "dark" ? "bg-blue-500 text-white" : "bg-gray-200 text-gray-700"}`}
            onClick={() => setTheme("dark")}
          >
            Dark
          </button>
        </div>
      </div>

      {/* Admin-only Section */}
      {adminMode && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-2">Admin Controls</h2>
          <div className="flex flex-col gap-3">
            <button
              className="bg-red-600 text-white px-4 py-2 rounded hover:bg-red-700 transition"
              onClick={handleResetAlerts}
            >
              Reset All Alerts
            </button>
            <button
              className="bg-yellow-500 text-white px-4 py-2 rounded hover:bg-yellow-600 transition"
              onClick={handleExportLogs}
            >
              Export System Logs
            </button>
            <button
              className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 transition"
              onClick={handleManageUsers}
            >
              Manage Users
            </button>
          </div>
        </div>
      )}

      {/* Save/Reset Buttons */}
      <div className="flex gap-4 justify-end">
        <button
          onClick={handleReset}
          className="flex items-center gap-2 px-4 py-2 rounded bg-gray-200 text-gray-700 hover:bg-gray-300 transition"
        >
          <RefreshCcw className="w-4 h-4" /> Reset
        </button>
        <button
          onClick={handleSave}
          className="flex items-center gap-2 px-4 py-2 rounded bg-blue-600 text-white hover:bg-blue-700 transition"
        >
          <Save className="w-4 h-4" /> Save Settings
        </button>
      </div>

      {/* Manage Users Modal */}
      {showUserModal && (
        <div className="fixed inset-0 bg-black bg-opacity-30 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-lg p-6 w-full max-w-md">
            <h3 className="text-xl font-bold mb-4">Manage Users</h3>
            <p className="mb-4 text-gray-600">User management features coming soon!</p>
            <button
              className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 transition"
              onClick={() => setShowUserModal(false)}
            >
              Close
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default Settings;



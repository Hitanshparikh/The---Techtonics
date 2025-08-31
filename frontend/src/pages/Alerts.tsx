import React, { useState, useEffect } from 'react';
import { AlertTriangle, Send, Phone, Mail, MessageSquare, Users, Plus, Minus, BarChart3 } from 'lucide-react';
import toast from 'react-hot-toast';
import { sendAlert, subscribeSMS, unsubscribeSMS, getSMSSubscribers, sendBulkSMS, getSMSStats } from '../api/coastalData';

interface Subscriber {
  id: string;
  phone: string;
  name?: string;
  subscribed_at: string;
}

interface SMSStats {
  subscribers: {
    total: number;
    active: number;
    inactive: number;
  };
  sms: {
    total_sent: number;
    successful: number;
    failed: number;
    success_rate: number;
  };
}

const Alerts: React.FC = () => {
  // Emergency Alert State
  const [alertMessage, setAlertMessage] = useState('');
  const [alertType, setAlertType] = useState('weather');
  const [severity, setSeverity] = useState('medium');
  const [selectedChannels, setSelectedChannels] = useState<string[]>(['sms']);
  const [region, setRegion] = useState('');
  const [loading, setLoading] = useState(false);

  // SMS Subscription State
  const [subscriberName, setSubscriberName] = useState('');
  const [subscriberPhone, setSubscriberPhone] = useState('');
  const [subscriptionLoading, setSubscriptionLoading] = useState(false);

  // Bulk SMS State
  const [bulkMessage, setBulkMessage] = useState('');
  const [bulkLoading, setBulkLoading] = useState(false);

  // Subscribers List State
  const [subscribers, setSubscribers] = useState<Subscriber[]>([]);
  const [subscribersLoading, setSubscribersLoading] = useState(false);

  // Stats State
  const [stats, setStats] = useState<SMSStats | null>(null);
  const [statsLoading, setStatsLoading] = useState(false);

  // Tab State
  const [activeTab, setActiveTab] = useState('emergency');

  useEffect(() => {
    if (activeTab === 'subscribers') {
      loadSubscribers();
    } else if (activeTab === 'stats') {
      loadStats();
    }
  }, [activeTab]);

  const loadSubscribers = async () => {
    setSubscribersLoading(true);
    try {
      const data = await getSMSSubscribers();
      setSubscribers(data.subscribers || []);
    } catch (error) {
      console.error('Error loading subscribers:', error);
      toast.error('Failed to load subscribers');
    } finally {
      setSubscribersLoading(false);
    }
  };

  const loadStats = async () => {
    setStatsLoading(true);
    try {
      const data = await getSMSStats();
      setStats(data);
    } catch (error) {
      console.error('Error loading stats:', error);
      toast.error('Failed to load statistics');
    } finally {
      setStatsLoading(false);
    }
  };

  const handleChannelChange = (channel: string) => {
    setSelectedChannels(prev => 
      prev.includes(channel) 
        ? prev.filter(c => c !== channel)
        : [...prev, channel]
    );
  };

  const handleSendAlert = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      const data = await sendAlert({
        message: alertMessage,
        alert_type: alertType,
        severity: severity,
        channels: selectedChannels,
        region: region || undefined
      });

      toast.success(`Emergency alert sent successfully to ${data.recipients_count} recipients!`);
      setAlertMessage('');
    } catch (error) {
      console.error('Error sending alert:', error);
      toast.error('Failed to send emergency alert. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleSubscribeSMS = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubscriptionLoading(true);
    
    try {
      await subscribeSMS({
        phone_number: subscriberPhone,
        name: subscriberName || undefined
      });

      toast.success(`Successfully subscribed ${subscriberPhone} to SMS alerts!`);
      setSubscriberName('');
      setSubscriberPhone('');
      
      if (activeTab === 'subscribers') {
        loadSubscribers();
      }
    } catch (error) {
      console.error('Error subscribing to SMS:', error);
      toast.error('Failed to subscribe to SMS alerts. Please check the phone number format.');
    } finally {
      setSubscriptionLoading(false);
    }
  };

  const handleUnsubscribe = async (phoneNumber: string) => {
    try {
      await unsubscribeSMS(phoneNumber);
      toast.success('Successfully unsubscribed from SMS alerts');
      loadSubscribers();
    } catch (error) {
      console.error('Error unsubscribing:', error);
      toast.error('Failed to unsubscribe');
    }
  };

  const handleSendBulkSMS = async (e: React.FormEvent) => {
    e.preventDefault();
    setBulkLoading(true);
    
    try {
      const data = await sendBulkSMS({
        message: bulkMessage,
        message_type: 'notification'
      });

      toast.success(`Bulk SMS sent to ${data.target_subscribers} subscribers!`);
      setBulkMessage('');
    } catch (error) {
      console.error('Error sending bulk SMS:', error);
      toast.error('Failed to send bulk SMS. Please try again.');
    } finally {
      setBulkLoading(false);
    }
  };

  const formatPhoneNumber = (phone: string) => {
    // Format phone number for display
    if (phone.startsWith('+1') && phone.length === 12) {
      return `+1 (${phone.slice(2, 5)}) ${phone.slice(5, 8)}-${phone.slice(8)}`;
    }
    return phone;
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-6xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Alert Management System</h1>
          <p className="text-gray-600">Send emergency alerts and manage SMS subscriptions</p>
        </div>

        {/* Tab Navigation */}
        <div className="border-b border-gray-200 mb-8">
          <nav className="-mb-px flex space-x-8">
            {[
              { id: 'emergency', label: 'Emergency Alerts', icon: AlertTriangle },
              { id: 'subscription', label: 'SMS Subscription', icon: Phone },
              { id: 'bulk', label: 'Bulk SMS', icon: MessageSquare },
              { id: 'subscribers', label: 'Subscribers', icon: Users },
              { id: 'stats', label: 'Statistics', icon: BarChart3 },
            ].map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`py-2 px-1 border-b-2 font-medium text-sm flex items-center space-x-2 ${
                    activeTab === tab.id
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  <Icon className="h-4 w-4" />
                  <span>{tab.label}</span>
                </button>
              );
            })}
          </nav>
        </div>

        {/* Emergency Alerts Tab */}
        {activeTab === 'emergency' && (
          <div className="bg-white p-6 rounded-lg shadow-md">
            <div className="flex items-center mb-6">
              <AlertTriangle className="h-6 w-6 text-red-500 mr-2" />
              <h2 className="text-xl font-semibold text-gray-800">Emergency Alert System</h2>
            </div>

            <form onSubmit={handleSendAlert} className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Alert Message
                </label>
                <textarea
                  value={alertMessage}
                  onChange={(e) => setAlertMessage(e.target.value)}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  rows={4}
                  placeholder="Enter your emergency alert message..."
                  required
                />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Alert Type
                  </label>
                  <select
                    value={alertType}
                    onChange={(e) => setAlertType(e.target.value)}
                    className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    <option value="weather">Weather Alert</option>
                    <option value="tsunami">Tsunami Warning</option>
                    <option value="earthquake">Earthquake Alert</option>
                    <option value="flooding">Flood Warning</option>
                    <option value="coastal_erosion">Coastal Erosion</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Severity Level
                  </label>
                  <select
                    value={severity}
                    onChange={(e) => setSeverity(e.target.value)}
                    className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    <option value="low">Low</option>
                    <option value="medium">Medium</option>
                    <option value="high">High</option>
                    <option value="critical">Critical</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Region (Optional)
                  </label>
                  <input
                    type="text"
                    value={region}
                    onChange={(e) => setRegion(e.target.value)}
                    className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="e.g., coastal_region_1"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Alert Channels
                </label>
                <div className="flex flex-wrap gap-4">
                  {[
                    { value: 'sms', label: 'SMS', icon: Phone },
                    { value: 'email', label: 'Email', icon: Mail },
                  ].map((channel) => {
                    const Icon = channel.icon;
                    return (
                      <label key={channel.value} className="flex items-center">
                        <input
                          type="checkbox"
                          checked={selectedChannels.includes(channel.value)}
                          onChange={() => handleChannelChange(channel.value)}
                          className="rounded border-gray-300 text-blue-600 shadow-sm focus:border-blue-300 focus:ring focus:ring-blue-200 focus:ring-opacity-50"
                        />
                        <Icon className="h-4 w-4 ml-2 mr-1 text-gray-500" />
                        <span className="ml-1 text-sm text-gray-700">{channel.label}</span>
                      </label>
                    );
                  })}
                </div>
              </div>

              <button
                type="submit"
                disabled={loading || !alertMessage.trim()}
                className="w-full bg-red-600 text-white py-3 px-4 rounded-lg hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
              >
                {loading ? (
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                ) : (
                  <>
                    <Send className="h-5 w-5 mr-2" />
                    Send Emergency Alert
                  </>
                )}
              </button>
            </form>
          </div>
        )}

        {/* SMS Subscription Tab */}
        {activeTab === 'subscription' && (
          <div className="bg-white p-6 rounded-lg shadow-md">
            <div className="flex items-center mb-6">
              <Phone className="h-6 w-6 text-blue-500 mr-2" />
              <h2 className="text-xl font-semibold text-gray-800">SMS Alert Subscription</h2>
            </div>

            <form onSubmit={handleSubscribeSMS} className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Phone Number *
                </label>
                <input
                  type="tel"
                  value={subscriberPhone}
                  onChange={(e) => setSubscriberPhone(e.target.value)}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="+1234567890 or (123) 456-7890"
                  required
                />
                <p className="mt-1 text-sm text-gray-500">
                  Enter your phone number with country code (e.g., +1 for US)
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Name (Optional)
                </label>
                <input
                  type="text"
                  value={subscriberName}
                  onChange={(e) => setSubscriberName(e.target.value)}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Your name"
                />
              </div>

              <button
                type="submit"
                disabled={subscriptionLoading || !subscriberPhone.trim()}
                className="w-full bg-blue-600 text-white py-3 px-4 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
              >
                {subscriptionLoading ? (
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                ) : (
                  <>
                    <Plus className="h-5 w-5 mr-2" />
                    Subscribe to SMS Alerts
                  </>
                )}
              </button>
            </form>

            <div className="mt-6 p-4 bg-blue-50 rounded-lg">
              <h3 className="font-medium text-blue-900 mb-2">What you'll receive:</h3>
              <ul className="text-sm text-blue-700 space-y-1">
                <li>• Welcome message confirming your subscription</li>
                <li>• Real-time coastal threat alerts</li>
                <li>• Emergency weather notifications</li>
                <li>• Critical safety updates</li>
              </ul>
              <p className="text-xs text-blue-600 mt-2">
                Reply STOP to any message to unsubscribe at any time.
              </p>
            </div>
          </div>
        )}

        {/* Bulk SMS Tab */}
        {activeTab === 'bulk' && (
          <div className="bg-white p-6 rounded-lg shadow-md">
            <div className="flex items-center mb-6">
              <MessageSquare className="h-6 w-6 text-green-500 mr-2" />
              <h2 className="text-xl font-semibold text-gray-800">Send Bulk SMS</h2>
            </div>

            <form onSubmit={handleSendBulkSMS} className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Message
                </label>
                <textarea
                  value={bulkMessage}
                  onChange={(e) => setBulkMessage(e.target.value)}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                  rows={4}
                  placeholder="Enter your message to send to all subscribers..."
                  required
                />
                <p className="mt-1 text-sm text-gray-500">
                  This message will be sent to all active SMS subscribers.
                </p>
              </div>

              <button
                type="submit"
                disabled={bulkLoading || !bulkMessage.trim()}
                className="w-full bg-green-600 text-white py-3 px-4 rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
              >
                {bulkLoading ? (
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                ) : (
                  <>
                    <Send className="h-5 w-5 mr-2" />
                    Send to All Subscribers
                  </>
                )}
              </button>
            </form>
          </div>
        )}

        {/* Subscribers Tab */}
        {activeTab === 'subscribers' && (
          <div className="bg-white p-6 rounded-lg shadow-md">
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center">
                <Users className="h-6 w-6 text-purple-500 mr-2" />
                <h2 className="text-xl font-semibold text-gray-800">SMS Subscribers</h2>
              </div>
              <button
                onClick={loadSubscribers}
                className="bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700"
              >
                Refresh
              </button>
            </div>

            {subscribersLoading ? (
              <div className="flex justify-center py-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600"></div>
              </div>
            ) : (
              <div>
                {subscribers.length === 0 ? (
                  <p className="text-gray-500 text-center py-8">No subscribers found.</p>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Phone Number
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Name
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Subscribed
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Actions
                          </th>
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {subscribers.map((subscriber) => (
                          <tr key={subscriber.id}>
                            <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                              {formatPhoneNumber(subscriber.phone)}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                              {subscriber.name || 'N/A'}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                              {new Date(subscriber.subscribed_at).toLocaleDateString()}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                              <button
                                onClick={() => handleUnsubscribe(subscriber.phone)}
                                className="text-red-600 hover:text-red-900 flex items-center"
                              >
                                <Minus className="h-4 w-4 mr-1" />
                                Unsubscribe
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* Statistics Tab */}
        {activeTab === 'stats' && (
          <div className="bg-white p-6 rounded-lg shadow-md">
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center">
                <BarChart3 className="h-6 w-6 text-indigo-500 mr-2" />
                <h2 className="text-xl font-semibold text-gray-800">SMS Statistics</h2>
              </div>
              <button
                onClick={loadStats}
                className="bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700"
              >
                Refresh
              </button>
            </div>

            {statsLoading ? (
              <div className="flex justify-center py-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
              </div>
            ) : stats ? (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h3 className="text-lg font-medium text-gray-900 mb-4">Subscribers</h3>
                  <div className="space-y-3">
                    <div className="flex justify-between">
                      <span className="text-gray-600">Total:</span>
                      <span className="font-semibold">{stats.subscribers.total}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Active:</span>
                      <span className="font-semibold text-green-600">{stats.subscribers.active}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Inactive:</span>
                      <span className="font-semibold text-red-600">{stats.subscribers.inactive}</span>
                    </div>
                  </div>
                </div>

                <div>
                  <h3 className="text-lg font-medium text-gray-900 mb-4">SMS Messages</h3>
                  <div className="space-y-3">
                    <div className="flex justify-between">
                      <span className="text-gray-600">Total Sent:</span>
                      <span className="font-semibold">{stats.sms.total_sent}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Successful:</span>
                      <span className="font-semibold text-green-600">{stats.sms.successful}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Failed:</span>
                      <span className="font-semibold text-red-600">{stats.sms.failed}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Success Rate:</span>
                      <span className="font-semibold text-blue-600">{stats.sms.success_rate}%</span>
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              <p className="text-gray-500 text-center py-8">No statistics available.</p>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default Alerts;

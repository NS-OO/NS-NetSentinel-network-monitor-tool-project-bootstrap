'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { useSocket } from '@/hooks/useSocket';

interface NetworkData {
  is_online: boolean;
  download_speed: number;
  upload_speed: number;
  total_devices: number;
  active_devices: number;
  devices: any[];
}

interface NetworkStats {
  timestamp: string;
  download_speed: number;
  upload_speed: number;
  total_devices: number;
  active_devices: number;
  network_usage: number;
  ping_latency: number;
}

export default function DashboardPage() {
  const [networkData, setNetworkData] = useState<NetworkData | null>(null);
  const [networkStats, setNetworkStats] = useState<NetworkStats[]>([]);
  const [alerts, setAlerts] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const router = useRouter();
  const { socket } = useSocket('http://localhost:5000');

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (!token) {
      router.push('/login');
      return;
    }

    fetchData();
    fetchStats();
    fetchAlerts();
  }, [router]);

  useEffect(() => {
    if (socket) {
      socket.on('network_data', (data: NetworkData) => {
        setNetworkData(data);
      });

      return () => {
        socket.off('network_data');
      };
    }
  }, [socket]);

  const fetchData = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('http://localhost:5000/api/network/status', {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setNetworkData(data);
      } else if (response.status === 401) {
        router.push('/login');
      }
    } catch (error) {
      console.error('Error fetching network data:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchStats = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('http://localhost:5000/api/network/stats', {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setNetworkStats(data.reverse());
      }
    } catch (error) {
      console.error('Error fetching network stats:', error);
    }
  };

  const fetchAlerts = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('http://localhost:5000/api/alerts', {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setAlerts(data.slice(0, 5));
      }
    } catch (error) {
      console.error('Error fetching alerts:', error);
    }
  };

  const formatSpeed = (bytes: number) => {
    if (bytes === 0) return '0 B/s';
    const k = 1024;
    const sizes = ['B/s', 'KB/s', 'MB/s', 'GB/s'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-lg">Loading dashboard...</div>
      </div>
    );
  }

  const chartData = networkStats.map(stat => ({
    time: new Date(stat.timestamp).toLocaleTimeString(),
    download: stat.download_speed,
    upload: stat.upload_speed,
    devices: stat.total_devices,
  }));

  const deviceData = networkData?.devices ? [
    { name: 'Online', value: networkData.active_devices, color: '#10b981' },
    { name: 'Offline', value: networkData.total_devices - networkData.active_devices, color: '#ef4444' },
  ] : [];

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-4">
      <div className="max-w-7xl mx-auto">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-3xl font-bold">Network Monitor Dashboard</h1>
          <div className="flex gap-2">
            <Button onClick={() => router.push('/devices')}>Manage Devices</Button>
            <Button onClick={() => router.push('/alerts')}>View Alerts</Button>
            <Button 
              variant="outline" 
              onClick={() => {
                localStorage.removeItem('token');
                localStorage.removeItem('user');
                router.push('/login');
              }}
            >
              Logout
            </Button>
          </div>
        </div>

        {/* Network Status */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-sm">Network Status</CardTitle>
            </CardHeader>
            <CardContent>
              <Badge variant={networkData?.is_online ? "default" : "destructive"}>
                {networkData?.is_online ? 'Online' : 'Offline'}
              </Badge>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-sm">Download Speed</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{formatSpeed(networkData?.download_speed || 0)}</div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-sm">Upload Speed</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{formatSpeed(networkData?.upload_speed || 0)}</div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-sm">Connected Devices</CardTitle>
            </CardContent>
            <CardContent>
              <div className="text-2xl font-bold">{networkData?.total_devices || 0}</div>
              <div className="text-sm text-gray-500">{networkData?.active_devices || 0} active</div>
            </CardContent>
          </Card>
        </div>

        {/* Charts */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          <Card>
            <CardHeader>
              <CardTitle>Network Speed Over Time</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="time" />
                  <YAxis />
                  <Tooltip />
                  <Line type="monotone" dataKey="download" stroke="#3b82f6" name="Download" />
                  <Line type="monotone" dataKey="upload" stroke="#10b981" name="Upload" />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Device Status</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={deviceData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, value }) => `${name}: ${value}`}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {deviceData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </div>

        {/* Recent Alerts */}
        <Card>
          <CardHeader>
            <CardTitle>Recent Alerts</CardTitle>
            <CardDescription>Latest network alerts and notifications</CardDescription>
          </CardHeader>
          <CardContent>
            {alerts.length === 0 ? (
              <p className="text-gray-500">No recent alerts</p>
            ) : (
              <div className="space-y-2">
                {alerts.map((alert) => (
                  <Alert key={alert.id} variant={alert.severity === 'critical' ? 'destructive' : 'default'}>
                    <AlertDescription>
                      <div className="flex justify-between items-start">
                        <div>
                          <div className="font-medium">{alert.type}</div>
                          <div className="text-sm">{alert.message}</div>
                        </div>
                        <div className="text-xs text-gray-500">
                          {new Date(alert.timestamp).toLocaleString()}
                        </div>
                      </div>
                    </AlertDescription>
                  </Alert>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

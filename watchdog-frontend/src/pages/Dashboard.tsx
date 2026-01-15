import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { api, Monitor } from '../lib/api';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Plus, Eye, Bell, Settings, Play, Trash2, ExternalLink, Clock, AlertCircle, CheckCircle } from 'lucide-react';

export function Dashboard() {
  const [monitors, setMonitors] = useState<Monitor[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadMonitors();
  }, []);

  const loadMonitors = async () => {
    const { data } = await api.monitors.list();
    if (data) {
      setMonitors(data);
    }
    setLoading(false);
  };

  const handleTriggerCheck = async (id: string) => {
    await api.monitors.triggerCheck(id);
    setTimeout(loadMonitors, 2000);
  };

  const handleDelete = async (id: string) => {
    if (confirm('Are you sure you want to delete this monitor?')) {
      await api.monitors.delete(id);
      loadMonitors();
    }
  };

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return 'Never';
    return new Date(dateStr).toLocaleString();
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Eye className="h-8 w-8 text-blue-600" />
            <span className="text-xl font-bold">URL Watchdog</span>
          </div>
          <nav className="flex items-center gap-4">
            <Link to="/notifications">
              <Button variant="ghost" size="sm">
                <Bell className="h-4 w-4 mr-2" />
                Notifications
              </Button>
            </Link>
            <Link to="/settings">
              <Button variant="ghost" size="sm">
                <Settings className="h-4 w-4 mr-2" />
                Settings
              </Button>
            </Link>
          </nav>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-8">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold">Your Monitors</h1>
                        <p className="text-gray-600">
                          {monitors.length} monitors
                        </p>
          </div>
          <Link to="/monitors/new">
            <Button>
              <Plus className="h-4 w-4 mr-2" />
              Add Monitor
            </Button>
          </Link>
        </div>

        {loading ? (
          <div className="text-center py-12">Loading...</div>
        ) : monitors.length === 0 ? (
          <Card>
            <CardContent className="py-12 text-center">
              <Eye className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium mb-2">No monitors yet</h3>
              <p className="text-gray-600 mb-4">
                Create your first monitor to start watching URLs for keywords.
              </p>
              <Link to="/monitors/new">
                <Button>
                  <Plus className="h-4 w-4 mr-2" />
                  Add Your First Monitor
                </Button>
              </Link>
            </CardContent>
          </Card>
        ) : (
          <div className="grid gap-4">
            {monitors.map((monitor) => (
              <Card key={monitor.id}>
                <CardHeader className="pb-2">
                  <div className="flex items-start justify-between">
                    <div>
                      <CardTitle className="flex items-center gap-2">
                        {monitor.name}
                        <Badge variant={monitor.is_active ? 'default' : 'secondary'}>
                          {monitor.is_active ? 'Active' : 'Paused'}
                        </Badge>
                        {monitor.last_match_found && (
                          <Badge variant="destructive">Match Found</Badge>
                        )}
                      </CardTitle>
                      <CardDescription className="flex items-center gap-1 mt-1">
                        <ExternalLink className="h-3 w-3" />
                        <a href={monitor.url} target="_blank" rel="noopener noreferrer" className="hover:underline">
                          {monitor.url}
                        </a>
                      </CardDescription>
                    </div>
                    <div className="flex gap-2">
                      <Button variant="outline" size="sm" onClick={() => handleTriggerCheck(monitor.id)}>
                        <Play className="h-4 w-4" />
                      </Button>
                      <Link to={`/monitors/${monitor.id}`}>
                        <Button variant="outline" size="sm">
                          <Settings className="h-4 w-4" />
                        </Button>
                      </Link>
                      <Button variant="outline" size="sm" onClick={() => handleDelete(monitor.id)}>
                        <Trash2 className="h-4 w-4 text-red-500" />
                      </Button>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="flex flex-wrap gap-4 text-sm text-gray-600">
                    <div className="flex items-center gap-1">
                      <Clock className="h-4 w-4" />
                      Checks {monitor.check_frequency}x/day
                    </div>
                    <div className="flex items-center gap-1">
                      {monitor.last_result?.startsWith('error') ? (
                        <AlertCircle className="h-4 w-4 text-red-500" />
                      ) : (
                        <CheckCircle className="h-4 w-4 text-green-500" />
                      )}
                      Last checked: {formatDate(monitor.last_checked)}
                    </div>
                  </div>
                  <div className="mt-2 flex flex-wrap gap-1">
                    {monitor.keywords.map((keyword, i) => (
                      <Badge key={i} variant="outline">{keyword}</Badge>
                    ))}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}

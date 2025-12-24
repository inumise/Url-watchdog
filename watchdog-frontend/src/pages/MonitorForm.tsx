import { useState, useEffect } from 'react';
import { useNavigate, useParams, Link } from 'react-router-dom';
import { api, CheckLog } from '../lib/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
import { ArrowLeft, Plus, X, Clock, CheckCircle, AlertCircle } from 'lucide-react';

export function MonitorForm() {
  const { id } = useParams();
  const navigate = useNavigate();
  const isEditing = !!id;

  const [name, setName] = useState('');
  const [url, setUrl] = useState('');
  const [keywords, setKeywords] = useState<string[]>([]);
  const [keywordInput, setKeywordInput] = useState('');
  const [checkFrequency, setCheckFrequency] = useState(4);
  const [isActive, setIsActive] = useState(true);
  const [logs, setLogs] = useState<CheckLog[]>([]);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [loadingData, setLoadingData] = useState(isEditing);

  useEffect(() => {
    if (isEditing) {
      loadMonitor();
      loadLogs();
    }
  }, [id]);

  const loadMonitor = async () => {
    const { data } = await api.monitors.get(id!);
    if (data) {
      setName(data.name);
      setUrl(data.url);
      setKeywords(data.keywords);
      setCheckFrequency(data.check_frequency);
      setIsActive(data.is_active);
    }
    setLoadingData(false);
  };

  const loadLogs = async () => {
    const { data } = await api.monitors.getLogs(id!);
    if (data) {
      setLogs(data);
    }
  };

  const addKeyword = () => {
    if (keywordInput.trim() && !keywords.includes(keywordInput.trim())) {
      setKeywords([...keywords, keywordInput.trim()]);
      setKeywordInput('');
    }
  };

  const removeKeyword = (keyword: string) => {
    setKeywords(keywords.filter(k => k !== keyword));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (keywords.length === 0) {
      setError('Please add at least one keyword to watch for');
      return;
    }

    setLoading(true);

    const data = { name, url, keywords, check_frequency: checkFrequency };

    if (isEditing) {
      const { error } = await api.monitors.update(id!, { ...data, is_active: isActive });
      if (error) {
        setError(error);
        setLoading(false);
        return;
      }
    } else {
      const { error } = await api.monitors.create(data);
      if (error) {
        setError(error);
        setLoading(false);
        return;
      }
    }

    navigate('/dashboard');
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleString();
  };

  if (loadingData) {
    return <div className="min-h-screen flex items-center justify-center">Loading...</div>;
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b">
        <div className="max-w-3xl mx-auto px-4 py-4">
          <Link to="/dashboard" className="flex items-center gap-2 text-gray-600 hover:text-gray-900">
            <ArrowLeft className="h-4 w-4" />
            Back to Dashboard
          </Link>
        </div>
      </header>

      <main className="max-w-3xl mx-auto px-4 py-8">
        <Card>
          <CardHeader>
            <CardTitle>{isEditing ? 'Edit Monitor' : 'Create New Monitor'}</CardTitle>
            <CardDescription>
              {isEditing 
                ? 'Update your monitor settings'
                : 'Set up a new URL to watch for specific keywords'
              }
            </CardDescription>
          </CardHeader>
          <form onSubmit={handleSubmit}>
            <CardContent className="space-y-6">
              {error && (
                <div className="bg-red-50 text-red-600 p-3 rounded-md text-sm">
                  {error}
                </div>
              )}

              <div className="space-y-2">
                <Label htmlFor="name">Monitor Name</Label>
                <Input
                  id="name"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g., Company Blog Updates"
                  required
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="url">URL to Monitor</Label>
                <Input
                  id="url"
                  type="url"
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  placeholder="https://example.com/page"
                  required
                />
                <p className="text-xs text-gray-500">
                  The full URL of the page you want to monitor
                </p>
              </div>

              <div className="space-y-2">
                <Label>Keywords to Watch</Label>
                <div className="flex gap-2">
                  <Input
                    value={keywordInput}
                    onChange={(e) => setKeywordInput(e.target.value)}
                    placeholder="Enter a keyword"
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') {
                        e.preventDefault();
                        addKeyword();
                      }
                    }}
                  />
                  <Button type="button" variant="outline" onClick={addKeyword}>
                    <Plus className="h-4 w-4" />
                  </Button>
                </div>
                <div className="flex flex-wrap gap-2 mt-2">
                  {keywords.map((keyword) => (
                    <Badge key={keyword} variant="secondary" className="flex items-center gap-1">
                      {keyword}
                      <button type="button" onClick={() => removeKeyword(keyword)}>
                        <X className="h-3 w-3" />
                      </button>
                    </Badge>
                  ))}
                </div>
                <p className="text-xs text-gray-500">
                  You'll be notified when any of these keywords appear on the page
                </p>
              </div>

              <div className="space-y-2">
                <Label htmlFor="frequency">Check Frequency</Label>
                <div className="flex items-center gap-4">
                  <Input
                    id="frequency"
                    type="number"
                    min={1}
                    max={24}
                    value={checkFrequency}
                    onChange={(e) => setCheckFrequency(parseInt(e.target.value) || 1)}
                    className="w-24"
                  />
                  <span className="text-gray-600">times per day</span>
                </div>
                <p className="text-xs text-gray-500">
                  How often to check the URL (1-24 times per day)
                </p>
              </div>

              {isEditing && (
                <div className="flex items-center justify-between">
                  <div>
                    <Label>Active</Label>
                    <p className="text-xs text-gray-500">Enable or disable this monitor</p>
                  </div>
                  <Switch checked={isActive} onCheckedChange={setIsActive} />
                </div>
              )}

              <div className="flex gap-4 pt-4">
                <Button type="submit" disabled={loading}>
                  {loading ? 'Saving...' : (isEditing ? 'Update Monitor' : 'Create Monitor')}
                </Button>
                <Link to="/dashboard">
                  <Button type="button" variant="outline">Cancel</Button>
                </Link>
              </div>
            </CardContent>
          </form>
        </Card>

        {isEditing && logs.length > 0 && (
          <Card className="mt-8">
            <CardHeader>
              <CardTitle>Recent Check History</CardTitle>
              <CardDescription>Last {logs.length} checks for this monitor</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {logs.map((log) => (
                  <div key={log.id} className="flex items-start gap-3 p-3 bg-gray-50 rounded-lg">
                    {log.success ? (
                      log.match_found ? (
                        <AlertCircle className="h-5 w-5 text-orange-500 mt-0.5" />
                      ) : (
                        <CheckCircle className="h-5 w-5 text-green-500 mt-0.5" />
                      )
                    ) : (
                      <AlertCircle className="h-5 w-5 text-red-500 mt-0.5" />
                    )}
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <Clock className="h-3 w-3 text-gray-400" />
                        <span className="text-sm text-gray-600">{formatDate(log.checked_at)}</span>
                      </div>
                      {log.success ? (
                        log.match_found ? (
                          <p className="text-sm mt-1">
                            <span className="font-medium text-orange-600">Keywords found:</span>{' '}
                            {log.matched_keywords.join(', ')}
                          </p>
                        ) : (
                          <p className="text-sm text-gray-600 mt-1">No keywords matched</p>
                        )
                      ) : (
                        <p className="text-sm text-red-600 mt-1">{log.error_message}</p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}
      </main>
    </div>
  );
}

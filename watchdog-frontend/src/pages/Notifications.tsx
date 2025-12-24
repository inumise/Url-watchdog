import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { api, NotificationChannel } from '../lib/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ArrowLeft, Mail, MessageCircle, Webhook, Trash2, Plus, Info } from 'lucide-react';

type ChannelType = 'email' | 'telegram' | 'webhook';

interface ChannelConfig {
  [key: string]: string;
}

export function Notifications() {
  const [channels, setChannels] = useState<NotificationChannel[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [selectedType, setSelectedType] = useState<ChannelType>('email');
  const [formName, setFormName] = useState('');
  const [formConfig, setFormConfig] = useState<ChannelConfig>({});
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    loadChannels();
  }, []);

  const loadChannels = async () => {
    const { data } = await api.notifications.list();
    if (data) {
      setChannels(data);
    }
    setLoading(false);
  };

  const handleCreate = async () => {
    setError('');
    setSaving(true);

    const { error } = await api.notifications.create({
      name: formName,
      channel_type: selectedType,
      config: formConfig,
    });

    if (error) {
      setError(error);
      setSaving(false);
      return;
    }

    setShowForm(false);
    setFormName('');
    setFormConfig({});
    loadChannels();
    setSaving(false);
  };

  const handleToggle = async (channel: NotificationChannel) => {
    await api.notifications.update(channel.id, { is_active: !channel.is_active });
    loadChannels();
  };

  const handleDelete = async (id: string) => {
    if (confirm('Are you sure you want to delete this notification channel?')) {
      await api.notifications.delete(id);
      loadChannels();
    }
  };

  const getChannelIcon = (type: string) => {
    switch (type) {
      case 'email': return <Mail className="h-5 w-5" />;
      case 'telegram': return <MessageCircle className="h-5 w-5" />;
      case 'webhook': return <Webhook className="h-5 w-5" />;
      default: return <Bell className="h-5 w-5" />;
    }
  };

  const renderConfigForm = () => {
    switch (selectedType) {
      case 'email':
        return (
          <div className="space-y-4">
            <div className="bg-blue-50 p-4 rounded-lg text-sm">
              <div className="flex gap-2">
                <Info className="h-5 w-5 text-blue-600 flex-shrink-0" />
                <div>
                  <p className="font-medium text-blue-800">Email Setup Instructions</p>
                  <p className="text-blue-700 mt-1">
                    You'll need SMTP credentials from your email provider. For Gmail, you'll need to create an App Password 
                    in your Google Account settings under Security &gt; 2-Step Verification &gt; App passwords.
                  </p>
                </div>
              </div>
            </div>
            <div className="space-y-2">
              <Label>SMTP Host</Label>
              <Input
                value={formConfig.smtp_host || ''}
                onChange={(e) => setFormConfig({ ...formConfig, smtp_host: e.target.value })}
                placeholder="smtp.gmail.com"
              />
            </div>
            <div className="space-y-2">
              <Label>SMTP Port</Label>
              <Input
                value={formConfig.smtp_port || ''}
                onChange={(e) => setFormConfig({ ...formConfig, smtp_port: e.target.value })}
                placeholder="587"
              />
            </div>
            <div className="space-y-2">
              <Label>SMTP Username (Email)</Label>
              <Input
                value={formConfig.smtp_user || ''}
                onChange={(e) => setFormConfig({ ...formConfig, smtp_user: e.target.value })}
                placeholder="your-email@gmail.com"
              />
            </div>
            <div className="space-y-2">
              <Label>SMTP Password / App Password</Label>
              <Input
                type="password"
                value={formConfig.smtp_password || ''}
                onChange={(e) => setFormConfig({ ...formConfig, smtp_password: e.target.value })}
                placeholder="Your app password"
              />
            </div>
            <div className="space-y-2">
              <Label>Send Alerts To</Label>
              <Input
                type="email"
                value={formConfig.to_email || ''}
                onChange={(e) => setFormConfig({ ...formConfig, to_email: e.target.value })}
                placeholder="alerts@example.com"
              />
            </div>
          </div>
        );

      case 'telegram':
        return (
          <div className="space-y-4">
            <div className="bg-blue-50 p-4 rounded-lg text-sm">
              <div className="flex gap-2">
                <Info className="h-5 w-5 text-blue-600 flex-shrink-0" />
                <div>
                  <p className="font-medium text-blue-800">Telegram Setup Instructions</p>
                  <ol className="text-blue-700 mt-1 list-decimal list-inside space-y-1">
                    <li>Message @BotFather on Telegram and create a new bot with /newbot</li>
                    <li>Copy the bot token you receive</li>
                    <li>Start a chat with your new bot and send any message</li>
                    <li>Visit https://api.telegram.org/bot&lt;YOUR_TOKEN&gt;/getUpdates to find your chat_id</li>
                  </ol>
                </div>
              </div>
            </div>
            <div className="space-y-2">
              <Label>Bot Token</Label>
              <Input
                value={formConfig.bot_token || ''}
                onChange={(e) => setFormConfig({ ...formConfig, bot_token: e.target.value })}
                placeholder="123456789:ABCdefGHIjklMNOpqrsTUVwxyz"
              />
            </div>
            <div className="space-y-2">
              <Label>Chat ID</Label>
              <Input
                value={formConfig.chat_id || ''}
                onChange={(e) => setFormConfig({ ...formConfig, chat_id: e.target.value })}
                placeholder="123456789"
              />
            </div>
          </div>
        );

      case 'webhook':
        return (
          <div className="space-y-4">
            <div className="bg-blue-50 p-4 rounded-lg text-sm">
              <div className="flex gap-2">
                <Info className="h-5 w-5 text-blue-600 flex-shrink-0" />
                <div>
                  <p className="font-medium text-blue-800">Webhook Setup</p>
                  <p className="text-blue-700 mt-1">
                    Use webhooks to integrate with any service that accepts HTTP POST requests. 
                    This works with Slack, Discord, Zapier, Make, n8n, and many other services.
                    The payload will include monitor details and matched keywords.
                  </p>
                </div>
              </div>
            </div>
            <div className="space-y-2">
              <Label>Webhook URL</Label>
              <Input
                value={formConfig.webhook_url || ''}
                onChange={(e) => setFormConfig({ ...formConfig, webhook_url: e.target.value })}
                placeholder="https://hooks.slack.com/services/..."
              />
            </div>
            <div className="space-y-2">
              <Label>Authorization Header (Optional)</Label>
              <Input
                value={formConfig.auth_header || ''}
                onChange={(e) => setFormConfig({ ...formConfig, headers: JSON.stringify({ Authorization: e.target.value }) })}
                placeholder="Bearer your-token"
              />
            </div>
          </div>
        );
    }
  };

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
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold">Notification Channels</h1>
            <p className="text-gray-600">Configure how you want to receive alerts</p>
          </div>
          {!showForm && (
            <Button onClick={() => setShowForm(true)}>
              <Plus className="h-4 w-4 mr-2" />
              Add Channel
            </Button>
          )}
        </div>

        {showForm && (
          <Card className="mb-8">
            <CardHeader>
              <CardTitle>Add Notification Channel</CardTitle>
              <CardDescription>Choose a channel type and configure it</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {error && (
                <div className="bg-red-50 text-red-600 p-3 rounded-md text-sm">
                  {error}
                </div>
              )}

              <div className="space-y-2">
                <Label>Channel Name</Label>
                <Input
                  value={formName}
                  onChange={(e) => setFormName(e.target.value)}
                  placeholder="e.g., My Email Alerts"
                />
              </div>

              <Tabs value={selectedType} onValueChange={(v) => {
                setSelectedType(v as ChannelType);
                setFormConfig({});
              }}>
                <TabsList className="grid w-full grid-cols-3">
                  <TabsTrigger value="email">
                    <Mail className="h-4 w-4 mr-2" />
                    Email
                  </TabsTrigger>
                  <TabsTrigger value="telegram">
                    <MessageCircle className="h-4 w-4 mr-2" />
                    Telegram
                  </TabsTrigger>
                  <TabsTrigger value="webhook">
                    <Webhook className="h-4 w-4 mr-2" />
                    Webhook
                  </TabsTrigger>
                </TabsList>
                <TabsContent value={selectedType} className="mt-4">
                  {renderConfigForm()}
                </TabsContent>
              </Tabs>

              <div className="flex gap-4">
                <Button onClick={handleCreate} disabled={saving || !formName}>
                  {saving ? 'Saving...' : 'Add Channel'}
                </Button>
                <Button variant="outline" onClick={() => {
                  setShowForm(false);
                  setFormName('');
                  setFormConfig({});
                  setError('');
                }}>
                  Cancel
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {loading ? (
          <div className="text-center py-12">Loading...</div>
        ) : channels.length === 0 && !showForm ? (
          <Card>
            <CardContent className="py-12 text-center">
              <Mail className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium mb-2">No notification channels</h3>
              <p className="text-gray-600 mb-4">
                Add a notification channel to receive alerts when keywords are found.
              </p>
              <Button onClick={() => setShowForm(true)}>
                <Plus className="h-4 w-4 mr-2" />
                Add Your First Channel
              </Button>
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-4">
            {channels.map((channel) => (
              <Card key={channel.id}>
                <CardContent className="py-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="p-2 bg-gray-100 rounded-lg">
                        {getChannelIcon(channel.channel_type)}
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-medium">{channel.name}</span>
                          <Badge variant="outline">{channel.channel_type}</Badge>
                        </div>
                        <p className="text-sm text-gray-500">
                          {channel.channel_type === 'email' && channel.config_masked.to_email}
                          {channel.channel_type === 'telegram' && `Chat ID: ${channel.config_masked.chat_id}`}
                          {channel.channel_type === 'webhook' && channel.config_masked.webhook_url}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-4">
                      <Switch
                        checked={channel.is_active}
                        onCheckedChange={() => handleToggle(channel)}
                      />
                      <Button variant="ghost" size="sm" onClick={() => handleDelete(channel.id)}>
                        <Trash2 className="h-4 w-4 text-red-500" />
                      </Button>
                    </div>
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

function Bell(props: any) {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props}>
      <path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9"/>
      <path d="M10.3 21a1.94 1.94 0 0 0 3.4 0"/>
    </svg>
  );
}

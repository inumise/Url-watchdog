import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../lib/auth-context';
import { api } from '../lib/api';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ArrowLeft, Crown, CreditCard, User, Calendar } from 'lucide-react';

export function Settings() {
  const { user } = useAuth();
  const [loading, setLoading] = useState(false);

  const handleUpgrade = async () => {
    setLoading(true);
    const currentUrl = window.location.origin;
    const { data, error } = await api.billing.createCheckout(
      `${currentUrl}/settings?success=true`,
      `${currentUrl}/settings`
    );
    
    if (data?.checkout_url) {
      window.location.href = data.checkout_url;
    } else {
      alert(error || 'Payment service not available');
      setLoading(false);
    }
  };

  const handleManageBilling = async () => {
    setLoading(true);
    const currentUrl = window.location.origin;
    const { data, error } = await api.billing.createPortal(`${currentUrl}/settings`);
    
    if (data?.portal_url) {
      window.location.href = data.portal_url;
    } else {
      alert(error || 'Unable to open billing portal');
      setLoading(false);
    }
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString();
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

      <main className="max-w-3xl mx-auto px-4 py-8 space-y-6">
        <h1 className="text-2xl font-bold">Settings</h1>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <User className="h-5 w-5" />
              Account
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between py-2 border-b">
              <span className="text-gray-600">Email</span>
              <span className="font-medium">{user?.email}</span>
            </div>
            <div className="flex items-center justify-between py-2 border-b">
              <span className="text-gray-600">Member since</span>
              <span className="font-medium flex items-center gap-2">
                <Calendar className="h-4 w-4" />
                {user?.created_at ? formatDate(user.created_at) : 'N/A'}
              </span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Crown className="h-5 w-5" />
              Subscription
            </CardTitle>
            <CardDescription>
              Manage your subscription and billing
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between mb-6">
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <span className="font-medium text-lg">
                    {user?.subscription_status === 'pro' ? 'Pro Plan' : 'Free Plan'}
                  </span>
                  <Badge variant={user?.subscription_status === 'pro' ? 'default' : 'secondary'}>
                    {user?.subscription_status === 'pro' ? 'Active' : 'Free'}
                  </Badge>
                </div>
                <p className="text-gray-600 text-sm">
                  {user?.subscription_status === 'pro' 
                    ? 'Unlimited monitors and priority support'
                    : 'Up to 3 monitors'
                  }
                </p>
              </div>
            </div>

            {user?.subscription_status === 'free' ? (
              <div className="bg-gradient-to-r from-blue-50 to-purple-50 p-6 rounded-lg">
                <h3 className="font-semibold text-lg mb-2">Upgrade to Pro</h3>
                <ul className="text-gray-700 space-y-2 mb-4">
                  <li className="flex items-center gap-2">
                    <span className="text-green-500">+</span>
                    Up to 100 monitors
                  </li>
                  <li className="flex items-center gap-2">
                    <span className="text-green-500">+</span>
                    Check up to 24 times per day
                  </li>
                  <li className="flex items-center gap-2">
                    <span className="text-green-500">+</span>
                    Unlimited notification channels
                  </li>
                  <li className="flex items-center gap-2">
                    <span className="text-green-500">+</span>
                    Priority support
                  </li>
                </ul>
                <div className="flex items-center gap-4">
                  <Button onClick={handleUpgrade} disabled={loading}>
                    <CreditCard className="h-4 w-4 mr-2" />
                    {loading ? 'Loading...' : 'Upgrade for $9.99/month'}
                  </Button>
                </div>
              </div>
            ) : (
              <Button variant="outline" onClick={handleManageBilling} disabled={loading}>
                <CreditCard className="h-4 w-4 mr-2" />
                {loading ? 'Loading...' : 'Manage Billing'}
              </Button>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>About URL Watchdog</CardTitle>
          </CardHeader>
          <CardContent className="text-gray-600 space-y-2">
            <p>
              URL Watchdog monitors web pages for specific keywords and sends you alerts 
              when they appear. Perfect for tracking product availability, price changes, 
              news mentions, and more.
            </p>
            <p className="text-sm">
              Note: This is a proof-of-concept application. Data is stored in memory and 
              will be lost when the server restarts. For production use, please contact us 
              for a persistent storage solution.
            </p>
          </CardContent>
        </Card>
      </main>
    </div>
  );
}

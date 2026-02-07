import {
  Users,
  Bell,
  Settings,
  Home,
  UserCheck,
  Calendar,
} from 'lucide-react';
import { useState } from 'react';

import { ChildSelection } from '@/components/Parent/ChildSelection';
import { ParentDashboard } from '@/components/Parent/ParentDashboard';
import { ParentNotifications } from '@/components/Parent/ParentNotifications';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

type TabType = 'dashboard' | 'children' | 'notifications' | 'settings';

export const ParentPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<TabType>('dashboard');

  const tabs = [
    {
      id: 'dashboard' as TabType,
      label: 'Ana Sayfa',
      icon: Home,
      component: ParentDashboard,
    },
    {
      id: 'children' as TabType,
      label: 'Çocuklarım',
      icon: Users,
      component: ChildSelection,
    },
    {
      id: 'notifications' as TabType,
      label: 'Bildirimler',
      icon: Bell,
      component: ParentNotifications,
    },
    {
      id: 'settings' as TabType,
      label: 'Ayarlar',
      icon: Settings,
      component: () => <div className="p-6">Ayarlar sayfası yakında...</div>,
    },
  ];

  const ActiveComponent = tabs.find(tab => tab.id === activeTab)?.component || ParentDashboard;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Veli Paneli</h1>
              <p className="text-gray-600">Çocuklarınızın eğitim sürecini takip edin</p>
            </div>
            <div className="flex items-center gap-4">
              <Badge className="bg-blue-100 text-blue-800">
                <UserCheck className="h-3 w-3 mr-1" />
                Veli Hesabı
              </Badge>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="flex gap-6">
          {/* Sidebar Navigation */}
          <div className="w-64 flex-shrink-0">
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Menü</CardTitle>
              </CardHeader>
              <CardContent className="p-0">
                <nav className="space-y-1">
                  {tabs.map((tab) => {
                    const Icon = tab.icon;
                    return (
                      <button
                        key={tab.id}
                        onClick={() => setActiveTab(tab.id)}
                        className={`w-full flex items-center gap-3 px-4 py-3 text-left rounded-lg transition-colors ${
                          activeTab === tab.id
                            ? 'bg-blue-50 text-blue-700 border-r-2 border-blue-500'
                            : 'text-gray-700 hover:bg-gray-50'
                        }`}
                      >
                        <Icon className="h-5 w-5" />
                        <span className="font-medium">{tab.label}</span>
                      </button>
                    );
                  })}
                </nav>
              </CardContent>
            </Card>

            {/* Quick Stats */}
            <Card className="mt-6">
              <CardHeader>
                <CardTitle className="text-sm">Hızlı Bilgiler</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Toplam Çocuk</span>
                  <Badge variant="outline">-</Badge>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Okunmamış</span>
                  <Badge className="bg-red-100 text-red-800">-</Badge>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Bu Hafta</span>
                  <Badge className="bg-green-100 text-green-800">-</Badge>
                </div>
              </CardContent>
            </Card>

            {/* Help Card */}
            <Card className="mt-6 bg-blue-50 border-blue-200">
              <CardContent className="pt-6">
                <div className="text-center">
                  <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-3">
                    <Calendar className="h-6 w-6 text-blue-600" />
                  </div>
                  <h4 className="font-medium text-blue-900 mb-2">Haftalık Raporlar</h4>
                  <p className="text-sm text-blue-800 mb-3">
                    Her hafta çocuklarınızın performans raporlarını alın
                  </p>
                  <Button size="sm" className="bg-blue-600 hover:bg-blue-700">
                    Daha Fazla Bilgi
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Main Content */}
          <div className="flex-1">
            <ActiveComponent />
          </div>
        </div>
      </div>
    </div>
  );
};
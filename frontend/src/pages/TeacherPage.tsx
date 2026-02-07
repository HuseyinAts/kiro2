import {
  LayoutDashboard,
  Users,
  FileText,
  Bell,
  BarChart3,
} from 'lucide-react';
import { useState } from 'react';

// Öğretmen bileşenlerini import et
import ClassReport from '@/components/Teacher/ClassReport';
import StudentList from '@/components/Teacher/StudentList';
import TeacherDashboard from '@/components/Teacher/TeacherDashboard';
import TeacherNotifications from '@/components/Teacher/TeacherNotifications';
import { Card, CardContent } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

const TeacherPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState('dashboard');

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-6">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          {/* Tab Navigation */}
          <div className="bg-white rounded-lg shadow-sm border">
            <TabsList className="grid w-full grid-cols-5 h-16">
              <TabsTrigger
                value="dashboard"
                className="flex flex-col items-center space-y-1 h-full"
              >
                <LayoutDashboard className="h-5 w-5" />
                <span className="text-xs">Dashboard</span>
              </TabsTrigger>

              <TabsTrigger
                value="students"
                className="flex flex-col items-center space-y-1 h-full"
              >
                <Users className="h-5 w-5" />
                <span className="text-xs">Öğrenciler</span>
              </TabsTrigger>

              <TabsTrigger
                value="reports"
                className="flex flex-col items-center space-y-1 h-full"
              >
                <FileText className="h-5 w-5" />
                <span className="text-xs">Raporlar</span>
              </TabsTrigger>

              <TabsTrigger
                value="notifications"
                className="flex flex-col items-center space-y-1 h-full"
              >
                <Bell className="h-5 w-5" />
                <span className="text-xs">Bildirimler</span>
              </TabsTrigger>

              <TabsTrigger
                value="analytics"
                className="flex flex-col items-center space-y-1 h-full"
              >
                <BarChart3 className="h-5 w-5" />
                <span className="text-xs">Analitik</span>
              </TabsTrigger>
            </TabsList>
          </div>

          {/* Tab Contents */}
          <div className="bg-white rounded-lg shadow-sm border min-h-[600px]">
            <TabsContent value="dashboard" className="m-0">
              <TeacherDashboard />
            </TabsContent>

            <TabsContent value="students" className="m-0">
              <StudentList />
            </TabsContent>

            <TabsContent value="reports" className="m-0">
              <ClassReport />
            </TabsContent>

            <TabsContent value="notifications" className="m-0">
              <TeacherNotifications />
            </TabsContent>

            <TabsContent value="analytics" className="m-0">
              <div className="p-6">
                <Card>
                  <CardContent className="pt-6">
                    <div className="text-center py-12">
                      <BarChart3 className="h-16 w-16 text-gray-400 mx-auto mb-4" />
                      <h3 className="text-lg font-medium text-gray-900 mb-2">
                        Gelişmiş Analitik
                      </h3>
                      <p className="text-gray-600 mb-4">
                        Detaylı performans analizi ve trend raporları yakında eklenecek
                      </p>
                      <div className="space-y-2 text-sm text-gray-500">
                        <p>• Öğrenci performans trendleri</p>
                        <p>• Konu bazlı başarı analizi</p>
                        <p>• Karşılaştırmalı sınıf raporları</p>
                        <p>• Tahmine dayalı başarı modelleri</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>
            </TabsContent>
          </div>
        </Tabs>
      </div>
    </div>
  );
};

export default TeacherPage;
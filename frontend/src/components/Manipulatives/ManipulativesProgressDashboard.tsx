/**
 * Manipulatives Progress Dashboard - Task 87.9
 * REQ-51.101-51.105: Progress tracking, visualization, achievement badges
 */
import axios from 'axios';
import * as React from 'react';
import {  useState, useEffect  } from 'react';
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';

interface ProgressData {
  virtualBlocks: {
    total_operations: number;
    operations_by_type: { [key: string]: number };
    avg_duration: number;
    mastery_level: number;
  };
  geogebra: {
    total_activities: number;
    activities_by_type: { [key: string]: number };
    completion_rate: number;
    avg_duration: number;
  };
  geometry: {
    total_shapes: number;
    shapes_by_type: { [key: string]: number };
    measurements_count: number;
    tools_used: string[];
  };
  tangram: {
    puzzles_attempted: number;
    puzzles_completed: number;
    completion_rate: number;
    avg_attempts: number;
  };
}

interface Badge {
  id: string;
  name: string;
  description: string;
  icon: string;
  earned: boolean;
  earnedDate?: string;
}

interface ManipulativesProgressDashboardProps {
  userId?: number;
}

const ManipulativesProgressDashboard: React.FC<ManipulativesProgressDashboardProps> = ({ userId }) => {
  const [progressData, setProgressData] = useState<ProgressData | null>(null);
  const [badges, setBadges] = useState<Badge[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedView, setSelectedView] = useState<'overview' | 'details' | 'badges'>('overview');

  // Load progress data
  useEffect(() => {
    loadProgressData();
    loadBadges();
  }, [userId]);

  const loadProgressData = async () => {
    try {
      const response = await axios.get('/api/manipulatives/progress/dashboard');
      if (response.data.success) {
        setProgressData(response.data.data);
      }
    } catch (error) {
      console.error('Progress data could not be loaded:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadBadges = async () => {
    try {
      const response = await axios.get('/api/manipulatives/badges');
      if (response.data.success) {
        setBadges(response.data.data);
      }
    } catch (error) {
      console.error('Badges could not be loaded:', error);
    }
  };

  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'];

  if (loading) {
    return (
      <div className="flex justify-center items-center h-96">
        <div className="text-xl">Yükleniyor...</div>
      </div>
    );
  }

  if (!progressData) {
    return (
      <div className="p-6 bg-white rounded-lg shadow-lg">
        <p>İlerleme verisi bulunamadı.</p>
      </div>
    );
  }

  // Prepare chart data
  const virtualBlocksData = Object.entries(progressData.virtualBlocks.operations_by_type).map(([key, value]) => ({
    name: key === 'add' ? 'Toplama' : key === 'subtract' ? 'Çıkarma' : key === 'multiply' ? 'Çarpma' : 'Bölme',
    value,
  }));

  const geogebraData = Object.entries(progressData.geogebra.activities_by_type).map(([key, value]) => ({
    name: key === 'geometry' ? 'Geometri' : key === 'algebra' ? 'Cebir' : 'Hesaplama',
    value,
  }));

  const geometryData = Object.entries(progressData.geometry.shapes_by_type).map(([key, value]) => ({
    name: key === 'line' ? 'Doğru' : key === 'circle' ? 'Daire' : key === 'rectangle' ? 'Dikdörtgen' : 'Üçgen',
    value,
  }));

  const overallProgress = [
    { name: 'Sanal Bloklar', mastery: progressData.virtualBlocks.mastery_level },
    { name: 'GeoGebra', completion: progressData.geogebra.completion_rate * 100 },
    { name: 'Geometri', shapes: progressData.geometry.total_shapes },
    { name: 'Tangram', completion: progressData.tangram.completion_rate * 100 },
  ];

  return (
    <div className="manipulatives-progress-dashboard p-6 bg-white rounded-lg shadow-lg">
      <h2 className="text-3xl font-bold mb-6">Manipülatifler İlerleme Panosu</h2>

      {/* View Selector */}
      <div className="view-selector mb-6 flex gap-2">
        <button
          onClick={() => setSelectedView('overview')}
          className={`px-6 py-3 rounded-lg font-medium transition-all ${
            selectedView === 'overview'
              ? 'bg-blue-500 text-white shadow-lg'
              : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
          }`}
        >
          📊 Genel Bakış
        </button>
        <button
          onClick={() => setSelectedView('details')}
          className={`px-6 py-3 rounded-lg font-medium transition-all ${
            selectedView === 'details'
              ? 'bg-blue-500 text-white shadow-lg'
              : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
          }`}
        >
          📈 Detaylı İstatistikler
        </button>
        <button
          onClick={() => setSelectedView('badges')}
          className={`px-6 py-3 rounded-lg font-medium transition-all ${
            selectedView === 'badges'
              ? 'bg-blue-500 text-white shadow-lg'
              : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
          }`}
        >
          🏆 Rozetler
        </button>
      </div>

      {/* Overview View */}
      {selectedView === 'overview' && (
        <div className="overview-section">
          {/* Summary Cards */}
          <div className="summary-cards grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
            <div className="card p-4 bg-gradient-to-br from-green-400 to-green-600 rounded-lg shadow text-white">
              <div className="text-sm opacity-90">Sanal Bloklar</div>
              <div className="text-3xl font-bold">{progressData.virtualBlocks.total_operations}</div>
              <div className="text-sm opacity-90">İşlem Tamamlandı</div>
              <div className="mt-2 text-sm">
                Ustalık: {progressData.virtualBlocks.mastery_level}%
              </div>
            </div>

            <div className="card p-4 bg-gradient-to-br from-blue-400 to-blue-600 rounded-lg shadow text-white">
              <div className="text-sm opacity-90">GeoGebra</div>
              <div className="text-3xl font-bold">{progressData.geogebra.total_activities}</div>
              <div className="text-sm opacity-90">Aktivite Tamamlandı</div>
              <div className="mt-2 text-sm">
                Tamamlanma: {(progressData.geogebra.completion_rate * 100).toFixed(0)}%
              </div>
            </div>

            <div className="card p-4 bg-gradient-to-br from-purple-400 to-purple-600 rounded-lg shadow text-white">
              <div className="text-sm opacity-90">Geometri</div>
              <div className="text-3xl font-bold">{progressData.geometry.total_shapes}</div>
              <div className="text-sm opacity-90">Şekil Çizildi</div>
              <div className="mt-2 text-sm">
                {progressData.geometry.measurements_count} Ölçüm
              </div>
            </div>

            <div className="card p-4 bg-gradient-to-br from-orange-400 to-orange-600 rounded-lg shadow text-white">
              <div className="text-sm opacity-90">Tangram</div>
              <div className="text-3xl font-bold">{progressData.tangram.puzzles_completed}</div>
              <div className="text-sm opacity-90">/ {progressData.tangram.puzzles_attempted} Puzzle</div>
              <div className="mt-2 text-sm">
                Başarı: {(progressData.tangram.completion_rate * 100).toFixed(0)}%
              </div>
            </div>
          </div>

          {/* Charts */}
          <div className="charts-grid grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Virtual Blocks Operations */}
            <div className="chart-container bg-gray-50 p-4 rounded-lg">
              <h3 className="text-lg font-semibold mb-4">Sanal Bloklar İşlem Dağılımı</h3>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={virtualBlocksData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="value" fill="#4CAF50" name="İşlem Sayısı" />
                </BarChart>
              </ResponsiveContainer>
            </div>

            {/* GeoGebra Activities */}
            <div className="chart-container bg-gray-50 p-4 rounded-lg">
              <h3 className="text-lg font-semibold mb-4">GeoGebra Aktivite Türleri</h3>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={geogebraData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={(entry) => `${entry.name}: ${entry.value}`}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {geogebraData.map((_entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>

            {/* Geometry Shapes */}
            <div className="chart-container bg-gray-50 p-4 rounded-lg">
              <h3 className="text-lg font-semibold mb-4">Geometri Şekil Dağılımı</h3>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={geometryData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="value" fill="#9C27B0" name="Şekil Sayısı" />
                </BarChart>
              </ResponsiveContainer>
            </div>

            {/* Overall Progress */}
            <div className="chart-container bg-gray-50 p-4 rounded-lg">
              <h3 className="text-lg font-semibold mb-4">Genel İlerleme</h3>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={overallProgress}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Line type="monotone" dataKey="mastery" stroke="#4CAF50" name="Ustalık (%)" />
                  <Line type="monotone" dataKey="completion" stroke="#2196F3" name="Tamamlanma (%)" />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      )}

      {/* Details View */}
      {selectedView === 'details' && (
        <div className="details-section">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Virtual Blocks Details */}
            <div className="detail-card p-6 bg-gradient-to-br from-green-50 to-green-100 rounded-lg shadow">
              <h3 className="text-xl font-bold mb-4 text-green-800">🟢 Sanal Bloklar</h3>
              <div className="stats space-y-2 text-sm">
                <div className="flex justify-between">
                  <span>Toplam İşlem:</span>
                  <span className="font-bold">{progressData.virtualBlocks.total_operations}</span>
                </div>
                <div className="flex justify-between">
                  <span>Ortalama Süre:</span>
                  <span className="font-bold">{progressData.virtualBlocks.avg_duration}s</span>
                </div>
                <div className="flex justify-between">
                  <span>Ustalık Seviyesi:</span>
                  <span className="font-bold">{progressData.virtualBlocks.mastery_level}%</span>
                </div>
                <div className="mt-4">
                  <div className="text-xs text-gray-600 mb-1">İşlem Dağılımı:</div>
                  {Object.entries(progressData.virtualBlocks.operations_by_type).map(([key, value]) => (
                    <div key={key} className="flex justify-between text-xs">
                      <span>{key}:</span>
                      <span>{value}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* GeoGebra Details */}
            <div className="detail-card p-6 bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg shadow">
              <h3 className="text-xl font-bold mb-4 text-blue-800">🔵 GeoGebra</h3>
              <div className="stats space-y-2 text-sm">
                <div className="flex justify-between">
                  <span>Toplam Aktivite:</span>
                  <span className="font-bold">{progressData.geogebra.total_activities}</span>
                </div>
                <div className="flex justify-between">
                  <span>Ortalama Süre:</span>
                  <span className="font-bold">{progressData.geogebra.avg_duration}s</span>
                </div>
                <div className="flex justify-between">
                  <span>Tamamlanma Oranı:</span>
                  <span className="font-bold">{(progressData.geogebra.completion_rate * 100).toFixed(0)}%</span>
                </div>
                <div className="mt-4">
                  <div className="text-xs text-gray-600 mb-1">Aktivite Türleri:</div>
                  {Object.entries(progressData.geogebra.activities_by_type).map(([key, value]) => (
                    <div key={key} className="flex justify-between text-xs">
                      <span>{key}:</span>
                      <span>{value}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Geometry Details */}
            <div className="detail-card p-6 bg-gradient-to-br from-purple-50 to-purple-100 rounded-lg shadow">
              <h3 className="text-xl font-bold mb-4 text-purple-800">🟣 İnteraktif Geometri</h3>
              <div className="stats space-y-2 text-sm">
                <div className="flex justify-between">
                  <span>Toplam Şekil:</span>
                  <span className="font-bold">{progressData.geometry.total_shapes}</span>
                </div>
                <div className="flex justify-between">
                  <span>Ölçüm Sayısı:</span>
                  <span className="font-bold">{progressData.geometry.measurements_count}</span>
                </div>
                <div className="flex justify-between">
                  <span>Kullanılan Araçlar:</span>
                  <span className="font-bold">{progressData.geometry.tools_used.length}</span>
                </div>
                <div className="mt-4">
                  <div className="text-xs text-gray-600 mb-1">Şekil Dağılımı:</div>
                  {Object.entries(progressData.geometry.shapes_by_type).map(([key, value]) => (
                    <div key={key} className="flex justify-between text-xs">
                      <span>{key}:</span>
                      <span>{value}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Tangram Details */}
            <div className="detail-card p-6 bg-gradient-to-br from-orange-50 to-orange-100 rounded-lg shadow">
              <h3 className="text-xl font-bold mb-4 text-orange-800">🟠 Dijital Tangram</h3>
              <div className="stats space-y-2 text-sm">
                <div className="flex justify-between">
                  <span>Denenen Puzzle:</span>
                  <span className="font-bold">{progressData.tangram.puzzles_attempted}</span>
                </div>
                <div className="flex justify-between">
                  <span>Tamamlanan:</span>
                  <span className="font-bold">{progressData.tangram.puzzles_completed}</span>
                </div>
                <div className="flex justify-between">
                  <span>Başarı Oranı:</span>
                  <span className="font-bold">{(progressData.tangram.completion_rate * 100).toFixed(0)}%</span>
                </div>
                <div className="flex justify-between">
                  <span>Ortalama Deneme:</span>
                  <span className="font-bold">{progressData.tangram.avg_attempts}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Badges View */}
      {selectedView === 'badges' && (
        <div className="badges-section">
          <h3 className="text-2xl font-bold mb-6">Kazanılan Rozetler</h3>
          <div className="badges-grid grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {badges.map((badge) => (
              <div
                key={badge.id}
                className={`badge-card p-4 rounded-lg shadow transition-all ${
                  badge.earned
                    ? 'bg-gradient-to-br from-yellow-400 to-yellow-600 text-white'
                    : 'bg-gray-200 text-gray-400'
                }`}
              >
                <div className="badge-icon text-4xl mb-2 text-center">{badge.icon}</div>
                <h4 className="font-bold text-center mb-1">{badge.name}</h4>
                <p className="text-xs text-center">{badge.description}</p>
                {badge.earned && badge.earnedDate && (
                  <div className="text-xs text-center mt-2 opacity-80">
                    {new Date(badge.earnedDate).toLocaleDateString('tr-TR')}
                  </div>
                )}
              </div>
            ))}
          </div>

          {badges.filter((b) => !b.earned).length > 0 && (
            <div className="mt-6 p-4 bg-blue-50 rounded-lg">
              <p className="text-sm text-gray-700">
                <strong>💡 İpucu:</strong> Daha fazla manipülatif kullanarak yeni rozetler kazanabilirsiniz!
                {' '}Henüz {badges.filter((b) => !b.earned).length} rozet kazanılmayı bekliyor.
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default ManipulativesProgressDashboard;

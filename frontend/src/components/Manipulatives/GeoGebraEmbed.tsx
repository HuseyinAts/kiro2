/**
 * GeoGebra Entegrasyonu - Task 87.2
 * REQ-51.86-51.90: GeoGebra embed, interactive geometry, dynamic mathematics
 */
import axios from 'axios';
import * as React from 'react';
import {  useState, useEffect, useRef  } from 'react';

interface GeoGebraApplet {
  id: string;
  name: string;
  type: string;
  url: string;
  description: string;
}

interface GeoGebraEmbedProps {
  appletId?: string;
  width?: number;
  height?: number;
  onActivityComplete?: (completed: boolean) => void;
}

const GeoGebraEmbed: React.FC<GeoGebraEmbedProps> = ({
  appletId = 'geometry-basic',
  width = 800,
  height = 600,
  onActivityComplete,
}) => {
  const [applets, setApplets] = useState<GeoGebraApplet[]>([]);
  const [selectedApplet, setSelectedApplet] = useState<GeoGebraApplet | null>(null);
  const [startTime, setStartTime] = useState<number>(Date.now());
  const [isLoading, setIsLoading] = useState(true);
  const iframeRef = useRef<HTMLIFrameElement>(null);

  // Applet listesini yükle
  useEffect(() => {
    loadApplets();
  }, []);

  const loadApplets = async () => {
    try {
      const response = await axios.get('/api/manipulatives/geogebra/applets');
      if (response.data.success) {
        setApplets(response.data.data);
        const defaultApplet = response.data.data.find((a: GeoGebraApplet) => a.id === appletId);
        if (defaultApplet) {
          setSelectedApplet(defaultApplet);
        }
      }
    } catch (error) {
      console.error('Applet listesi yüklenemedi:', error);
    } finally {
      setIsLoading(false);
    }
  };

  // Applet değiştir
  const changeApplet = (applet: GeoGebraApplet) => {
    setSelectedApplet(applet);
    setStartTime(Date.now());
  };

  // Aktiviteyi kaydet
  const saveActivity = async (completed: boolean) => {
    if (!selectedApplet) {return;}

    try {
      const duration = Math.floor((Date.now() - startTime) / 1000);

      await axios.post('/api/manipulatives/geogebra/activity', {
        user_id: 0, // Backend'de current_user'dan alınacak
        applet_id: selectedApplet.id,
        activity_type: selectedApplet.type,
        duration_seconds: duration,
        completed,
      });

      if (onActivityComplete) {
        onActivityComplete(completed);
      }

      alert(completed ? 'Aktivite tamamlandı!' : 'Aktivite kaydedildi!');
    } catch (error) {
      console.error('Aktivite kaydedilemedi:', error);
      alert('Aktivite kaydedilemedi. Lütfen tekrar deneyin.');
    }
  };

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-96">
        <div className="text-xl">Yükleniyor...</div>
      </div>
    );
  }

  return (
    <div className="geogebra-container p-6 bg-white rounded-lg shadow-lg">
      <h2 className="text-2xl font-bold mb-4">GeoGebra İnteraktif Matematik</h2>

      {/* Applet seçici */}
      <div className="applet-selector mb-4">
        <label className="block text-sm font-medium mb-2">Aktivite Seç:</label>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {applets.map(applet => (
            <button
              key={applet.id}
              onClick={() => changeApplet(applet)}
              className={`p-4 border-2 rounded-lg text-left transition-all ${
                selectedApplet?.id === applet.id
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-300 hover:border-blue-300'
              }`}
            >
              <h3 className="font-bold text-lg mb-1">{applet.name}</h3>
              <p className="text-sm text-gray-600">{applet.description}</p>
              <span className="inline-block mt-2 px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded">
                {applet.type}
              </span>
            </button>
          ))}
        </div>
      </div>

      {/* GeoGebra iframe */}
      {selectedApplet && (
        <div className="geogebra-embed mb-4">
          <iframe
            ref={iframeRef}
            src={selectedApplet.url}
            width={width}
            height={height}
            className="border-2 border-gray-300 rounded"
            title={selectedApplet.name}
            allow="fullscreen"
          />
        </div>
      )}

      {/* Kontroller */}
      <div className="controls flex justify-between items-center">
        <div className="info text-sm text-gray-600">
          {selectedApplet && (
            <>
              <strong>Aktif:</strong> {selectedApplet.name} ({selectedApplet.type})
            </>
          )}
        </div>
        <div className="actions flex gap-2">
          <button
            onClick={() => saveActivity(false)}
            className="px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600"
            disabled={!selectedApplet}
          >
            Kaydet
          </button>
          <button
            onClick={() => saveActivity(true)}
            className="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600"
            disabled={!selectedApplet}
          >
            Tamamla
          </button>
        </div>
      </div>

      {/* Yardım metni */}
      <div className="help-text mt-4 p-4 bg-blue-50 rounded">
        <p className="text-sm text-gray-700">
          <strong>GeoGebra Hakkında:</strong><br />
          GeoGebra, dinamik matematik yazılımıdır. Geometri, cebir, istatistik ve hesaplama
          konularında interaktif öğrenme sağlar.<br /><br />
          <strong>İpuçları:</strong><br />
          • Araçları kullanarak şekiller çizin<br />
          • Noktaları sürükleyerek dinamik değişimleri gözlemleyin<br />
          • Ölçüm araçlarıyla uzunluk ve açı ölçün
        </p>
      </div>
    </div>
  );
};

export default GeoGebraEmbed;

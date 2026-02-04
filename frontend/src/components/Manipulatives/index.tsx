/**
 * Manipülatifler Ana Bileşeni - Task 87
 * Tüm manipülatif araçları bir arada
 */
import React, { useState } from 'react';
import VirtualBlocks from './VirtualBlocks';
import GeoGebraEmbed from './GeoGebraEmbed';
import InteractiveGeometry from './InteractiveGeometry';
import DigitalTangram from './DigitalTangram';
import ManipulativesProgressDashboard from './ManipulativesProgressDashboard';

type ManipulativeType = 'blocks' | 'geogebra' | 'geometry' | 'tangram' | 'progress';

const Manipulatives: React.FC = () => {
  const [activeTab, setActiveTab] = useState<ManipulativeType>('blocks');

  const tabs = [
    { id: 'blocks' as ManipulativeType, name: 'Sanal Bloklar', icon: '🧱', description: 'Sayı blokları ile işlemler' },
    { id: 'geogebra' as ManipulativeType, name: 'GeoGebra', icon: '📐', description: 'Dinamik matematik' },
    { id: 'geometry' as ManipulativeType, name: 'Geometri', icon: '📏', description: 'İnteraktif çizim araçları' },
    { id: 'tangram' as ManipulativeType, name: 'Tangram', icon: '🧩', description: 'Şekil bulmacası' },
    { id: 'progress' as ManipulativeType, name: 'İlerleme', icon: '📊', description: 'İstatistikler ve rozetler' }
  ];

  return (
    <div className="manipulatives-page min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Başlık */}
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Matematik Manipülatifleri
          </h1>
          <p className="text-gray-600">
            İnteraktif araçlarla matematik öğrenin - Diskalkuli desteği
          </p>
        </div>

        {/* Tab menüsü */}
        <div className="bg-white rounded-lg shadow-md mb-6">
          <div className="flex border-b">
            {tabs.map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex-1 px-6 py-4 text-center transition-all ${
                  activeTab === tab.id
                    ? 'border-b-4 border-blue-500 bg-blue-50'
                    : 'hover:bg-gray-50'
                }`}
              >
                <div className="text-3xl mb-1">{tab.icon}</div>
                <div className="font-semibold text-gray-900">{tab.name}</div>
                <div className="text-xs text-gray-600">{tab.description}</div>
              </button>
            ))}
          </div>
        </div>

        {/* İçerik */}
        <div className="content">
          {activeTab === 'blocks' && <VirtualBlocks />}
          {activeTab === 'geogebra' && <GeoGebraEmbed />}
          {activeTab === 'geometry' && <InteractiveGeometry />}
          {activeTab === 'tangram' && <DigitalTangram />}
          {activeTab === 'progress' && <ManipulativesProgressDashboard />}
        </div>

        {/* Bilgilendirme */}
        <div className="mt-6 p-4 bg-yellow-50 border-l-4 border-yellow-400 rounded">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-yellow-400" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-sm text-yellow-700">
                <strong>Diskalkuli Desteği:</strong> Bu araçlar, matematik öğrenme güçlüğü olan öğrenciler için özel olarak tasarlanmıştır. 
                Görsel ve interaktif öğrenme yöntemleriyle matematiksel kavramları daha kolay anlamanıza yardımcı olur.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Manipulatives;

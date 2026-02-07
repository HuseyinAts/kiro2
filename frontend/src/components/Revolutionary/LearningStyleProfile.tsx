/**
 * Öğrenme Stili Profil Bileşeni
 * VARK + Felder-Silverman hibrit öğrenme stili görüntüleme
 */

import * as React from 'react';
import {  useState, useEffect  } from 'react';

import { revolutionaryFeaturesService, HybridLearningProfile, ContentRecommendation } from '../../services/revolutionaryFeaturesService';

interface LearningStyleProfileProps {
  studentId: string;
  onProfileUpdate?: (profile: HybridLearningProfile) => void;
}

const LearningStyleProfile: React.FC<LearningStyleProfileProps> = ({
  studentId,
  onProfileUpdate,
}) => {
  const [profile, setProfile] = useState<HybridLearningProfile | null>(null);
  const [recommendations, setRecommendations] = useState<ContentRecommendation | null>(null);
  const [explanation, setExplanation] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Profil verilerini yükle
  useEffect(() => {
    const loadProfileData = async () => {
      try {
        setLoading(true);
        setError(null);

        // Öğrenme stili profilini tespit et
        const learningProfile = await revolutionaryFeaturesService.detectLearningStyle(studentId);
        setProfile(learningProfile);
        onProfileUpdate?.(learningProfile);

        // İçerik önerilerini al
        const contentRecs = await revolutionaryFeaturesService.getContentRecommendations(studentId);
        setRecommendations(contentRecs);

        // Açıklamayı al
        const profileExplanation = await revolutionaryFeaturesService.getLearningStyleExplanation(studentId);
        setExplanation(profileExplanation);

      } catch (err) {
        setError(err instanceof Error ? err.message : 'Öğrenme stili verileri yüklenirken hata oluştu');
      } finally {
        setLoading(false);
      }
    };

    if (studentId) {
      loadProfileData();
    }
  }, [studentId, onProfileUpdate]);

  // VARK profil renk kodlaması
  const getVARKColor = (type: string) => {
    switch (type) {
      case 'visual': return 'bg-blue-100 text-blue-800';
      case 'auditory': return 'bg-green-100 text-green-800';
      case 'reading': return 'bg-purple-100 text-purple-800';
      case 'kinesthetic': return 'bg-orange-100 text-orange-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  // Felder-Silverman boyut renk kodlaması
  const getFelderColor = (dimension: string) => {
    switch (dimension) {
      case 'active_reflective': return 'bg-red-100 text-red-800';
      case 'sensing_intuitive': return 'bg-indigo-100 text-indigo-800';
      case 'visual_verbal': return 'bg-teal-100 text-teal-800';
      case 'sequential_global': return 'bg-pink-100 text-pink-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  // Güven seviyesi renk kodlaması
  const getConfidenceColor = (level: string) => {
    switch (level) {
      case 'yüksek': return 'text-green-600';
      case 'orta': return 'text-yellow-600';
      case 'düşük': return 'text-red-600';
      default: return 'text-gray-600';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <span className="ml-2 text-gray-600">Öğrenme stili analizi yükleniyor...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <div className="flex">
          <div className="flex-shrink-0">
            <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
            </svg>
          </div>
          <div className="ml-3">
            <h3 className="text-sm font-medium text-red-800">Hata</h3>
            <p className="mt-1 text-sm text-red-700">{error}</p>
          </div>
        </div>
      </div>
    );
  }

  if (!profile) {
    return (
      <div className="text-center p-8 text-gray-500">
        Öğrenme stili profili bulunamadı
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Hibrit Profil Özeti */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          🚀 Hibrit Öğrenme Stili Profili
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <div className="text-center">
            <div className="text-2xl font-bold text-purple-600">{profile.hybrid_code}</div>
            <div className="text-sm text-gray-600">Hibrit Kod</div>
          </div>
          <div className="text-center">
            <div className={`text-2xl font-bold ${getConfidenceColor(profile.confidence.level)}`}>
              {profile.confidence.score.toFixed(1)}%
            </div>
            <div className="text-sm text-gray-600">Güven Seviyesi</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-600">{profile.data_points_used}</div>
            <div className="text-sm text-gray-600">Veri Noktası</div>
          </div>
        </div>

        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <h4 className="font-medium text-blue-900 mb-2">Profil Özeti</h4>
          <p className="text-sm text-blue-800">
            Bu profil, VARK duyusal tercihleriniz ve Felder-Silverman bilişsel süreçlerinizi
            birleştirerek 64 farklı öğrenme kombinasyonundan size en uygun olanını belirler.
          </p>
        </div>
      </div>

      {/* VARK Profili */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          VARK Duyusal Tercihler
        </h3>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center">
            <div className={`p-4 rounded-lg ${getVARKColor('visual')}`}>
              <div className="text-2xl font-bold">{(profile.vark_profile.visual * 100).toFixed(0)}%</div>
              <div className="text-sm font-medium">Görsel</div>
            </div>
            <div className="text-xs text-gray-600 mt-2">Diyagramlar, grafikler</div>
          </div>

          <div className="text-center">
            <div className={`p-4 rounded-lg ${getVARKColor('auditory')}`}>
              <div className="text-2xl font-bold">{(profile.vark_profile.auditory * 100).toFixed(0)}%</div>
              <div className="text-sm font-medium">İşitsel</div>
            </div>
            <div className="text-xs text-gray-600 mt-2">Sesli açıklamalar</div>
          </div>

          <div className="text-center">
            <div className={`p-4 rounded-lg ${getVARKColor('reading')}`}>
              <div className="text-2xl font-bold">{(profile.vark_profile.reading * 100).toFixed(0)}%</div>
              <div className="text-sm font-medium">Okuma</div>
            </div>
            <div className="text-xs text-gray-600 mt-2">Metin, listeler</div>
          </div>

          <div className="text-center">
            <div className={`p-4 rounded-lg ${getVARKColor('kinesthetic')}`}>
              <div className="text-2xl font-bold">{(profile.vark_profile.kinesthetic * 100).toFixed(0)}%</div>
              <div className="text-sm font-medium">Kinestetik</div>
            </div>
            <div className="text-xs text-gray-600 mt-2">Uygulamalı çalışma</div>
          </div>
        </div>

        <div className="mt-4 p-3 bg-gray-50 rounded-lg">
          <div className="text-sm font-medium text-gray-700 mb-1">Dominant Tercih</div>
          <div className={`inline-block px-3 py-1 rounded-full text-sm font-medium ${getVARKColor(profile.vark_profile.dominant)}`}>
            {profile.vark_profile.dominant.charAt(0).toUpperCase() + profile.vark_profile.dominant.slice(1)}
          </div>
        </div>
      </div>

      {/* Felder-Silverman Profili */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          Felder-Silverman Bilişsel Süreçler
        </h3>

        <div className="space-y-4">
          <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
            <div>
              <div className="font-medium text-gray-900">Aktif ↔ Yansıtıcı</div>
              <div className="text-sm text-gray-600">Bilgiyi nasıl işlersiniz?</div>
            </div>
            <div className={`px-3 py-1 rounded-full text-sm font-medium ${getFelderColor('active_reflective')}`}>
              {profile.felder_profile.active_reflective > 0 ? 'Aktif' : 'Yansıtıcı'}
              ({Math.abs(profile.felder_profile.active_reflective).toFixed(1)})
            </div>
          </div>

          <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
            <div>
              <div className="font-medium text-gray-900">Algısal ↔ Sezgisel</div>
              <div className="text-sm text-gray-600">Hangi bilgi türünü tercih edersiniz?</div>
            </div>
            <div className={`px-3 py-1 rounded-full text-sm font-medium ${getFelderColor('sensing_intuitive')}`}>
              {profile.felder_profile.sensing_intuitive > 0 ? 'Algısal' : 'Sezgisel'}
              ({Math.abs(profile.felder_profile.sensing_intuitive).toFixed(1)})
            </div>
          </div>

          <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
            <div>
              <div className="font-medium text-gray-900">Görsel ↔ Sözel</div>
              <div className="text-sm text-gray-600">Bilgiyi nasıl alırsınız?</div>
            </div>
            <div className={`px-3 py-1 rounded-full text-sm font-medium ${getFelderColor('visual_verbal')}`}>
              {profile.felder_profile.visual_verbal > 0 ? 'Görsel' : 'Sözel'}
              ({Math.abs(profile.felder_profile.visual_verbal).toFixed(1)})
            </div>
          </div>

          <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
            <div>
              <div className="font-medium text-gray-900">Sıralı ↔ Bütünsel</div>
              <div className="text-sm text-gray-600">Anlayışa nasıl ulaşırsınız?</div>
            </div>
            <div className={`px-3 py-1 rounded-full text-sm font-medium ${getFelderColor('sequential_global')}`}>
              {profile.felder_profile.sequential_global > 0 ? 'Sıralı' : 'Bütünsel'}
              ({Math.abs(profile.felder_profile.sequential_global).toFixed(1)})
            </div>
          </div>
        </div>

        <div className="mt-4 p-3 bg-gray-50 rounded-lg">
          <div className="text-sm font-medium text-gray-700 mb-2">Tercih Edilen Yaklaşımlar</div>
          <div className="flex flex-wrap gap-2">
            {profile.felder_profile.preferences.map((pref, index) => (
              <span key={index} className="px-2 py-1 bg-indigo-100 text-indigo-800 text-xs rounded-full">
                {pref}
              </span>
            ))}
          </div>
        </div>
      </div>

      {/* İçerik Önerileri */}
      {recommendations && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Kişiselleştirilmiş İçerik Önerileri
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h4 className="font-medium text-gray-700 mb-3">Önerilen İçerik Türleri</h4>
              <div className="space-y-2">
                {recommendations.recommended_content_types.map((type, index) => (
                  <div key={index} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                    <span className="text-sm text-gray-700">{type}</span>
                    <span className="text-sm font-medium text-blue-600">
                      {(recommendations.content_weights[type] * 100).toFixed(0)}%
                    </span>
                  </div>
                ))}
              </div>
            </div>

            <div>
              <h4 className="font-medium text-gray-700 mb-3">Öğrenme Stratejileri</h4>
              <div className="space-y-2">
                {recommendations.learning_strategies.map((strategy, index) => (
                  <div key={index} className="p-2 bg-green-50 border border-green-200 rounded">
                    <span className="text-sm text-green-800">{strategy}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="mt-4">
            <h4 className="font-medium text-gray-700 mb-3">Çalışma Teknikleri</h4>
            <div className="flex flex-wrap gap-2">
              {recommendations.study_techniques.map((technique, index) => (
                <span key={index} className="px-3 py-1 bg-purple-100 text-purple-800 text-sm rounded-full">
                  {technique}
                </span>
              ))}
            </div>
          </div>

          <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <div className="text-sm text-blue-700">Zorluk Ayarlaması</div>
                <div className="text-lg font-bold text-blue-900">
                  {recommendations.adjustments.difficulty > 0 ? '+' : ''}{(recommendations.adjustments.difficulty * 100).toFixed(0)}%
                </div>
              </div>
              <div>
                <div className="text-sm text-blue-700">Hız Ayarlaması</div>
                <div className="text-lg font-bold text-blue-900">
                  {recommendations.adjustments.pace > 0 ? '+' : ''}{(recommendations.adjustments.pace * 100).toFixed(0)}%
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Açıklama */}
      {explanation && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Profiliniz Hakkında
          </h3>

          <div className="prose prose-sm max-w-none">
            <p className="text-gray-700">{explanation.explanation}</p>
          </div>

          {explanation.recommendations && (
            <div className="mt-4 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
              <h4 className="font-medium text-yellow-800 mb-2">Öneriler</h4>
              <ul className="text-sm text-yellow-700 space-y-1">
                {explanation.recommendations.map((rec: string, index: number) => (
                  <li key={index}>• {rec}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* Profil Bilgileri */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          Profil Bilgileri
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
          <div>
            <div className="text-gray-600">İlk Tespit Tarihi</div>
            <div className="font-medium">{new Date(profile.detection_date).toLocaleDateString('tr-TR')}</div>
          </div>
          <div>
            <div className="text-gray-600">Son Güncelleme</div>
            <div className="font-medium">{new Date(profile.last_updated).toLocaleDateString('tr-TR')}</div>
          </div>
          <div>
            <div className="text-gray-600">Kullanılan Veri Noktası</div>
            <div className="font-medium">{profile.data_points_used} adet</div>
          </div>
          <div>
            <div className="text-gray-600">Güven Seviyesi</div>
            <div className={`font-medium ${getConfidenceColor(profile.confidence.level)}`}>
              {profile.confidence.level} ({profile.confidence.score.toFixed(1)}%)
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LearningStyleProfile;
/**
 * Kültürel Adaptasyon Ayarları Bileşeni
 * Türk öğrenci kültürü faktörleri ayarlama
 */

import * as React from 'react';
import {  useState, useEffect  } from 'react';

import culturalAdaptationService from '../../services/culturalAdaptationService';
import { CulturalContext } from '../../types/revolutionary';

interface CulturalAdaptationSettingsProps {
  studentId: string;
  onSettingsUpdate?: (settings: CulturalContext) => void;
}

const CulturalAdaptationSettings: React.FC<CulturalAdaptationSettingsProps> = ({
  studentId,
  onSettingsUpdate,
}) => {
  const [culturalContext, setCulturalContext] = useState<CulturalContext | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Form state
  const [formData, setFormData] = useState({
    group_learning_preference: 0.8,
    teacher_respect_level: 0.9,
    family_involvement: 0.7,
    peer_competition: 0.6,
    authority_acceptance: 0.8,
    collective_success: 0.75,
    elder_wisdom_value: 0.85,
    social_harmony: 0.9,
  });

  // Kültürel bağlamı yükle
  useEffect(() => {
    const loadCulturalContext = async () => {
      try {
        setLoading(true);
        setError(null);

        console.log(`Loading cultural adaptation for student: ${studentId}`);

        // Backend API'den kültürel adaptasyon verilerini al
        const adaptationResult = await culturalAdaptationService.getStudentCulturalAdaptation(studentId);

        if (adaptationResult.success && adaptationResult.data) {
          const adaptation = adaptationResult.data;

          // Kültürel bağlam oluştur
          const context: CulturalContext = {
            student_id: studentId,
            group_learning_preference: adaptation.cultural_factors.group_study_preference,
            teacher_respect_level: adaptation.cultural_factors.teacher_respect_level,
            family_involvement: adaptation.cultural_factors.family_pressure_level,
            peer_competition: adaptation.cultural_factors.peer_competition_level,
            authority_acceptance: adaptation.cultural_factors.authority_acceptance_level,
            collective_success: adaptation.cultural_factors.collective_success_orientation,
            elder_wisdom_value: adaptation.cultural_factors.elder_wisdom_value,
            social_harmony: adaptation.cultural_factors.social_harmony_importance,
            detected_at: adaptation.last_updated,
          };

          setCulturalContext(context);

          // Form verilerini güncelle
          setFormData({
            group_learning_preference: context.group_learning_preference,
            teacher_respect_level: context.teacher_respect_level,
            family_involvement: context.family_involvement,
            peer_competition: context.peer_competition,
            authority_acceptance: context.authority_acceptance,
            collective_success: context.collective_success,
            elder_wisdom_value: context.elder_wisdom_value,
            social_harmony: context.social_harmony,
          });

        } else {
          // API başarısız olursa fallback: Davranışsal verilerden tespit et
          console.warn('Cultural adaptation API failed, using behavioral detection fallback');

          const sampleBehavioralData = {
            group_study_sessions: 15,
            individual_study_sessions: 8,
            teacher_question_count: 12,
            peer_interaction_count: 25,
            help_seeking_frequency: 10,
            video_watch_time: 120,
            text_reading_time: 90,
            interactive_engagement: 35,
            quiz_completion_rate: 0.85,
            hands_on_performance: 0.78,
            visual_content_performance: 0.82,
            auditory_content_performance: 0.75,
            text_content_performance: 0.80,
            note_taking_frequency: 8,
          };

          const contextResult = await culturalAdaptationService.detectCulturalContext(studentId, sampleBehavioralData);

          if (contextResult.success && contextResult.data) {
            const context = contextResult.data;
            setCulturalContext(context);

            setFormData({
              group_learning_preference: context.group_learning_preference,
              teacher_respect_level: context.teacher_respect_level,
              family_involvement: context.family_involvement,
              peer_competition: context.peer_competition,
              authority_acceptance: context.authority_acceptance,
              collective_success: context.collective_success,
              elder_wisdom_value: context.elder_wisdom_value,
              social_harmony: context.social_harmony,
            });
          } else {
            // Son fallback: Varsayılan değerler
            console.warn('Cultural context detection failed, using default values');
            const defaultContext: CulturalContext = {
              student_id: studentId,
              group_learning_preference: 0.8,
              teacher_respect_level: 0.9,
              family_involvement: 0.7,
              peer_competition: 0.6,
              authority_acceptance: 0.8,
              collective_success: 0.75,
              elder_wisdom_value: 0.85,
              social_harmony: 0.9,
              detected_at: new Date().toISOString(),
            };
            setCulturalContext(defaultContext);
          }
        }

      } catch (err) {
        console.error('Cultural context loading error:', err);
        setError(err instanceof Error ? err.message : 'Kültürel bağlam yüklenirken hata oluştu');

        // Hata durumunda varsayılan değerler
        const defaultContext: CulturalContext = {
          student_id: studentId,
          group_learning_preference: 0.8,
          teacher_respect_level: 0.9,
          family_involvement: 0.7,
          peer_competition: 0.6,
          authority_acceptance: 0.8,
          collective_success: 0.75,
          elder_wisdom_value: 0.85,
          social_harmony: 0.9,
          detected_at: new Date().toISOString(),
        };
        setCulturalContext(defaultContext);
      } finally {
        setLoading(false);
      }
    };

    if (studentId) {
      loadCulturalContext();
    }
  }, [studentId]);

  // Form değişikliklerini işle
  const handleInputChange = (field: keyof typeof formData, value: number) => {
    setFormData(prev => ({
      ...prev,
      [field]: value,
    }));
  };

  // Ayarları kaydet
  const handleSave = async () => {
    try {
      setSaving(true);
      setError(null);
      setSuccessMessage(null);

      console.log(`Saving cultural factors for student: ${studentId}`, formData);

      // Backend API'ye kültürel faktörleri gönder
      const updateResult = await culturalAdaptationService.updateCulturalFactors(studentId, {
        group_study_preference: formData.group_learning_preference,
        teacher_respect_level: formData.teacher_respect_level,
        family_pressure_level: formData.family_involvement,
        peer_competition_level: formData.peer_competition,
        authority_acceptance_level: formData.authority_acceptance,
        collective_success_orientation: formData.collective_success,
        elder_wisdom_value: formData.elder_wisdom_value,
        social_harmony_importance: formData.social_harmony,
      });

      if (updateResult.success) {
        // Başarılı güncelleme
        const updatedContext: CulturalContext = {
          student_id: studentId,
          ...formData,
          detected_at: new Date().toISOString(),
        };

        setCulturalContext(updatedContext);
        onSettingsUpdate?.(updatedContext);

        setSuccessMessage('Kültürel adaptasyon ayarları başarıyla kaydedildi!');

        console.log('Cultural factors updated successfully:', updateResult.data);
      } else {
        // API hatası durumunda fallback
        console.warn('Cultural factors update API failed, using fallback:', updateResult.message);

        const updatedContext: CulturalContext = {
          student_id: studentId,
          ...formData,
          detected_at: new Date().toISOString(),
        };

        setCulturalContext(updatedContext);
        onSettingsUpdate?.(updatedContext);

        setSuccessMessage('Kültürel adaptasyon ayarları yerel olarak kaydedildi!');
      }

      // Başarı mesajını 3 saniye sonra temizle
      setTimeout(() => setSuccessMessage(null), 3000);

    } catch (err) {
      console.error('Cultural factors save error:', err);
      setError(err instanceof Error ? err.message : 'Ayarlar kaydedilirken hata oluştu');
    } finally {
      setSaving(false);
    }
  };

  // Varsayılan değerlere sıfırla
  const handleReset = () => {
    setFormData({
      group_learning_preference: 0.8,
      teacher_respect_level: 0.9,
      family_involvement: 0.7,
      peer_competition: 0.6,
      authority_acceptance: 0.8,
      collective_success: 0.75,
      elder_wisdom_value: 0.85,
      social_harmony: 0.9,
    });
  };

  // Değer açıklaması
  const getValueDescription = (value: number) => {
    if (value >= 0.8) {return 'Yüksek';}
    if (value >= 0.6) {return 'Orta';}
    if (value >= 0.4) {return 'Düşük';}
    return 'Çok Düşük';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <span className="ml-2 text-gray-600">Kültürel ayarlar yükleniyor...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Başlık */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-2">
          🚀 Kültürel Adaptasyon Ayarları
        </h3>
        <p className="text-sm text-gray-600">
          Türk eğitim kültürüne uyarlanmış öğrenme deneyimi için kişisel tercihlerinizi ayarlayın.
          Bu ayarlar, size önerilen içerik ve öğrenme stratejilerini etkiler.
        </p>
      </div>

      {/* Hata ve Başarı Mesajları */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-sm text-red-700">{error}</p>
            </div>
          </div>
        </div>
      )}

      {successMessage && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-green-400" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-sm text-green-700">{successMessage}</p>
            </div>
          </div>
        </div>
      )}

      {/* Öğrenme Tercihleri */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h4 className="text-md font-semibold text-gray-900 mb-4">Öğrenme Tercihleri</h4>

        <div className="space-y-6">
          {/* Grup Çalışması Tercihi */}
          <div>
            <div className="flex justify-between items-center mb-2">
              <label className="text-sm font-medium text-gray-700">Grup Çalışması Tercihi</label>
              <span className="text-sm text-gray-500">
                {getValueDescription(formData.group_learning_preference)} ({(formData.group_learning_preference * 100).toFixed(0)}%)
              </span>
            </div>
            <input
              type="range"
              min="0"
              max="1"
              step="0.1"
              value={formData.group_learning_preference}
              onChange={(e) => handleInputChange('group_learning_preference', parseFloat(e.target.value))}
              className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
            />
            <div className="flex justify-between text-xs text-gray-500 mt-1">
              <span>Bireysel</span>
              <span>Grup</span>
            </div>
            <p className="text-xs text-gray-600 mt-1">
              Arkadaşlarınızla birlikte çalışmayı ne kadar tercih ediyorsunuz?
            </p>
          </div>

          {/* Öğretmen Saygısı */}
          <div>
            <div className="flex justify-between items-center mb-2">
              <label className="text-sm font-medium text-gray-700">Öğretmen Rehberliği Tercihi</label>
              <span className="text-sm text-gray-500">
                {getValueDescription(formData.teacher_respect_level)} ({(formData.teacher_respect_level * 100).toFixed(0)}%)
              </span>
            </div>
            <input
              type="range"
              min="0"
              max="1"
              step="0.1"
              value={formData.teacher_respect_level}
              onChange={(e) => handleInputChange('teacher_respect_level', parseFloat(e.target.value))}
              className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
            />
            <div className="flex justify-between text-xs text-gray-500 mt-1">
              <span>Bağımsız</span>
              <span>Rehberli</span>
            </div>
            <p className="text-xs text-gray-600 mt-1">
              Öğretmen rehberliğine ne kadar değer veriyorsunuz?
            </p>
          </div>

          {/* Akran Rekabeti */}
          <div>
            <div className="flex justify-between items-center mb-2">
              <label className="text-sm font-medium text-gray-700">Akran Rekabeti Tercihi</label>
              <span className="text-sm text-gray-500">
                {getValueDescription(formData.peer_competition)} ({(formData.peer_competition * 100).toFixed(0)}%)
              </span>
            </div>
            <input
              type="range"
              min="0"
              max="1"
              step="0.1"
              value={formData.peer_competition}
              onChange={(e) => handleInputChange('peer_competition', parseFloat(e.target.value))}
              className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
            />
            <div className="flex justify-between text-xs text-gray-500 mt-1">
              <span>İşbirlikçi</span>
              <span>Rekabetçi</span>
            </div>
            <p className="text-xs text-gray-600 mt-1">
              Arkadaşlarınızla rekabet etmeyi ne kadar seviyorsunuz?
            </p>
          </div>
        </div>
      </div>

      {/* Kültürel Değerler */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h4 className="text-md font-semibold text-gray-900 mb-4">Kültürel Değerler</h4>

        <div className="space-y-6">
          {/* Aile Katılımı */}
          <div>
            <div className="flex justify-between items-center mb-2">
              <label className="text-sm font-medium text-gray-700">Aile Katılımı</label>
              <span className="text-sm text-gray-500">
                {getValueDescription(formData.family_involvement)} ({(formData.family_involvement * 100).toFixed(0)}%)
              </span>
            </div>
            <input
              type="range"
              min="0"
              max="1"
              step="0.1"
              value={formData.family_involvement}
              onChange={(e) => handleInputChange('family_involvement', parseFloat(e.target.value))}
              className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
            />
            <p className="text-xs text-gray-600 mt-1">
              Ailenizin eğitim sürecinize katılımını ne kadar önemsiyorsunuz?
            </p>
          </div>

          {/* Kolektif Başarı */}
          <div>
            <div className="flex justify-between items-center mb-2">
              <label className="text-sm font-medium text-gray-700">Kolektif Başarı Değeri</label>
              <span className="text-sm text-gray-500">
                {getValueDescription(formData.collective_success)} ({(formData.collective_success * 100).toFixed(0)}%)
              </span>
            </div>
            <input
              type="range"
              min="0"
              max="1"
              step="0.1"
              value={formData.collective_success}
              onChange={(e) => handleInputChange('collective_success', parseFloat(e.target.value))}
              className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
            />
            <p className="text-xs text-gray-600 mt-1">
              Grup başarısını bireysel başarıya göre ne kadar önemsiyorsunuz?
            </p>
          </div>

          {/* Büyük Bilgeliği */}
          <div>
            <div className="flex justify-between items-center mb-2">
              <label className="text-sm font-medium text-gray-700">Büyük Bilgeliği Değeri</label>
              <span className="text-sm text-gray-500">
                {getValueDescription(formData.elder_wisdom_value)} ({(formData.elder_wisdom_value * 100).toFixed(0)}%)
              </span>
            </div>
            <input
              type="range"
              min="0"
              max="1"
              step="0.1"
              value={formData.elder_wisdom_value}
              onChange={(e) => handleInputChange('elder_wisdom_value', parseFloat(e.target.value))}
              className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
            />
            <p className="text-xs text-gray-600 mt-1">
              Büyüklerinizin deneyim ve bilgisine ne kadar değer veriyorsunuz?
            </p>
          </div>

          {/* Sosyal Uyum */}
          <div>
            <div className="flex justify-between items-center mb-2">
              <label className="text-sm font-medium text-gray-700">Sosyal Uyum</label>
              <span className="text-sm text-gray-500">
                {getValueDescription(formData.social_harmony)} ({(formData.social_harmony * 100).toFixed(0)}%)
              </span>
            </div>
            <input
              type="range"
              min="0"
              max="1"
              step="0.1"
              value={formData.social_harmony}
              onChange={(e) => handleInputChange('social_harmony', parseFloat(e.target.value))}
              className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
            />
            <p className="text-xs text-gray-600 mt-1">
              Sosyal uyum ve barışı ne kadar önemsiyorsunuz?
            </p>
          </div>

          {/* Otorite Kabulü */}
          <div>
            <div className="flex justify-between items-center mb-2">
              <label className="text-sm font-medium text-gray-700">Otorite Kabulü</label>
              <span className="text-sm text-gray-500">
                {getValueDescription(formData.authority_acceptance)} ({(formData.authority_acceptance * 100).toFixed(0)}%)
              </span>
            </div>
            <input
              type="range"
              min="0"
              max="1"
              step="0.1"
              value={formData.authority_acceptance}
              onChange={(e) => handleInputChange('authority_acceptance', parseFloat(e.target.value))}
              className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
            />
            <p className="text-xs text-gray-600 mt-1">
              Otorite figürlerine ne kadar saygı duyuyorsunuz?
            </p>
          </div>
        </div>
      </div>

      {/* Mevcut Ayarlar Özeti */}
      {culturalContext && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h4 className="text-md font-semibold text-gray-900 mb-4">Mevcut Profil Özeti</h4>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center p-3 bg-blue-50 rounded-lg">
              <div className="text-lg font-bold text-blue-600">
                {(formData.group_learning_preference * 100).toFixed(0)}%
              </div>
              <div className="text-xs text-gray-600">Grup Tercihi</div>
            </div>
            <div className="text-center p-3 bg-green-50 rounded-lg">
              <div className="text-lg font-bold text-green-600">
                {(formData.teacher_respect_level * 100).toFixed(0)}%
              </div>
              <div className="text-xs text-gray-600">Öğretmen Rehberliği</div>
            </div>
            <div className="text-center p-3 bg-purple-50 rounded-lg">
              <div className="text-lg font-bold text-purple-600">
                {(formData.family_involvement * 100).toFixed(0)}%
              </div>
              <div className="text-xs text-gray-600">Aile Katılımı</div>
            </div>
            <div className="text-center p-3 bg-orange-50 rounded-lg">
              <div className="text-lg font-bold text-orange-600">
                {(formData.social_harmony * 100).toFixed(0)}%
              </div>
              <div className="text-xs text-gray-600">Sosyal Uyum</div>
            </div>
          </div>
        </div>
      )}

      {/* Aksiyon Butonları */}
      <div className="flex justify-between items-center">
        <button
          onClick={handleReset}
          className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
        >
          Varsayılana Sıfırla
        </button>

        <button
          onClick={handleSave}
          disabled={saving}
          className="px-6 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {saving ? 'Kaydediliyor...' : 'Ayarları Kaydet'}
        </button>
      </div>
    </div>
  );
};

export default CulturalAdaptationSettings;
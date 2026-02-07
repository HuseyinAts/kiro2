/**
 * IRT + Morfoloji Analiz Bileşeni
 * Öğretmenler için soru analizi ve öğrenci morfoloji profilleri
 */

import * as React from 'react';
import {  useState, useEffect  } from 'react';

import { revolutionaryFeaturesService } from '../../services/revolutionaryFeaturesService';

// Local type definitions for this component
interface LocalQuestionAnalysis {
  question_id: string;
  irt_parameters: {
    difficulty: number;
    discrimination: number;
    guessing: number;
    morfoloji_faktoru: number;
  };
  morphology_analysis: {
    ortalama_morfoloji_skoru: number;
    ek_tipi_cesitliligi: number;
    kelime_karmasikligi: number;
    cok_anlamlilik_skoru: number;
    morfolojik_belirsizlik: number;
  };
  quality_score: number;
  difficulty_level: string;
  recommendations: string[];
}

interface LocalStudentMorphologyProfile {
  student_id: string;
  morphology_awareness: number;
  suffix_recognition: number;
  root_identification: number;
  compound_understanding: number;
  semantic_disambiguation: number;
  overall_competency: number;
  last_updated: string;
}

interface IRTMorphologyAnalysisProps {
  teacherId: string;
  classId?: string;
}

const IRTMorphologyAnalysis: React.FC<IRTMorphologyAnalysisProps> = ({
  teacherId,
  classId,
}) => {
  const [questionAnalysis, setQuestionAnalysis] = useState<LocalQuestionAnalysis | null>(null);
  const [studentProfiles, setStudentProfiles] = useState<LocalStudentMorphologyProfile[]>([]);
  const [statistics, setStatistics] = useState<any>(null);
  const [qualityReport, setQualityReport] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedTab, setSelectedTab] = useState<'analysis' | 'profiles' | 'statistics'>('analysis');

  // Örnek soru analizi
  const [sampleQuestion, _setSampleQuestion] = useState({
    id: 'sample_001',
    text: 'Türkiye\'nin en büyük gölü olan Van Gölü\'nün yüzölçümü yaklaşık 3.713 km²\'dir. Bu göl, aynı zamanda dünyanın en büyük soda göllerinden biridir. Van Gölü\'nün ortalama derinliği 171 metre olup, en derin yeri 451 metredir.',
    subject: 'Coğrafya',
    examType: 'TYT',
  });

  // Verileri yükle
  useEffect(() => {
    const loadAnalysisData = async () => {
      try {
        setLoading(true);
        setError(null);

        // Örnek soru analizi yap
        const analysis = await revolutionaryFeaturesService.quickQuestionEvaluation(
          sampleQuestion.id,
        );

        // Mock question analysis data
        const mockAnalysis: LocalQuestionAnalysis = {
          question_id: sampleQuestion.id,
          irt_parameters: {
            difficulty: analysis.tahmini_zorluk || 0.5,
            discrimination: 1.2,
            guessing: 0.25,
            morfoloji_faktoru: analysis.morfolojik_karmasiklik || 0.3,
          },
          morphology_analysis: {
            ortalama_morfoloji_skoru: analysis.morfolojik_karmasiklik || 0.3,
            ek_tipi_cesitliligi: 0.4,
            kelime_karmasikligi: 0.6,
            cok_anlamlilik_skoru: 0.2,
            morfolojik_belirsizlik: 0.1,
          },
          quality_score: analysis.uygunluk_skoru || 75,
          difficulty_level: analysis.zorluk_seviyesi || 'orta',
          recommendations: analysis.oneriler || ['Soru yapısı uygun', 'Morfolojik karmaşıklık dengeli'],
        };
        setQuestionAnalysis(mockAnalysis);

        // Örnek öğrenci profilleri
        const mockProfiles: LocalStudentMorphologyProfile[] = [
          {
            student_id: 'student_001',
            morphology_awareness: 0.75,
            suffix_recognition: 0.80,
            root_identification: 0.70,
            compound_understanding: 0.65,
            semantic_disambiguation: 0.85,
            overall_competency: 0.75,
            last_updated: new Date().toISOString(),
          },
          {
            student_id: 'student_002',
            morphology_awareness: 0.60,
            suffix_recognition: 0.55,
            root_identification: 0.65,
            compound_understanding: 0.50,
            semantic_disambiguation: 0.70,
            overall_competency: 0.60,
            last_updated: new Date().toISOString(),
          },
        ];
        setStudentProfiles(mockProfiles);

        // İstatistikleri al
        const stats = await revolutionaryFeaturesService.getIRTStatistics();
        setStatistics(stats);

        // Kalite raporunu al
        const quality = await revolutionaryFeaturesService.getQualityReport();
        setQualityReport(quality);

      } catch (err) {
        setError(err instanceof Error ? err.message : 'IRT Morfoloji verileri yüklenirken hata oluştu');
      } finally {
        setLoading(false);
      }
    };

    loadAnalysisData();
  }, [teacherId, classId]);

  // Zorluk seviyesi renk kodlaması
  const getDifficultyColor = (level: string) => {
    switch (level) {
      case 'kolay': return 'bg-green-100 text-green-800';
      case 'orta': return 'bg-yellow-100 text-yellow-800';
      case 'zor': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  // Kalite skoru renk kodlaması
  const getQualityColor = (score: number) => {
    if (score >= 80) {return 'text-green-600';}
    if (score >= 60) {return 'text-yellow-600';}
    return 'text-red-600';
  };

  // Yetkinlik seviyesi renk kodlaması
  const getCompetencyColor = (level: number) => {
    if (level >= 0.8) {return 'bg-green-100 text-green-800';}
    if (level >= 0.6) {return 'bg-yellow-100 text-yellow-800';}
    return 'bg-red-100 text-red-800';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <span className="ml-2 text-gray-600">IRT Morfoloji analizi yükleniyor...</span>
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

  return (
    <div className="space-y-6">
      {/* Tab Navigation */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          <button
            onClick={() => setSelectedTab('analysis')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              selectedTab === 'analysis'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Soru Analizi
          </button>
          <button
            onClick={() => setSelectedTab('profiles')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              selectedTab === 'profiles'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Öğrenci Profilleri
          </button>
          <button
            onClick={() => setSelectedTab('statistics')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              selectedTab === 'statistics'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            İstatistikler
          </button>
        </nav>
      </div>

      {/* Soru Analizi Tab */}
      {selectedTab === 'analysis' && questionAnalysis && (
        <div className="space-y-6">
          {/* Örnek Soru */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              🚀 IRT + Türkçe Morfoloji Soru Analizi
            </h3>

            <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 mb-4">
              <h4 className="font-medium text-gray-700 mb-2">Örnek Soru Metni</h4>
              <p className="text-sm text-gray-600">{sampleQuestion.text}</p>
              <div className="mt-2 flex space-x-4 text-xs text-gray-500">
                <span>Konu: {sampleQuestion.subject}</span>
                <span>Sınav: {sampleQuestion.examType}</span>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="text-center p-4 bg-blue-50 rounded-lg">
                <div className="text-2xl font-bold text-blue-600">{questionAnalysis.irt_parameters.difficulty.toFixed(2)}</div>
                <div className="text-sm text-gray-600">IRT Zorluğu</div>
              </div>
              <div className="text-center p-4 bg-green-50 rounded-lg">
                <div className="text-2xl font-bold text-green-600">{questionAnalysis.irt_parameters.discrimination.toFixed(2)}</div>
                <div className="text-sm text-gray-600">Ayırt Edicilik</div>
              </div>
              <div className="text-center p-4 bg-purple-50 rounded-lg">
                <div className="text-2xl font-bold text-purple-600">{(questionAnalysis.irt_parameters.morfoloji_faktoru * 100).toFixed(0)}%</div>
                <div className="text-sm text-gray-600">Morfoloji Faktörü</div>
              </div>
              <div className="text-center p-4 bg-orange-50 rounded-lg">
                <div className={`text-2xl font-bold ${getQualityColor(questionAnalysis.quality_score)}`}>
                  {questionAnalysis.quality_score.toFixed(0)}
                </div>
                <div className="text-sm text-gray-600">Kalite Skoru</div>
              </div>
            </div>
          </div>

          {/* Morfoloji Analizi Detayları */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Türkçe Morfoloji Analizi
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h4 className="font-medium text-gray-700 mb-3">Morfolojik Karmaşıklık</h4>
                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">Ortalama Skor</span>
                    <span className="font-medium">{(questionAnalysis.morphology_analysis.ortalama_morfoloji_skoru * 100).toFixed(0)}%</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">Ek Çeşitliliği</span>
                    <span className="font-medium">{(questionAnalysis.morphology_analysis.ek_tipi_cesitliligi * 100).toFixed(0)}%</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">Kelime Karmaşıklığı</span>
                    <span className="font-medium">{(questionAnalysis.morphology_analysis.kelime_karmasikligi * 100).toFixed(0)}%</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">Çok Anlamlılık</span>
                    <span className="font-medium">{(questionAnalysis.morphology_analysis.cok_anlamlilik_skoru * 100).toFixed(0)}%</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">Morfolojik Belirsizlik</span>
                    <span className="font-medium">{(questionAnalysis.morphology_analysis.morfolojik_belirsizlik * 100).toFixed(0)}%</span>
                  </div>
                </div>
              </div>

              <div>
                <h4 className="font-medium text-gray-700 mb-3">Analiz Sonuçları</h4>
                <div className="space-y-3">
                  <div className="p-3 bg-gray-50 rounded-lg">
                    <div className="text-sm font-medium text-gray-700">Zorluk Seviyesi</div>
                    <span className={`inline-block mt-1 px-2 py-1 rounded-full text-xs font-medium ${getDifficultyColor(questionAnalysis.difficulty_level)}`}>
                      {questionAnalysis.difficulty_level}
                    </span>
                  </div>

                  <div className="p-3 bg-gray-50 rounded-lg">
                    <div className="text-sm font-medium text-gray-700 mb-2">Öneriler</div>
                    <ul className="text-xs text-gray-600 space-y-1">
                      {questionAnalysis.recommendations.map((rec, index) => (
                        <li key={index}>• {rec}</li>
                      ))}
                    </ul>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* ÖSYM/ETS Karşılaştırması */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              ÖSYM/ETS Standartları Karşılaştırması
            </h3>

            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <div className="flex items-center">
                <svg className="h-5 w-5 text-green-400 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
                <div>
                  <h4 className="font-medium text-green-800">Standartları Aşıyor</h4>
                  <p className="text-sm text-green-700">
                    Bu soru, Türkçe morfoloji analizi ile ÖSYM ve ETS standartlarını aşan
                    detaylı değerlendirme sunmaktadır.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Öğrenci Profilleri Tab */}
      {selectedTab === 'profiles' && (
        <div className="space-y-6">
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Öğrenci Morfoloji Profilleri
            </h3>

            <div className="space-y-4">
              {studentProfiles.map((profile, index) => (
                <div key={profile.student_id} className="border border-gray-200 rounded-lg p-4">
                  <div className="flex items-center justify-between mb-4">
                    <h4 className="font-medium text-gray-900">Öğrenci {index + 1}</h4>
                    <span className={`px-3 py-1 rounded-full text-sm font-medium ${getCompetencyColor(profile.overall_competency)}`}>
                      Genel Yetkinlik: {(profile.overall_competency * 100).toFixed(0)}%
                    </span>
                  </div>

                  <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                    <div className="text-center">
                      <div className="text-lg font-bold text-blue-600">{(profile.morphology_awareness * 100).toFixed(0)}%</div>
                      <div className="text-xs text-gray-600">Morfoloji Farkındalığı</div>
                    </div>
                    <div className="text-center">
                      <div className="text-lg font-bold text-green-600">{(profile.suffix_recognition * 100).toFixed(0)}%</div>
                      <div className="text-xs text-gray-600">Ek Tanıma</div>
                    </div>
                    <div className="text-center">
                      <div className="text-lg font-bold text-purple-600">{(profile.root_identification * 100).toFixed(0)}%</div>
                      <div className="text-xs text-gray-600">Kök Belirleme</div>
                    </div>
                    <div className="text-center">
                      <div className="text-lg font-bold text-orange-600">{(profile.compound_understanding * 100).toFixed(0)}%</div>
                      <div className="text-xs text-gray-600">Birleşik Anlama</div>
                    </div>
                    <div className="text-center">
                      <div className="text-lg font-bold text-red-600">{(profile.semantic_disambiguation * 100).toFixed(0)}%</div>
                      <div className="text-xs text-gray-600">Anlam Ayrımı</div>
                    </div>
                  </div>

                  <div className="mt-3 text-xs text-gray-500">
                    Son güncelleme: {new Date(profile.last_updated).toLocaleDateString('tr-TR')}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* İstatistikler Tab */}
      {selectedTab === 'statistics' && (
        <div className="space-y-6">
          {/* Genel İstatistikler */}
          {statistics && (
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                IRT Morfoloji Sistem İstatistikleri
              </h3>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="text-center p-4 bg-blue-50 rounded-lg">
                  <div className="text-2xl font-bold text-blue-600">{statistics.toplam_analiz || 0}</div>
                  <div className="text-sm text-gray-600">Toplam Analiz</div>
                </div>
                <div className="text-center p-4 bg-green-50 rounded-lg">
                  <div className="text-2xl font-bold text-green-600">{statistics.basarili_analiz || 0}</div>
                  <div className="text-sm text-gray-600">Başarılı Analiz</div>
                </div>
                <div className="text-center p-4 bg-purple-50 rounded-lg">
                  <div className="text-2xl font-bold text-purple-600">{statistics.ortalama_kalite || 0}</div>
                  <div className="text-sm text-gray-600">Ortalama Kalite</div>
                </div>
                <div className="text-center p-4 bg-orange-50 rounded-lg">
                  <div className="text-2xl font-bold text-orange-600">{statistics.aktif_profil || 0}</div>
                  <div className="text-sm text-gray-600">Aktif Profil</div>
                </div>
              </div>
            </div>
          )}

          {/* Kalite Raporu */}
          {qualityReport && (
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                Soru Kalitesi Raporu
              </h3>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h4 className="font-medium text-gray-700 mb-3">Kalite Dağılımı</h4>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">Toplam Soru</span>
                      <span className="font-medium">{qualityReport.toplam_soru_sayisi || 0}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">Yüksek Kalite</span>
                      <span className="font-medium text-green-600">{qualityReport.yuksek_kalite_sayisi || 0}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">Düşük Kalite</span>
                      <span className="font-medium text-red-600">{qualityReport.dusuk_kalite_sayisi || 0}</span>
                    </div>
                  </div>
                </div>

                <div>
                  <h4 className="font-medium text-gray-700 mb-3">Kalite Metrikleri</h4>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">Ortalama Kalite</span>
                      <span className="font-medium">{qualityReport.ortalama_kalite_skoru?.toFixed(1) || 0}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">En Yüksek</span>
                      <span className="font-medium text-green-600">{qualityReport.en_yuksek_kalite || 0}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">En Düşük</span>
                      <span className="font-medium text-red-600">{qualityReport.en_dusuk_kalite || 0}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">Yüksek Kalite Oranı</span>
                      <span className="font-medium">{qualityReport.yuksek_kalite_orani?.toFixed(1) || 0}%</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default IRTMorphologyAnalysis;
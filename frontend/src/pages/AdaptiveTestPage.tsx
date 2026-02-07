/**
 * Adaptive Test Page - CAT (Computer Adaptive Testing)
 * Next-Gen feature: Real-time ability estimation with BanditCAT algorithm
 */
import * as React from 'react';
import {  useState, useEffect  } from 'react';
import { useParams, useNavigate } from 'react-router-dom';

import { apiClient } from '../services/apiClient';

interface CATSession {
  session_id: string;
  current_ability: number;
  current_sem: number;
  questions_answered: number;
  status: 'in_progress' | 'complete';
}

interface Question {
  id: string;
  metin: string;
  secenekler: Record<string, string>;
  dogru_cevap: string;
  konu: string;
  irt_params: {
    a: number;
    b: number;
    c: number;
  };
}

interface CATResults {
  final_ability: number;
  final_sem: number;
  confidence_interval: [number, number];
  questions_answered: number;
  performance_summary: {
    correct_answers: number;
    accuracy_rate: number;
    percentile_estimate: number;
  };
}

export const AdaptiveTestPage: React.FC = () => {
  const { konu } = useParams<{ konu: string }>();
  const navigate = useNavigate();

  const [session, setSession] = useState<CATSession | null>(null);
  const [currentQuestion, setCurrentQuestion] = useState<Question | null>(null);
  const [selectedAnswer, setSelectedAnswer] = useState<string>('');
  const [startTime, setStartTime] = useState<number>(0);
  const [isLoading, setIsLoading] = useState(false);
  const [results, setResults] = useState<CATResults | null>(null);

  // Start CAT session
  useEffect(() => {
    startSession();
  }, [konu]);

  const startSession = async () => {
    setIsLoading(true);
    try {
      const studentId = localStorage.getItem('userId') || 'demo-student';

      const response = await apiClient.post('/api/v2/cat/start', {
        student_id: studentId,
        konu: konu || 'Matematik',
        sinav_tipi: 'TYT',
      });

      setSession({
        session_id: response.data.session_id,
        current_ability: response.data.initial_ability,
        current_sem: 1.0,
        questions_answered: 0,
        status: 'in_progress',
      });

      setCurrentQuestion(response.data.first_question);
      setStartTime(Date.now());
    } catch (error) {
      console.error('Session start failed:', error);
      alert('Test başlatılamadı. Lütfen tekrar deneyin.');
    } finally {
      setIsLoading(false);
    }
  };

  const submitAnswer = async () => {
    if (!selectedAnswer || !session || !currentQuestion) {return;}

    setIsLoading(true);
    const responseTime = Math.floor((Date.now() - startTime) / 1000);

    try {
      const response = await apiClient.post('/api/v2/cat/submit', {
        session_id: session.session_id,
        question_id: currentQuestion.id,
        is_correct: selectedAnswer === currentQuestion.dogru_cevap,
        response_time_seconds: responseTime,
      });

      if (response.data.status === 'complete') {
        // Test completed
        setResults(response.data.final_results);
        setSession({ ...session, status: 'complete' });
      } else {
        // Update session and get next question
        setSession({
          session_id: session.session_id,
          current_ability: response.data.current_ability,
          current_sem: response.data.current_sem,
          questions_answered: response.data.questions_answered,
          status: 'in_progress',
        });

        setCurrentQuestion(response.data.next_question);
        setSelectedAnswer('');
        setStartTime(Date.now());
      }
    } catch (error) {
      console.error('Submit failed:', error);
      alert('Cevap gönderilemedi. Lütfen tekrar deneyin.');
    } finally {
      setIsLoading(false);
    }
  };

  const getAbilityLabel = (theta: number): string => {
    if (theta < -1) {return 'Temel Seviye';}
    if (theta < 0) {return 'Orta-Alt Seviye';}
    if (theta < 1) {return 'Orta-Üst Seviye';}
    return 'İleri Seviye';
  };

  if (isLoading && !currentQuestion) {
    return <div className="loading">Test yükleniyor...</div>;
  }

  if (results) {
    return (
      <div className="cat-results">
        <h1>Test Tamamlandı!</h1>

        <div className="ability-card">
          <h2>Yetenek Tahmini (θ)</h2>
          <div className="ability-value">{results.final_ability.toFixed(2)}</div>
          <div className="ability-label">{getAbilityLabel(results.final_ability)}</div>
          <div className="confidence-interval">
            Güven Aralığı: [{results.confidence_interval[0].toFixed(2)}, {results.confidence_interval[1].toFixed(2)}]
          </div>
        </div>

        <div className="performance-stats">
          <h2>Performans Özeti</h2>
          <div className="stat">
            <span>Cevaplanan Soru:</span>
            <strong>{results.questions_answered}</strong>
          </div>
          <div className="stat">
            <span>Doğru Sayısı:</span>
            <strong>{results.performance_summary.correct_answers}</strong>
          </div>
          <div className="stat">
            <span>Başarı Oranı:</span>
            <strong>{(results.performance_summary.accuracy_rate * 100).toFixed(1)}%</strong>
          </div>
          <div className="stat">
            <span>Yüzdelik Dilim:</span>
            <strong>{results.performance_summary.percentile_estimate.toFixed(0)}. yüzdelik</strong>
          </div>
        </div>

        <button onClick={() => navigate('/dashboard')}>
          Dashboard&apos;a Dön
        </button>
      </div>
    );
  }

  return (
    <div className="adaptive-test-page">
      {/* Header with progress */}
      <div className="test-header">
        <h1>Adaptif Test - {konu}</h1>
        {session && (
          <div className="progress-bar">
            <div className="progress-info">
              <span>Soru: {session.questions_answered}</span>
              <span>Yetenek: {session.current_ability.toFixed(2)}</span>
              <span>Kesinlik: {(1 / session.current_sem).toFixed(1)}</span>
            </div>
            {/* Ability meter */}
            <div className="ability-meter">
              <div
                className="ability-indicator"
                style={{
                  left: `${((session.current_ability + 3) / 6) * 100}%`,
                }}
              />
              <div className="meter-labels">
                <span>-3</span>
                <span>0</span>
                <span>+3</span>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Question display */}
      {currentQuestion && (
        <div className="question-card">
          <div className="question-number">
            Soru {session?.questions_answered ? session.questions_answered + 1 : 1}
          </div>

          <div className="question-text">
            {currentQuestion.metin}
          </div>

          <div className="answer-options">
            {Object.entries(currentQuestion.secenekler).map(([key, value]) => (
              <button
                key={key}
                className={`option-button ${selectedAnswer === key ? 'selected' : ''}`}
                onClick={() => setSelectedAnswer(key)}
                disabled={isLoading}
              >
                <span className="option-key">{key})</span>
                <span className="option-text">{value}</span>
              </button>
            ))}
          </div>

          <button
            className="submit-button"
            onClick={submitAnswer}
            disabled={!selectedAnswer || isLoading}
          >
            {isLoading ? 'Gönderiliyor...' : 'Cevabı Gönder'}
          </button>
        </div>
      )}

      <style>{`
        .adaptive-test-page {
          max-width: 800px;
          margin: 0 auto;
          padding: 20px;
        }

        .test-header {
          background: white;
          padding: 20px;
          border-radius: 8px;
          margin-bottom: 20px;
          box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }

        .ability-meter {
          position: relative;
          height: 40px;
          background: linear-gradient(to right, #ef4444, #f59e0b, #10b981);
          border-radius: 20px;
          margin: 10px 0;
        }

        .ability-indicator {
          position: absolute;
          width: 4px;
          height: 100%;
          background: white;
          box-shadow: 0 0 10px rgba(0,0,0,0.3);
          transition: left 0.5s ease;
        }

        .question-card {
          background: white;
          padding: 30px;
          border-radius: 8px;
          box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }

        .option-button {
          width: 100%;
          padding: 15px;
          margin: 10px 0;
          border: 2px solid #e5e7eb;
          border-radius: 8px;
          background: white;
          cursor: pointer;
          transition: all 0.2s;
          text-align: left;
        }

        .option-button:hover {
          border-color: #3b82f6;
          background: #eff6ff;
        }

        .option-button.selected {
          border-color: #3b82f6;
          background: #dbeafe;
        }

        .submit-button {
          width: 100%;
          padding: 15px;
          margin-top: 20px;
          background: #3b82f6;
          color: white;
          border: none;
          border-radius: 8px;
          font-size: 16px;
          font-weight: bold;
          cursor: pointer;
        }

        .submit-button:disabled {
          background: #9ca3af;
          cursor: not-allowed;
        }

        .cat-results {
          max-width: 600px;
          margin: 0 auto;
          padding: 20px;
        }

        .ability-card {
          background: white;
          padding: 30px;
          border-radius: 8px;
          text-align: center;
          margin: 20px 0;
          box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }

        .ability-value {
          font-size: 72px;
          font-weight: bold;
          color: #3b82f6;
          margin: 20px 0;
        }
      `}</style>
    </div>
  );
};

export default AdaptiveTestPage;

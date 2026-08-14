import React, { useState, useEffect } from 'react';
import styles from './ExamSession.module.css';
import { BookmarkBorder, Bookmark, ChevronLeft, ChevronRight } from '@mui/icons-material';
import mockExamService, { ExamQuestionData, ExamSubmitResult } from '../../services/mockExamService';
import { ExamResultDashboard } from './ExamResultDashboard';

interface Question {
  id: string;
  order: number;
  text: string;
  options: { letter: string; text: string }[];
  branch: string;
}

const MOCK_FALLBACK_QUESTIONS: Question[] = Array.from({ length: 120 }, (_, i) => {
  let branch = "TUR";
  if (i >= 40 && i < 60) branch = "SOS";
  else if (i >= 60 && i < 100) branch = "MAT";
  else if (i >= 100) branch = "FEN";

  return {
    id: `q-${i + 1}`,
    order: i + 1,
    text: `Bu örnek bir ${branch} sorusudur (Soru ${i + 1}). Aşağıdakilerden hangisi doğrudur?`,
    options: [
      { letter: 'A', text: 'Örnek Seçenek A' },
      { letter: 'B', text: 'Örnek Seçenek B' },
      { letter: 'C', text: 'Örnek Seçenek C' },
      { letter: 'D', text: 'Örnek Seçenek D' },
      { letter: 'E', text: 'Örnek Seçenek E' },
    ],
    branch,
  };
});

const BRANCHES = [
  { id: 'TUR', name: 'TÜRKÇE', range: [1, 40] },
  { id: 'SOS', name: 'SOSYAL BİL.', range: [41, 60] },
  { id: 'MAT', name: 'MATEMATİK', range: [61, 100] },
  { id: 'FEN', name: 'FEN BİL.', range: [101, 120] },
];

interface ExamSessionProps {
  sessionId?: string;
  studentId?: string;
}

export const ExamSession: React.FC<ExamSessionProps> = ({ sessionId: initialSessionId, studentId = "student-123" }) => {
  const [sessionId, setSessionId] = useState<string | undefined>(initialSessionId);
  const [questions, setQuestions] = useState<Question[]>(MOCK_FALLBACK_QUESTIONS);
  const [activeBranch, setActiveBranch] = useState('TUR');
  const [currentQuestionOrder, setCurrentQuestionOrder] = useState(1);
  const [answers, setAnswers] = useState<Record<number, string>>({});
  const [marked, setMarked] = useState<Record<number, boolean>>({});
  const [timeLeft, setTimeLeft] = useState(165 * 60);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isCompleted, setIsCompleted] = useState(false);
  const [results, setResults] = useState<ExamSubmitResult | null>(null);

  // Load or generate exam session
  useEffect(() => {
    let isMounted = true;
    const initExam = async () => {
      try {
        let activeId = sessionId;
        if (!activeId) {
          const res = await mockExamService.generateMockExam(studentId);
          activeId = res.exam_session_id;
          if (isMounted) setSessionId(activeId);
        }
        if (activeId) {
          const sessionData = await mockExamService.getExamSession(activeId);
          if (isMounted && sessionData.questions && sessionData.questions.length > 0) {
            const mappedQuestions: Question[] = sessionData.questions.map((q: ExamQuestionData) => ({
              id: q.id,
              order: q.order,
              text: q.text,
              options: q.options,
              branch: q.branch
            }));
            setQuestions(mappedQuestions);

            const initialAns: Record<number, string> = {};
            sessionData.questions.forEach((q: ExamQuestionData) => {
              if (q.selected_answer) {
                initialAns[q.order] = q.selected_answer;
              }
            });
            setAnswers(initialAns);
          }
        }
      } catch (err) {
        console.warn('Failed to load live backend session, falling back to local questions state.', err);
      }
    };
    initExam();
    return () => { isMounted = false; };
  }, [initialSessionId, studentId]);

  // Timer effect
  useEffect(() => {
    if (isCompleted) return;
    const timer = setInterval(() => {
      setTimeLeft((prev) => (prev > 0 ? prev - 1 : 0));
    }, 1000);
    return () => clearInterval(timer);
  }, [isCompleted]);

  const formatTime = (seconds: number) => {
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = seconds % 60;
    return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  };

  const handleSelectOption = async (letter: string) => {
    setAnswers((prev) => ({ ...prev, [currentQuestionOrder]: letter }));
    const curQ = questions.find((q) => q.order === currentQuestionOrder);
    if (sessionId && curQ && curQ.id && !curQ.id.startsWith('q-') && !curQ.id.startsWith('dummy-')) {
      try {
        await mockExamService.saveExamAnswer(sessionId, curQ.id, letter, 5.0);
      } catch (e) {
        console.warn('Failed sync answer to server', e);
      }
    }
  };

  const handleToggleMark = () => {
    setMarked((prev) => ({ ...prev, [currentQuestionOrder]: !prev[currentQuestionOrder] }));
  };

  const handleFinishExam = async () => {
    if (isSubmitting) return;
    setIsSubmitting(true);
    const timeSpent = (165 * 60) - timeLeft;

    if (sessionId && !sessionId.startsWith('dummy')) {
      try {
        const res = await mockExamService.submitExam(sessionId, timeSpent);
        setResults(res);
      } catch (e) {
        console.warn('Failed submit exam to backend, calculating client-side fallback result', e);
      }
    }
    setIsCompleted(true);
    setIsSubmitting(false);
  };

  const currentQuestion = questions.find((q) => q.order === currentQuestionOrder) || MOCK_FALLBACK_QUESTIONS[0];

  // Auto-switch branch tab based on current question
  useEffect(() => {
    if (currentQuestionOrder >= 1 && currentQuestionOrder <= 40) setActiveBranch('TUR');
    else if (currentQuestionOrder >= 41 && currentQuestionOrder <= 60) setActiveBranch('SOS');
    else if (currentQuestionOrder >= 61 && currentQuestionOrder <= 100) setActiveBranch('MAT');
    else if (currentQuestionOrder >= 101 && currentQuestionOrder <= 120) setActiveBranch('FEN');
  }, [currentQuestionOrder]);

  const activeBranchObj = BRANCHES.find((b) => b.id === activeBranch) || BRANCHES[0];
  const activeBranchQuestions = Array.from(
    { length: activeBranchObj.range[1] - activeBranchObj.range[0] + 1 },
    (_, i) => i + activeBranchObj.range[0]
  );

  if (isCompleted) {
    return <ExamResultDashboard results={results} onRestart={() => window.location.reload()} />;
  }

  return (
    <div className={styles.container}>
      {/* Sidebar for Navigation */}
      <aside className={styles.sidebar}>
        <div className={styles.sidebarHeader}>
          <h1 className={styles.sidebarTitle}>KIRO2 MOCK</h1>
          <div className={styles.timer}>{formatTime(timeLeft)}</div>
        </div>

        <div className={styles.branchTabs}>
          {BRANCHES.map((b) => (
            <button
              key={b.id}
              className={`${styles.branchTab} ${activeBranch === b.id ? styles.branchTabActive : ''}`}
              onClick={() => {
                setActiveBranch(b.id);
                setCurrentQuestionOrder(b.range[0]);
              }}
            >
              {b.name}
            </button>
          ))}
        </div>

        <div className={styles.questionGrid}>
          {activeBranchQuestions.map((num) => {
            const isAnswered = !!answers[num];
            const isMarked = !!marked[num];
            const isActive = currentQuestionOrder === num;

            return (
              <button
                key={num}
                onClick={() => setCurrentQuestionOrder(num)}
                className={`
                  ${styles.qBtn}
                  ${isActive ? styles.qBtnActive : ''}
                  ${isAnswered && !isActive ? styles.qBtnAnswered : ''}
                  ${isMarked && !isActive ? styles.qBtnMarked : ''}
                `}
              >
                {num}
              </button>
            );
          })}
        </div>
      </aside>

      {/* Main Content Area */}
      <main className={styles.main}>
        <header className={styles.header}>
          <div className={styles.questionInfo}>
            {activeBranchObj.name} - Soru {currentQuestionOrder}
          </div>
          <button className={styles.finishBtn} onClick={handleFinishExam} disabled={isSubmitting}>
            {isSubmitting ? 'Hesaplanıyor...' : 'Sınavı Bitir'}
          </button>
        </header>

        <div className={styles.content}>
          <div className={styles.questionCard}>
            <div className={styles.questionText}>
              {currentQuestion.text}
            </div>

            <div className={styles.optionsList}>
              {currentQuestion.options.map((opt) => {
                const isSelected = answers[currentQuestionOrder] === opt.letter;
                return (
                  <div
                    key={opt.letter}
                    className={`${styles.option} ${isSelected ? styles.optionSelected : ''}`}
                    onClick={() => handleSelectOption(opt.letter)}
                  >
                    <div className={styles.optionLetter}>{opt.letter}</div>
                    <div className={styles.optionText}>{opt.text}</div>
                  </div>
                );
              })}
            </div>
          </div>

          <div className={styles.controls}>
            <button
              className={styles.navBtn}
              disabled={currentQuestionOrder === 1}
              onClick={() => setCurrentQuestionOrder(prev => prev - 1)}
            >
              <ChevronLeft style={{ verticalAlign: 'middle', marginRight: 4 }} /> Önceki
            </button>

            <button className={styles.markBtn} onClick={handleToggleMark}>
              {marked[currentQuestionOrder] ? <Bookmark /> : <BookmarkBorder />}
              İşaretle
            </button>

            <button
              className={styles.navBtn}
              disabled={currentQuestionOrder === 120}
              onClick={() => setCurrentQuestionOrder(prev => prev + 1)}
            >
              Sonraki <ChevronRight style={{ verticalAlign: 'middle', marginLeft: 4 }} />
            </button>
          </div>
        </div>
      </main>
    </div>
  );
};

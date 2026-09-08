// SS10.72: `import React from 'react'` (import/default) ve
// `import mockExamService from ...` (import/no-named-as-default) eslint
// kurallarini ihlal ediyordu. Adlandirilmis ithal ikisini de cozuyor;
// `React.FC` yerine props tipi dogrudan yaziliyor.
import { useState, useEffect } from 'react';
import { BookmarkBorder, Bookmark, ChevronLeft, ChevronRight } from '@mui/icons-material';
import { mockExamService, ExamQuestionData, ExamSubmitResult } from '../../services/mockExamService';
import styles from './ExamSession.module.css';
import { ExamResultDashboard } from './ExamResultDashboard';

interface Question {
  id: string;
  order: number;
  text: string;
  options: { letter: string; text: string }[];
  branch: string;
}

/**
 * SS10.72 -- 120 SORULUK UYDURMA "FALLBACK" HAVUZU KALDIRILDI.
 *
 * Burada `MOCK_FALLBACK_QUESTIONS` adinda, metni
 * "Bu örnek bir TUR sorusudur (Soru 1). Aşağıdakilerden hangisi doğrudur?"
 * olan 120 uydurma soru vardi ve bunlar bilesenin BASLANGIC DURUMUYDU:
 *
 *     const [questions, setQuestions] = useState<Question[]>(MOCK_FALLBACK_QUESTIONS);
 *
 * Arka uc cagrisi duserse `catch` yalnizca `console.warn(... falling back to
 * local questions state)` diyordu. Yani ogrenci, hicbir uyari gormeden
 * 120 SAHTE SORULUK BIR DENEME SINAVI cozuyordu -- cevaplari hicbir yere
 * yazilmiyor, neti anlamsiz.
 *
 * Bu, deponun kendi test dosyasinda da iz birakmis: ExamSession.test.tsx
 * yorumu "component'in kendi 120 soruluk fallback'i 'Örnek Seçenek A'
 * dondurdugu icin test yanlis modulu mock'ladigini fark edemiyordu" diyor --
 * yani sahte havuz gercek bir kusuru ORTMUSTU.
 *
 * Dogru davranis: veri yoksa sinav BASLAMAZ. Asagida yukleme/hata durumlari
 * acikca gosteriliyor.
 */

const BRANCHES = [
  { id: 'TUR', name: 'TÜRKÇE', range: [1, 40] },
  { id: 'SOS', name: 'SOSYAL BİL.', range: [41, 60] },
  { id: 'MAT', name: 'MATEMATİK', range: [61, 100] },
  { id: 'FEN', name: 'FEN BİL.', range: [101, 120] },
];

interface ExamSessionProps {
  sessionId?: string;
  /**
   * SS10.72: eskiden `studentId = "student-123"` diye SABIT bir varsayilani
   * vardi. Bilesen bir rotaya baglandiginda prop verilmezse HER ogrenci
   * "student-123" adina sinav uretirdi. Varsayilan kaldirildi: cagiran taraf
   * gercek ogrenci kimligini vermek ZORUNDA.
   */
  studentId: string;
}

export const ExamSession = ({ sessionId: initialSessionId, studentId }: ExamSessionProps) => {
  const [sessionId, setSessionId] = useState<string | undefined>(initialSessionId);
  const [questions, setQuestions] = useState<Question[]>([]);
  const [yukleniyor, setYukleniyor] = useState(true);
  const [yuklemeHatasi, setYuklemeHatasi] = useState<string | null>(null);
  const [gonderimHatasi, setGonderimHatasi] = useState<string | null>(null);
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
          if (isMounted) {setSessionId(activeId);}
        }
        if (activeId) {
          const sessionData = await mockExamService.getExamSession(activeId);
          if (isMounted && sessionData.questions && sessionData.questions.length > 0) {
            const mappedQuestions: Question[] = sessionData.questions.map((q: ExamQuestionData) => ({
              id: q.id,
              order: q.order,
              text: q.text,
              options: q.options,
              branch: q.branch,
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
        // SS10.72: eskiden burasi yalnizca console.warn edip 120 uydurma
        // soruyla devam ediyordu. Artik hata GORUNUR: sinav baslamaz.
        console.error('Deneme sinavi oturumu yuklenemedi.', err);
        if (isMounted) {
          setYuklemeHatasi(
            'Deneme sinavi yuklenemedi. Lutfen baglantinizi kontrol edip tekrar deneyin.',
          );
        }
      } finally {
        if (isMounted) {setYukleniyor(false);}
      }
    };
    initExam();
    return () => { isMounted = false; };
    // SS10.72: `sessionId` BILEREK bagimlilik listesinde degil. Bu efekt
    // oturum kimligi yoksa YENI oturum uretip `setSessionId` cagiriyor;
    // `sessionId`i listeye eklemek efekti yeniden tetikler ve her turda bir
    // sinav daha uretir. Giris noktasi `initialSessionId` prop'udur.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initialSessionId, studentId]);

  // Timer effect
  useEffect(() => {
    if (isCompleted) {return;}
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
    if (isSubmitting) {return;}
    setIsSubmitting(true);
    const timeSpent = (165 * 60) - timeLeft;

    if (sessionId && !sessionId.startsWith('dummy')) {
      try {
        const res = await mockExamService.submitExam(sessionId, timeSpent);
        setResults(res);
        setGonderimHatasi(null);
        setIsCompleted(true);
      } catch (e) {
        // SS10.72: eskiden burasi console.warn edip YINE DE isCompleted=true
        // yapiyordu; ogrenci `results === null` ile sonuc ekranina dusuyor,
        // sinavi gonderilmemis oldugu halde "bitti" saniyordu.
        // "client-side fallback result" diye bir hesap ZATEN YOKTU -- yorum
        // var olmayan bir davranisi anlatiyordu.
        console.error('Deneme sinavi gonderilemedi.', e);
        setGonderimHatasi(
          'Sinav gonderilemedi. Cevaplariniz kaydedildi; lutfen tekrar deneyin.',
        );
      }
    } else {
      // Oturum kimligi yoksa gonderilecek bir sey de yok.
      setGonderimHatasi('Aktif bir sinav oturumu yok; gonderim yapilamadi.');
    }
    setIsSubmitting(false);
  };

  const currentQuestion = questions.find((q) => q.order === currentQuestionOrder);

  // Auto-switch branch tab based on current question
  useEffect(() => {
    if (currentQuestionOrder >= 1 && currentQuestionOrder <= 40) {setActiveBranch('TUR');}
    else if (currentQuestionOrder >= 41 && currentQuestionOrder <= 60) {setActiveBranch('SOS');}
    else if (currentQuestionOrder >= 61 && currentQuestionOrder <= 100) {setActiveBranch('MAT');}
    else if (currentQuestionOrder >= 101 && currentQuestionOrder <= 120) {setActiveBranch('FEN');}
  }, [currentQuestionOrder]);

  const activeBranchObj = BRANCHES.find((b) => b.id === activeBranch) || BRANCHES[0];
  const activeBranchQuestions = Array.from(
    { length: activeBranchObj.range[1] - activeBranchObj.range[0] + 1 },
    (_, i) => i + activeBranchObj.range[0],
  );

  if (isCompleted) {
    return <ExamResultDashboard results={results} onRestart={() => window.location.reload()} />;
  }

  // SS10.72: veri yoksa sinav BASLAMAZ. Eskiden bu dallarin yerine 120
  // uydurma soru gosteriliyordu.
  if (yukleniyor) {
    return (
      <div className={styles.container} role="status">
        Deneme sinavi hazirlaniyor...
      </div>
    );
  }

  if (yuklemeHatasi || !currentQuestion) {
    return (
      <div className={styles.container} role="alert">
        {yuklemeHatasi ?? 'Deneme sinavi sorulari yuklenemedi.'}
      </div>
    );
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

        {/* SS10.72: gonderim hatasi artik SESSIZ degil. Eskiden hata yutulup
            sonuc ekranina bos `results` ile geciliyordu. */}
        {gonderimHatasi && (
          <div role="alert" className={styles.header}>
            {gonderimHatasi}
          </div>
        )}

        <div className={styles.content}>
          <div className={styles.questionCard}>
            <div className={styles.questionText}>
              {currentQuestion.text}
            </div>

            <div className={styles.optionsList}>
              {currentQuestion.options.map((opt) => {
                const isSelected = answers[currentQuestionOrder] === opt.letter;
                return (
                  // SS10.72: <div onClick> yerine gercek <button>.
                  // Sik secmek klavyeyle de yapilabilmeli; jsx-a11y
                  // (click-events-have-key-events / no-static-element-interactions)
                  // bunu hakli olarak isaretliyordu.
                  <button
                    key={opt.letter}
                    type="button"
                    aria-pressed={isSelected}
                    className={`${styles.option} ${isSelected ? styles.optionSelected : ''}`}
                    onClick={() => handleSelectOption(opt.letter)}
                  >
                    <div className={styles.optionLetter}>{opt.letter}</div>
                    <div className={styles.optionText}>{opt.text}</div>
                  </button>
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

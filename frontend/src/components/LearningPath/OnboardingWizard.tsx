/**
 * OnboardingWizard — 4 adımlı AI-guided onboarding
 *
 * Adım 1: Hedef Belirleme (sınav, dersler, süre, günlük çalışma)
 * Adım 2: Bilgi Değerlendirmesi (tanısal test VEYA öz değerlendirme)
 * Adım 3: Öğrenme Tercihleri (video/metin/etkileşimli + VARK mapping)
 * Adım 4: AI Yol Üretimi (loading + reasoning gösterimi)
 */

import { useState, useCallback } from 'react';
import {
  Box,
  Typography,
  Stepper,
  Step,
  StepLabel,
  Slider,
  Chip,
  RadioGroup,
  FormControlLabel,
  Radio,
  Fade,
} from '@mui/material';
import {
  School,
  Quiz,
  VideoLibrary,
  MenuBook,
  SportsEsports,
  Shuffle,
  ArrowForward,
  ArrowBack,
  CheckCircle,
  AutoAwesome,
  EditNote,
} from '@mui/icons-material';
import { GlassCard } from '../ui/GlassCard';
import { ModernButton } from '../ui/ModernButton';
import { ModernLoader } from '../ui/ModernLoader';
import modernColors from '../../theme/modern-colors';
import { QuizInterface } from '../Quiz/QuizInterface';
import type { Question } from '../Quiz/QuizInterface';
import { mapApiToQuizQuestion } from '../../utils/questionMappers';

// ─── Types ───

export interface OnboardingResult {
  examType: string;
  subjects: string[];
  durationMonths: number;
  availableTime: number;
  knowledgeLevel: string;
  learningPreference: string;
  /** VARK-compatible responses for backend */
  varkResponses: Record<string, string>;
  completionTime: number;
}

interface OnboardingWizardProps {
  studentId: string;
  onComplete: (result: OnboardingResult) => void;
  onSkip?: () => void;
}

// ─── Constants ───

const STEPS = ['Hedefler', 'Seviye', 'Tercihler', 'Yol Oluştur'];

const EXAM_TYPES = [
  { value: 'YKS-TYT', label: 'TYT (Temel Yeterlilik)' },
  { value: 'YKS-AYT-SAY', label: 'AYT Sayısal' },
  { value: 'YKS-AYT-SOZ', label: 'AYT Sözel' },
  { value: 'YKS-AYT-EA', label: 'AYT Eşit Ağırlık' },
];

const SUBJECTS = [
  { value: 'matematik', label: 'Matematik' },
  { value: 'fizik', label: 'Fizik' },
  { value: 'kimya', label: 'Kimya' },
  { value: 'biyoloji', label: 'Biyoloji' },
  { value: 'turkce', label: 'Türkçe' },
  { value: 'tarih', label: 'Tarih' },
  { value: 'cografya', label: 'Coğrafya' },
  { value: 'edebiyat', label: 'Edebiyat' },
  { value: 'geometri', label: 'Geometri' },
];

const KNOWLEDGE_LEVELS = [
  { value: 'beginner', label: 'Başlangıç', description: 'Temel kavramlar yeni' },
  { value: 'elementary', label: 'Temel', description: 'Bazı konular tanıdık' },
  { value: 'intermediate', label: 'Orta', description: 'Çoğu konuyu biliyorum' },
  { value: 'advanced', label: 'İleri', description: 'Güçlü altyapım var' },
  { value: 'expert', label: 'Uzman', description: 'Neredeyse her konuya hakimim' },
];

const LEARNING_PREFERENCES = [
  { value: 'visual', label: 'Video', icon: VideoLibrary, color: '#2196F3', vark: 'visual' },
  { value: 'reading', label: 'Metin', icon: MenuBook, color: '#4CAF50', vark: 'reading' },
  { value: 'kinesthetic', label: 'Etkileşimli', icon: SportsEsports, color: '#9C27B0', vark: 'kinesthetic' },
  { value: 'mixed', label: 'Karma', icon: Shuffle, color: '#FF9800', vark: 'mixed' },
];

// ─── Component ───

export function OnboardingWizard({ studentId: _studentId, onComplete, onSkip }: OnboardingWizardProps) {
  const [activeStep, setActiveStep] = useState(0);
  const [startTime] = useState(Date.now());

  // Step 1: Goals
  const [examType, setExamType] = useState('YKS-TYT');
  const [selectedSubjects, setSelectedSubjects] = useState<string[]>(['matematik']);
  const [durationMonths, setDurationMonths] = useState(3);
  const [availableTime, setAvailableTime] = useState(90);

  // Step 2: Assessment
  const [assessmentMode, setAssessmentMode] = useState<'self' | 'quiz' | null>(null);
  const [knowledgeLevel, setKnowledgeLevel] = useState('intermediate');
  const [diagnosticQuestions, setDiagnosticQuestions] = useState<Question[] | null>(null);
  const [diagnosticDone, setDiagnosticDone] = useState(false);

  // Step 3: Preferences
  const [learningPreference, setLearningPreference] = useState('mixed');

  // Step 4: Generating
  const [isGenerating, setIsGenerating] = useState(false);

  // ─── Navigation ───

  const canProceed = useCallback(() => {
    switch (activeStep) {
      case 0: return examType && selectedSubjects.length > 0;
      case 1: return assessmentMode === 'self' || diagnosticDone;
      case 2: return !!learningPreference;
      default: return true;
    }
  }, [activeStep, examType, selectedSubjects, assessmentMode, diagnosticDone, learningPreference]);

  const handleNext = useCallback(() => {
    if (activeStep === STEPS.length - 1) {
      // Final step — trigger generation
      setIsGenerating(true);

      // Build VARK responses from preference selection
      const varkResponses: Record<string, string> = {};
      const pref = learningPreference === 'mixed' ? 'visual' : learningPreference;
      for (let i = 1; i <= 5; i++) {
        varkResponses[`q${i}`] = pref;
      }

      const result: OnboardingResult = {
        examType,
        subjects: selectedSubjects,
        durationMonths,
        availableTime,
        knowledgeLevel,
        learningPreference,
        varkResponses,
        completionTime: Math.round((Date.now() - startTime) / 1000),
      };

      onComplete(result);
      return;
    }
    setActiveStep(prev => prev + 1);
  }, [activeStep, examType, selectedSubjects, durationMonths, availableTime, knowledgeLevel, learningPreference, startTime, onComplete]);

  const handleBack = useCallback(() => {
    setActiveStep(prev => Math.max(0, prev - 1));
  }, []);

  // ─── Subject toggle ───

  const toggleSubject = useCallback((subject: string) => {
    setSelectedSubjects(prev =>
      prev.includes(subject) ? prev.filter(s => s !== subject) : [...prev, subject],
    );
  }, []);

  // ─── Diagnostic quiz ───

  const startDiagnostic = useCallback(async () => {
    setAssessmentMode('quiz');
    try {
      const subject = selectedSubjects[0] || 'matematik';
      const res = await fetch(
        `/api/learning-path/exit-quiz/${encodeURIComponent(subject)}?count=10`,
        { credentials: 'include' },
      );
      const data = await res.json();
      if (data.success && data.questions?.length > 0) {
        setDiagnosticQuestions(data.questions.map(mapApiToQuizQuestion));
      } else {
        // Fallback: no questions available, use self-assessment
        setAssessmentMode('self');
      }
    } catch {
      setAssessmentMode('self');
    }
  }, [selectedSubjects]);

  const handleDiagnosticComplete = useCallback((results: { percentage: number }) => {
    // Map percentage to knowledge level
    if (results.percentage >= 90) setKnowledgeLevel('expert');
    else if (results.percentage >= 70) setKnowledgeLevel('advanced');
    else if (results.percentage >= 50) setKnowledgeLevel('intermediate');
    else if (results.percentage >= 30) setKnowledgeLevel('elementary');
    else setKnowledgeLevel('beginner');

    setDiagnosticDone(true);
    setDiagnosticQuestions(null);
  }, []);

  // ─── Step 4: Generating state ───

  if (isGenerating) {
    return (
      <GlassCard glassIntensity="medium" elevated>
        <Box sx={{ textAlign: 'center', py: 6 }}>
          <ModernLoader message="AI öğrenme yolunuzu oluşturuyor..." size="large" />
          <Typography variant="body2" color="text.secondary" sx={{ mt: 3 }}>
            Hedefleriniz, bilgi düzeyiniz ve tercihleriniz analiz ediliyor...
          </Typography>
        </Box>
      </GlassCard>
    );
  }

  // ─── Diagnostic quiz overlay ───

  if (diagnosticQuestions) {
    const subjectLabel = selectedSubjects[0]?.charAt(0).toUpperCase() + (selectedSubjects[0]?.slice(1) || '');
    return (
      <GlassCard glassIntensity="medium" elevated>
        <Typography variant="h6" sx={{ fontWeight: 700, mb: 2, textAlign: 'center' }}>
          Hızlı Seviye Testi
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 3, textAlign: 'center' }}>
          {subjectLabel} — 10 soru
        </Typography>
        <QuizInterface
          config={{
            title: `${subjectLabel} Seviye Testi`,
            description: 'Bilgi düzeyinizi belirlemek için 10 soru',
            questions: diagnosticQuestions,
            passingScore: 50,
            showCorrectAnswers: true,
            immediateFeedback: true,
          }}
          onSubmit={handleDiagnosticComplete}
          onExit={() => {
            setDiagnosticQuestions(null);
            setAssessmentMode(null);
          }}
        />
      </GlassCard>
    );
  }

  // ─── Main wizard ───

  return (
    <GlassCard glassIntensity="medium" elevated sx={{ maxWidth: 640, mx: 'auto' }}>
      <Box sx={{ mb: 4 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 2 }}>
          <AutoAwesome sx={{ color: '#6366f1', fontSize: 28 }} />
          <Typography variant="h5" sx={{ fontWeight: 800 }}>
            Öğrenme Yolunuzu Oluşturalım
          </Typography>
        </Box>
        <Stepper activeStep={activeStep} alternativeLabel sx={{ mb: 3 }}>
          {STEPS.map((label) => (
            <Step key={label}>
              <StepLabel>{label}</StepLabel>
            </Step>
          ))}
        </Stepper>
      </Box>

      <Fade in key={activeStep}>
        <Box sx={{ minHeight: 280 }}>
          {/* ── Step 1: Hedef Belirleme ── */}
          {activeStep === 0 && (
            <Box>
              <Typography variant="subtitle1" sx={{ fontWeight: 700, mb: 2 }}>
                Hangi sınava hazırlanıyorsunuz?
              </Typography>
              <RadioGroup value={examType} onChange={(e) => setExamType(e.target.value)}>
                {EXAM_TYPES.map((exam) => (
                  <FormControlLabel
                    key={exam.value}
                    value={exam.value}
                    control={<Radio />}
                    label={exam.label}
                    sx={{
                      mb: 0.5, p: 1, borderRadius: 2,
                      border: '1px solid',
                      borderColor: examType === exam.value ? '#6366f1' : 'divider',
                      backgroundColor: examType === exam.value ? '#6366f110' : 'transparent',
                    }}
                  />
                ))}
              </RadioGroup>

              <Typography variant="subtitle1" sx={{ fontWeight: 700, mt: 3, mb: 1.5 }}>
                Hangi derslere çalışmak istiyorsunuz?
              </Typography>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                {SUBJECTS.map((subj) => (
                  <Chip
                    key={subj.value}
                    label={subj.label}
                    onClick={() => toggleSubject(subj.value)}
                    color={selectedSubjects.includes(subj.value) ? 'primary' : 'default'}
                    variant={selectedSubjects.includes(subj.value) ? 'filled' : 'outlined'}
                    icon={<School sx={{ fontSize: 16 }} />}
                  />
                ))}
              </Box>

              <Typography variant="subtitle1" sx={{ fontWeight: 700, mt: 3, mb: 1 }}>
                Hedef süre: {durationMonths} ay
              </Typography>
              <Slider
                value={durationMonths}
                onChange={(_, v) => setDurationMonths(v as number)}
                min={1}
                max={12}
                step={1}
                marks={[
                  { value: 1, label: '1 ay' },
                  { value: 6, label: '6 ay' },
                  { value: 12, label: '12 ay' },
                ]}
                sx={{ mx: 1 }}
              />

              <Typography variant="subtitle1" sx={{ fontWeight: 700, mt: 2, mb: 1 }}>
                Günlük çalışma süresi: {availableTime} dk
              </Typography>
              <Slider
                value={availableTime}
                onChange={(_, v) => setAvailableTime(v as number)}
                min={30}
                max={240}
                step={15}
                marks={[
                  { value: 30, label: '30dk' },
                  { value: 120, label: '2sa' },
                  { value: 240, label: '4sa' },
                ]}
                sx={{ mx: 1 }}
              />
            </Box>
          )}

          {/* ── Step 2: Bilgi Değerlendirmesi ── */}
          {activeStep === 1 && (
            <Box>
              {!assessmentMode && !diagnosticDone && (
                <>
                  <Typography variant="subtitle1" sx={{ fontWeight: 700, mb: 2 }}>
                    Mevcut bilgi düzeyinizi nasıl belirleyelim?
                  </Typography>
                  <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 2 }}>
                    <GlassCard
                      glassIntensity="light"
                      hoverable
                      onClick={startDiagnostic}
                      sx={{ cursor: 'pointer', textAlign: 'center', p: 3 }}
                    >
                      <Quiz sx={{ fontSize: 40, color: '#6366f1', mb: 1 }} />
                      <Typography variant="subtitle2" sx={{ fontWeight: 700 }}>
                        Hızlı Test
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        10 soru ile seviyenizi tespit edelim
                      </Typography>
                    </GlassCard>
                    <GlassCard
                      glassIntensity="light"
                      hoverable
                      onClick={() => setAssessmentMode('self')}
                      sx={{ cursor: 'pointer', textAlign: 'center', p: 3 }}
                    >
                      <EditNote sx={{ fontSize: 40, color: '#22c55e', mb: 1 }} />
                      <Typography variant="subtitle2" sx={{ fontWeight: 700 }}>
                        Öz Değerlendirme
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        Kendi seviyenizi seçin
                      </Typography>
                    </GlassCard>
                  </Box>
                </>
              )}

              {assessmentMode === 'self' && (
                <>
                  <Typography variant="subtitle1" sx={{ fontWeight: 700, mb: 2 }}>
                    Genel bilgi düzeyinizi seçin
                  </Typography>
                  <RadioGroup value={knowledgeLevel} onChange={(e) => setKnowledgeLevel(e.target.value)}>
                    {KNOWLEDGE_LEVELS.map((level) => (
                      <FormControlLabel
                        key={level.value}
                        value={level.value}
                        control={<Radio />}
                        label={
                          <Box>
                            <Typography variant="body2" sx={{ fontWeight: 600 }}>{level.label}</Typography>
                            <Typography variant="caption" color="text.secondary">{level.description}</Typography>
                          </Box>
                        }
                        sx={{
                          mb: 0.5, p: 1.5, borderRadius: 2,
                          border: '1px solid',
                          borderColor: knowledgeLevel === level.value ? '#6366f1' : 'divider',
                          backgroundColor: knowledgeLevel === level.value ? '#6366f110' : 'transparent',
                        }}
                      />
                    ))}
                  </RadioGroup>
                </>
              )}

              {diagnosticDone && (
                <Box sx={{ textAlign: 'center', py: 3 }}>
                  <CheckCircle sx={{ fontSize: 48, color: '#22c55e', mb: 2 }} />
                  <Typography variant="h6" sx={{ fontWeight: 700, mb: 1 }}>
                    Seviye Tespit Edildi
                  </Typography>
                  <Chip
                    label={KNOWLEDGE_LEVELS.find(l => l.value === knowledgeLevel)?.label || knowledgeLevel}
                    color="primary"
                    sx={{ fontWeight: 700, fontSize: '1rem', py: 2.5, px: 1 }}
                  />
                </Box>
              )}
            </Box>
          )}

          {/* ── Step 3: Öğrenme Tercihleri ── */}
          {activeStep === 2 && (
            <Box>
              <Typography variant="subtitle1" sx={{ fontWeight: 700, mb: 2 }}>
                İçerik formatı tercihiniz nedir?
              </Typography>
              <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 2 }}>
                {LEARNING_PREFERENCES.map((pref) => {
                  const Icon = pref.icon;
                  const isSelected = learningPreference === pref.value;
                  return (
                    <GlassCard
                      key={pref.value}
                      glassIntensity="light"
                      hoverable
                      onClick={() => setLearningPreference(pref.value)}
                      sx={{
                        cursor: 'pointer',
                        textAlign: 'center',
                        p: 3,
                        border: '2px solid',
                        borderColor: isSelected ? pref.color : 'transparent',
                        backgroundColor: isSelected ? `${pref.color}10` : undefined,
                      }}
                    >
                      <Icon sx={{ fontSize: 40, color: pref.color, mb: 1 }} />
                      <Typography variant="subtitle2" sx={{ fontWeight: 700 }}>
                        {pref.label}
                      </Typography>
                    </GlassCard>
                  );
                })}
              </Box>
            </Box>
          )}

          {/* ── Step 4: Özet & Oluştur ── */}
          {activeStep === 3 && (
            <Box>
              <Typography variant="subtitle1" sx={{ fontWeight: 700, mb: 2 }}>
                Öğrenme yolunuz hazır mı?
              </Typography>
              <GlassCard glassIntensity="light" sx={{ mb: 2 }}>
                <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 1.5 }}>
                  <Box>
                    <Typography variant="caption" color="text.secondary">Sınav</Typography>
                    <Typography variant="body2" sx={{ fontWeight: 600 }}>
                      {EXAM_TYPES.find(e => e.value === examType)?.label}
                    </Typography>
                  </Box>
                  <Box>
                    <Typography variant="caption" color="text.secondary">Süre</Typography>
                    <Typography variant="body2" sx={{ fontWeight: 600 }}>{durationMonths} ay</Typography>
                  </Box>
                  <Box>
                    <Typography variant="caption" color="text.secondary">Günlük Çalışma</Typography>
                    <Typography variant="body2" sx={{ fontWeight: 600 }}>{availableTime} dk</Typography>
                  </Box>
                  <Box>
                    <Typography variant="caption" color="text.secondary">Seviye</Typography>
                    <Typography variant="body2" sx={{ fontWeight: 600 }}>
                      {KNOWLEDGE_LEVELS.find(l => l.value === knowledgeLevel)?.label}
                    </Typography>
                  </Box>
                </Box>
                <Box sx={{ mt: 1.5 }}>
                  <Typography variant="caption" color="text.secondary">Dersler</Typography>
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mt: 0.5 }}>
                    {selectedSubjects.map(s => (
                      <Chip key={s} label={SUBJECTS.find(sub => sub.value === s)?.label || s} size="small" />
                    ))}
                  </Box>
                </Box>
                <Box sx={{ mt: 1.5 }}>
                  <Typography variant="caption" color="text.secondary">Tercih</Typography>
                  <Typography variant="body2" sx={{ fontWeight: 600 }}>
                    {LEARNING_PREFERENCES.find(p => p.value === learningPreference)?.label}
                  </Typography>
                </Box>
              </GlassCard>
            </Box>
          )}
        </Box>
      </Fade>

      {/* ─── Navigation Buttons ─── */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 3 }}>
        <Box sx={{ display: 'flex', gap: 1 }}>
          {activeStep > 0 && (
            <ModernButton variant="glass" icon={<ArrowBack />} onClick={handleBack}>
              Geri
            </ModernButton>
          )}
          {onSkip && activeStep === 0 && (
            <ModernButton variant="glass" onClick={onSkip}>
              Atla
            </ModernButton>
          )}
        </Box>
        <ModernButton
          variant="gradient"
          gradient={activeStep === 3 ? modernColors.gradients.success : modernColors.gradients.primary}
          icon={activeStep === 3 ? <AutoAwesome /> : <ArrowForward />}
          onClick={handleNext}
          disabled={!canProceed()}
        >
          {activeStep === 3 ? 'Yolumu Oluştur' : 'İleri'}
        </ModernButton>
      </Box>
    </GlassCard>
  );
}

export default OnboardingWizard;

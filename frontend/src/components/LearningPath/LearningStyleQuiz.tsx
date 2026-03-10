/**
 * LearningStyleQuiz - VARK Öğrenme Stili Anketi
 *
 * Backend'deki anket şablonundan (learning_style_detector.py) alınan 5 soru.
 * Her soru 4 seçenekli (Visual/Auditory/Reading/Kinesthetic).
 * Sonuçlar submitQuestionnaire API'si ile backend'e gönderilir.
 */

import { useState, useCallback } from 'react';
import {
  Box,
  Button,
  Card,
  CardContent,
  Typography,
  RadioGroup,
  FormControlLabel,
  Radio,
  LinearProgress,
  Chip,
  Fade,
} from '@mui/material';
import {
  Visibility,
  Hearing,
  MenuBook,
  TouchApp,
  ArrowForward,
  ArrowBack,
  CheckCircle,
} from '@mui/icons-material';

interface QuizOption {
  text: string;
  style: 'visual' | 'auditory' | 'reading' | 'kinesthetic';
}

interface QuizQuestion {
  id: string;
  question: string;
  options: QuizOption[];
}

export interface QuizResult {
  dominant_style: string;
  scores: Record<string, number>;
  responses: Record<string, string>;
  completion_time: number;
}

interface LearningStyleQuizProps {
  onComplete: (result: QuizResult) => void;
  onSkip?: () => void;
}

const QUESTIONS: QuizQuestion[] = [
  {
    id: 'q1',
    question: 'Yeni bir konuyu öğrenirken hangi yöntemi tercih edersiniz?',
    options: [
      { text: 'Diyagramlar ve grafikler', style: 'visual' },
      { text: 'Sesli açıklamalar', style: 'auditory' },
      { text: 'Yazılı materyaller', style: 'reading' },
      { text: 'Uygulamalı deneyimler', style: 'kinesthetic' },
    ],
  },
  {
    id: 'q2',
    question: 'Bir problemi çözerken nasıl yaklaşırsınız?',
    options: [
      { text: 'Görsel şemalar çizerim', style: 'visual' },
      { text: 'Kendimle konuşurum', style: 'auditory' },
      { text: 'Adım adım yazarım', style: 'reading' },
      { text: 'Deneme yanılma yaparım', style: 'kinesthetic' },
    ],
  },
  {
    id: 'q3',
    question: 'Bilgiyi en iyi nasıl hatırlarsınız?',
    options: [
      { text: 'Görsel imgeler halinde', style: 'visual' },
      { text: 'Sesli tekrarlar yaparak', style: 'auditory' },
      { text: 'Notlar alarak', style: 'reading' },
      { text: 'Uygulayarak', style: 'kinesthetic' },
    ],
  },
  {
    id: 'q4',
    question: 'Grup çalışmasında hangi rolü tercih edersiniz?',
    options: [
      { text: 'Sunum hazırlayıcı', style: 'visual' },
      { text: 'Tartışma lideri', style: 'auditory' },
      { text: 'Araştırmacı/yazıcı', style: 'reading' },
      { text: 'Uygulama sorumlusu', style: 'kinesthetic' },
    ],
  },
  {
    id: 'q5',
    question: 'Boş zamanınızda hangi aktiviteyi tercih edersiniz?',
    options: [
      { text: 'Film/video izlemek', style: 'visual' },
      { text: 'Müzik dinlemek/podcast', style: 'auditory' },
      { text: 'Kitap okumak', style: 'reading' },
      { text: 'Spor/oyun oynamak', style: 'kinesthetic' },
    ],
  },
];

const STYLE_LABELS: Record<string, { label: string; icon: typeof Visibility; color: string }> = {
  visual: { label: 'Görsel', icon: Visibility, color: '#2196F3' },
  auditory: { label: 'İşitsel', icon: Hearing, color: '#FF9800' },
  reading: { label: 'Okuma-Yazma', icon: MenuBook, color: '#4CAF50' },
  kinesthetic: { label: 'Uygulamalı', icon: TouchApp, color: '#9C27B0' },
};

export function LearningStyleQuiz({ onComplete, onSkip }: LearningStyleQuizProps) {
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [startTime] = useState(Date.now());

  const progress = ((currentQuestion + (answers[QUESTIONS[currentQuestion]?.id] ? 1 : 0)) / QUESTIONS.length) * 100;
  const isLastQuestion = currentQuestion === QUESTIONS.length - 1;
  const currentQ = QUESTIONS[currentQuestion];
  const selectedAnswer = answers[currentQ.id] || '';

  const handleAnswer = useCallback((style: string) => {
    setAnswers(prev => ({ ...prev, [currentQ.id]: style }));
  }, [currentQ.id]);

  const handleNext = useCallback(() => {
    if (isLastQuestion) {
      // Calculate scores
      const scores: Record<string, number> = { visual: 0, auditory: 0, reading: 0, kinesthetic: 0 };
      Object.values(answers).forEach(style => {
        scores[style] = (scores[style] || 0) + 1;
      });

      // Normalize to 0-1
      const total = QUESTIONS.length;
      Object.keys(scores).forEach(key => {
        scores[key] = scores[key] / total;
      });

      // Find dominant
      const dominant = Object.entries(scores).reduce((a, b) => (b[1] > a[1] ? b : a))[0];

      onComplete({
        dominant_style: dominant,
        scores,
        responses: answers,
        completion_time: Math.round((Date.now() - startTime) / 1000),
      });
    } else {
      setCurrentQuestion(prev => prev + 1);
    }
  }, [isLastQuestion, answers, startTime, onComplete]);

  const handleBack = useCallback(() => {
    setCurrentQuestion(prev => Math.max(0, prev - 1));
  }, []);

  return (
    <Card
      sx={{
        maxWidth: 600,
        mx: 'auto',
        mt: 4,
        borderRadius: 3,
        boxShadow: '0 8px 32px rgba(0,0,0,0.12)',
      }}
    >
      <CardContent sx={{ p: 4 }}>
        <Typography variant="h5" gutterBottom fontWeight={600} textAlign="center">
          Öğrenme Stilinizi Keşfedin
        </Typography>
        <Typography variant="body2" color="text.secondary" textAlign="center" sx={{ mb: 3 }}>
          Size en uygun öğrenme yolunu oluşturmak için birkaç soru cevaplayın
        </Typography>

        <Box sx={{ mb: 3 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
            <Typography variant="caption" color="text.secondary">
              Soru {currentQuestion + 1} / {QUESTIONS.length}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              %{Math.round(progress)}
            </Typography>
          </Box>
          <LinearProgress
            variant="determinate"
            value={progress}
            sx={{ height: 8, borderRadius: 4 }}
          />
        </Box>

        <Fade in key={currentQ.id}>
          <Box>
            <Typography variant="h6" sx={{ mb: 3, fontWeight: 500 }}>
              {currentQ.question}
            </Typography>

            <RadioGroup
              value={selectedAnswer}
              onChange={(e) => handleAnswer(e.target.value)}
            >
              {currentQ.options.map((option) => {
                const styleInfo = STYLE_LABELS[option.style];
                const StyleIcon = styleInfo.icon;
                return (
                  <FormControlLabel
                    key={option.style}
                    value={option.style}
                    control={<Radio />}
                    label={
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <StyleIcon sx={{ color: styleInfo.color, fontSize: 20 }} />
                        <Typography>{option.text}</Typography>
                      </Box>
                    }
                    sx={{
                      mb: 1,
                      p: 1.5,
                      borderRadius: 2,
                      border: '1px solid',
                      borderColor: selectedAnswer === option.style ? styleInfo.color : 'divider',
                      backgroundColor: selectedAnswer === option.style ? `${styleInfo.color}10` : 'transparent',
                      transition: 'all 0.2s',
                      '&:hover': { backgroundColor: `${styleInfo.color}08` },
                    }}
                  />
                );
              })}
            </RadioGroup>
          </Box>
        </Fade>

        <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 3 }}>
          <Button
            onClick={handleBack}
            disabled={currentQuestion === 0}
            startIcon={<ArrowBack />}
          >
            Geri
          </Button>

          <Box sx={{ display: 'flex', gap: 1 }}>
            {onSkip && currentQuestion === 0 && (
              <Button variant="text" color="inherit" onClick={onSkip} size="small">
                Atla
              </Button>
            )}
            <Button
              variant="contained"
              onClick={handleNext}
              disabled={!selectedAnswer}
              endIcon={isLastQuestion ? <CheckCircle /> : <ArrowForward />}
            >
              {isLastQuestion ? 'Tamamla' : 'İleri'}
            </Button>
          </Box>
        </Box>

        <Box sx={{ display: 'flex', justifyContent: 'center', gap: 1, mt: 3 }}>
          {Object.entries(STYLE_LABELS).map(([key, info]) => (
            <Chip
              key={key}
              label={info.label}
              size="small"
              sx={{
                backgroundColor: `${info.color}15`,
                color: info.color,
                fontSize: '0.7rem',
              }}
            />
          ))}
        </Box>
      </CardContent>
    </Card>
  );
}

export default LearningStyleQuiz;

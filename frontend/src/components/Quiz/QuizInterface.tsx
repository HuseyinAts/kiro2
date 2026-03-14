import {
  Timer,
  CheckCircle,
  Cancel,
  NavigateNext,
  NavigateBefore,
  BookmarkBorder,
  Bookmark,
  Lightbulb,
  Code,
  Description,
  Psychology,
  Calculate,
  Send,
  Refresh,
  EmojiEvents,
  TrendingUp,
  Warning,
} from '@mui/icons-material';
import {
  Paper,
  Button,
  RadioGroup,
  FormControlLabel,
  Radio,
  Checkbox,
  LinearProgress,
  Chip,
  Card,
  CardContent,
  Alert,
  TextField,
  IconButton,
  Tooltip,
} from '@mui/material';
import confetti from 'canvas-confetti';
import clsx from 'clsx';
import { motion, AnimatePresence } from 'framer-motion';
import { useState, useEffect } from 'react';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';

import { ErrorTypeSelector, type ErrorType } from './ErrorTypeSelector';
import { MnemonicHint } from './MnemonicHint';

export interface Question {
  id: string
  type: 'multiple-choice' | 'multiple-select' | 'code' | 'text' | 'true-false'
  question: string
  description?: string
  code?: string
  options?: string[]
  correctAnswer?: string | string[]
  explanation?: string
  difficulty: 'easy' | 'medium' | 'hard'
  points: number
  timeLimit?: number
  hints?: string[]
  tags?: string[]
}

export interface QuizConfig {
  title: string
  description: string
  questions: Question[]
  timeLimit?: number
  passingScore: number
  allowReview?: boolean
  showCorrectAnswers?: boolean
  adaptiveDifficulty?: boolean
  /** Pratik modu: Her cevaptan sonra anında doğru/yanlış + açıklama göster (d=1.29) */
  immediateFeedback?: boolean
}

interface QuizInterfaceProps {
  config: QuizConfig
  onSubmit?: (results: QuizResults) => void
  onExit?: () => void
  /** F8: Called when student classifies a wrong answer's error type */
  onErrorTypeSelect?: (questionId: string, errorType: ErrorType) => void
  className?: string
}

interface QuizResults {
  score: number
  totalScore: number
  percentage: number
  answers: Record<string, any>
  timeSpent: number
  correctCount: number
  incorrectCount: number
  isTimeout?: boolean  // True if quiz ended due to timeout
}

export function QuizInterface({
  config,
  onSubmit,
  onExit,
  onErrorTypeSelect,
  className,
}: QuizInterfaceProps) {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [answers, setAnswers] = useState<Record<string, any>>({});
  const [flagged, setFlagged] = useState<Set<string>>(new Set());
  const [showHint, setShowHint] = useState(false);
  const [currentHintIndex, setCurrentHintIndex] = useState(0);
  const [timeLeft, setTimeLeft] = useState(config.timeLimit || 0);
  const [isSubmitted, setIsSubmitted] = useState(false);
  const [results, setResults] = useState<QuizResults | null>(null);
  const [_showExplanation, _setShowExplanation] = useState(false);
  const [reviewMode, setReviewMode] = useState(false);
  const [startTime] = useState(Date.now());
  // Immediate feedback state — shows correct/wrong after answering (d=1.29)
  const [feedbackVisible, setFeedbackVisible] = useState(false);
  const [feedbackCorrect, setFeedbackCorrect] = useState(false);

  const currentQuestion = config.questions[currentIndex];
  const isLastQuestion = currentIndex === config.questions.length - 1;
  const isFirstQuestion = currentIndex === 0;

  // Timer effect
  useEffect(() => {
    if (!config.timeLimit || isSubmitted || timeLeft <= 0) {return;}

    const timer = setInterval(() => {
      setTimeLeft(prev => {
        if (prev <= 1) {
          // Timeout: submit with timeout flag
          setTimeout(() => handleSubmit(true), 0);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [timeLeft, isSubmitted, config.timeLimit]);

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const handleAnswerChange = (value: any) => {
    setAnswers(prev => ({
      ...prev,
      [currentQuestion.id]: value,
    }));
    // Immediate feedback: show correct/wrong right after answering
    if (config.immediateFeedback) {
      const isCorrect = currentQuestion.type === 'multiple-select'
        ? Array.isArray(currentQuestion.correctAnswer) &&
          Array.isArray(value) &&
          currentQuestion.correctAnswer.length === value.length &&
          (currentQuestion.correctAnswer as string[]).every(a => value.includes(a))
        : value === currentQuestion.correctAnswer;
      setFeedbackCorrect(isCorrect);
      setFeedbackVisible(true);
    }
  };

  const handleMultiSelectChange = (option: string) => {
    const current = answers[currentQuestion.id] || [];
    const updated = current.includes(option)
      ? current.filter((o: string) => o !== option)
      : [...current, option];
    handleAnswerChange(updated);
  };

  const handleNext = () => {
    if (!isLastQuestion) {
      setCurrentIndex(prev => prev + 1);
      setShowHint(false);
      setCurrentHintIndex(0);
      setFeedbackVisible(false);
    }
  };

  const handlePrevious = () => {
    if (!isFirstQuestion) {
      setCurrentIndex(prev => prev - 1);
      setShowHint(false);
      setCurrentHintIndex(0);
      setFeedbackVisible(false);
    }
  };

  const toggleFlag = () => {
    const newFlagged = new Set(flagged);
    if (newFlagged.has(currentQuestion.id)) {
      newFlagged.delete(currentQuestion.id);
    } else {
      newFlagged.add(currentQuestion.id);
    }
    setFlagged(newFlagged);
  };

  const calculateResults = (timeout: boolean = false): QuizResults => {
    let correctCount = 0;
    let totalScore = 0;
    let earnedScore = 0;

    config.questions.forEach(question => {
      totalScore += question.points;
      const userAnswer = answers[question.id];

      let isCorrect = false;
      if (question.type === 'multiple-select') {
        const correct = question.correctAnswer as string[];
        const user = userAnswer || [];
        isCorrect =
          correct.length === user.length &&
          correct.every(ans => user.includes(ans));
      } else {
        isCorrect = userAnswer === question.correctAnswer;
      }

      if (isCorrect) {
        correctCount++;
        earnedScore += question.points;
      }
    });

    const percentage = Math.round((earnedScore / totalScore) * 100);
    const timeSpent = Math.round((Date.now() - startTime) / 1000);

    return {
      score: earnedScore,
      totalScore,
      percentage,
      answers,
      timeSpent,
      correctCount,
      incorrectCount: config.questions.length - correctCount,
      isTimeout: timeout,  // Include timeout flag in results
    };
  };

  const handleSubmit = (timeout: boolean = false) => {
    const quizResults = calculateResults(timeout);
    setResults(quizResults);
    setIsSubmitted(true);

    if (quizResults.percentage >= config.passingScore) {
      // Celebration animation
      confetti({
        particleCount: 100,
        spread: 70,
        origin: { y: 0.6 },
      });
    }

    onSubmit?.(quizResults);
  };

  const handleReview = () => {
    setReviewMode(true);
    setCurrentIndex(0);
  };

  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty) {
      case 'easy': return 'success';
      case 'medium': return 'warning';
      case 'hard': return 'error';
      default: return 'default';
    }
  };

  const getQuestionIcon = (type: string) => {
    switch (type) {
      case 'code': return <Code />;
      case 'text': return <Description />;
      case 'true-false': return <Psychology />;
      default: return <Calculate />;
    }
  };

  if (isSubmitted && results && !reviewMode) {
    return (
      <Paper elevation={3} className={clsx('p-6', className)}>
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="text-center"
        >
          <EmojiEvents
            className="text-6xl mb-4"
            style={{
              color: results.percentage >= config.passingScore ? '#10b981' : '#ef4444',
            }}
          />

          <h2 className="text-2xl font-bold mb-4">
            Quiz Tamamlandı!
          </h2>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <Card>
              <CardContent>
                <TrendingUp className="text-blue-500 mb-2" />
                <div className="text-2xl font-bold">{results.score}</div>
                <div className="text-sm text-gray-600">Puan</div>
              </CardContent>
            </Card>

            <Card>
              <CardContent>
                <CheckCircle className="text-green-500 mb-2" />
                <div className="text-2xl font-bold">{results.correctCount}</div>
                <div className="text-sm text-gray-600">Doğru</div>
              </CardContent>
            </Card>

            <Card>
              <CardContent>
                <Cancel className="text-red-500 mb-2" />
                <div className="text-2xl font-bold">{results.incorrectCount}</div>
                <div className="text-sm text-gray-600">Yanlış</div>
              </CardContent>
            </Card>

            <Card>
              <CardContent>
                <Timer className="text-purple-500 mb-2" />
                <div className="text-2xl font-bold">{formatTime(results.timeSpent)}</div>
                <div className="text-sm text-gray-600">Süre</div>
              </CardContent>
            </Card>
          </div>

          <div className="mb-6">
            <div className="text-4xl font-bold mb-2">
              %{results.percentage}
            </div>
            <LinearProgress
              variant="determinate"
              value={results.percentage}
              className="h-3 rounded-full"
              color={results.percentage >= config.passingScore ? 'success' : 'error'}
            />
          </div>

          {results.percentage >= config.passingScore ? (
            <Alert severity="success" className="mb-4">
              Tebrikler! Testi başarıyla geçtiniz!
            </Alert>
          ) : (
            <Alert severity="error" className="mb-4">
              Maalesef testi geçemediniz. Geçme notu: %{config.passingScore}
            </Alert>
          )}

          <div className="flex gap-2 justify-center">
            {config.allowReview && (
              <Button
                variant="outlined"
                onClick={handleReview}
                startIcon={<Description />}
              >
                Cevapları İncele
              </Button>
            )}
            <Button
              variant="contained"
              onClick={() => window.location.reload()}
              startIcon={<Refresh />}
            >
              Tekrar Dene
            </Button>
            <Button
              onClick={onExit}
            >
              Çıkış
            </Button>
          </div>
        </motion.div>
      </Paper>
    );
  }

  return (
    <Paper elevation={3} className={clsx('flex flex-col h-full', className)}>
      {/* Header */}
      <div className="p-4 border-b border-gray-200 bg-white">
        <div className="flex justify-between items-start mb-3">
          <div>
            <h2 className="text-xl font-bold">{config.title}</h2>
            <p className="text-sm text-gray-600">{config.description}</p>
          </div>

          {config.timeLimit && (
            <>
              <Chip
                icon={<Timer />}
                label={formatTime(timeLeft)}
                color={timeLeft < 60 ? 'error' : 'default'}
                className={timeLeft < 60 ? 'animate-pulse' : ''}
              />
              {timeLeft <= 30 && timeLeft > 0 && (
                <Chip
                  icon={<Warning />}
                  label="Süre bitiyor!"
                  color="error"
                  className="animate-pulse"
                />
              )}
            </>
          )}
        </div>

        <div className="flex justify-between items-center">
          <div className="flex gap-2">
            <Chip
              label={`Soru ${currentIndex + 1} / ${config.questions.length}`}
              variant="outlined"
            />
            <Chip
              label={currentQuestion.difficulty}
              size="small"
              color={getDifficultyColor(currentQuestion.difficulty) as any}
            />
            <Chip
              icon={getQuestionIcon(currentQuestion.type)}
              label={`${currentQuestion.points} puan`}
              size="small"
              variant="outlined"
            />
          </div>

          <LinearProgress
            variant="determinate"
            value={((currentIndex + 1) / config.questions.length) * 100}
            className="flex-1 mx-4 rounded-full"
          />
        </div>
      </div>

      {/* Question Content */}
      <div className="flex-1 overflow-y-auto p-6">
        <AnimatePresence mode="wait">
          <motion.div
            key={currentQuestion.id}
            initial={{ opacity: 0, x: 50 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -50 }}
            transition={{ duration: 0.3 }}
          >
            {/* Question */}
            <div className="mb-6">
              <div className="flex justify-between items-start mb-4">
                <h3 className="text-lg font-semibold flex-1">
                  {currentQuestion.question}
                </h3>

                <IconButton onClick={toggleFlag} size="small">
                  {flagged.has(currentQuestion.id) ? (
                    <Bookmark color="warning" />
                  ) : (
                    <BookmarkBorder />
                  )}
                </IconButton>
              </div>

              {currentQuestion.description && (
                <p className="text-gray-600 mb-4">
                  {currentQuestion.description}
                </p>
              )}

              {currentQuestion.code && (
                <Paper variant="outlined" className="p-4 mb-4 bg-gray-900 rounded-lg">
                  <SyntaxHighlighter
                    language="javascript"
                    style={vscDarkPlus}
                    showLineNumbers
                  >
                    {currentQuestion.code}
                  </SyntaxHighlighter>
                </Paper>
              )}
            </div>

            {/* Answer Options */}
            <div className="mb-6">
              {currentQuestion.type === 'multiple-choice' && (
                <RadioGroup
                  value={answers[currentQuestion.id] || ''}
                  onChange={(e) => handleAnswerChange(e.target.value)}
                >
                  {currentQuestion.options?.map((option, index) => (
                    <FormControlLabel
                      key={index}
                      value={option}
                      control={<Radio />}
                      label={option}
                      className={clsx(
                        'mb-2 p-2 rounded-lg border transition-all',
                        answers[currentQuestion.id] === option
                          ? 'border-blue-500 bg-blue-50'
                          : 'border-gray-200 hover:bg-gray-50',
                      )}
                    />
                  ))}
                </RadioGroup>
              )}

              {currentQuestion.type === 'multiple-select' && (
                <div className="space-y-2">
                  {currentQuestion.options?.map((option, index) => (
                    <FormControlLabel
                      key={index}
                      control={
                        <Checkbox
                          checked={(answers[currentQuestion.id] || []).includes(option)}
                          onChange={() => handleMultiSelectChange(option)}
                        />
                      }
                      label={option}
                      className={clsx(
                        'p-2 rounded-lg border transition-all',
                        (answers[currentQuestion.id] || []).includes(option)
                          ? 'border-blue-500 bg-blue-50'
                          : 'border-gray-200 hover:bg-gray-50',
                      )}
                    />
                  ))}
                </div>
              )}

              {currentQuestion.type === 'true-false' && (
                <RadioGroup
                  value={answers[currentQuestion.id] || ''}
                  onChange={(e) => handleAnswerChange(e.target.value)}
                  row
                >
                  <FormControlLabel
                    value="true"
                    control={<Radio />}
                    label="Doğru"
                    className={clsx(
                      'mr-4 px-4 py-2 rounded-lg border',
                      answers[currentQuestion.id] === 'true'
                        ? 'border-green-500 bg-green-50'
                        : 'border-gray-200',
                    )}
                  />
                  <FormControlLabel
                    value="false"
                    control={<Radio />}
                    label="Yanlış"
                    className={clsx(
                      'px-4 py-2 rounded-lg border',
                      answers[currentQuestion.id] === 'false'
                        ? 'border-red-500 bg-red-50'
                        : 'border-gray-200',
                    )}
                  />
                </RadioGroup>
              )}

              {currentQuestion.type === 'text' && (
                <TextField
                  fullWidth
                  multiline
                  rows={4}
                  variant="outlined"
                  placeholder="Cevabınızı yazın..."
                  value={answers[currentQuestion.id] || ''}
                  onChange={(e) => handleAnswerChange(e.target.value)}
                />
              )}

              {currentQuestion.type === 'code' && (
                <TextField
                  fullWidth
                  multiline
                  rows={10}
                  variant="outlined"
                  placeholder="// Kodunuzu buraya yazın..."
                  value={answers[currentQuestion.id] || ''}
                  onChange={(e) => handleAnswerChange(e.target.value)}
                  sx={{
                    '& .MuiInputBase-input': {
                      fontFamily: 'monospace',
                      fontSize: '14px',
                    },
                  }}
                />
              )}
            </div>

            {/* Hints */}
            {currentQuestion.hints && currentQuestion.hints.length > 0 && (
              <div className="mb-4">
                <Button
                  variant="outlined"
                  size="small"
                  startIcon={<Lightbulb />}
                  onClick={() => {
                    setShowHint(true);
                    setCurrentHintIndex(prev =>
                      Math.min(prev + 1, currentQuestion.hints!.length - 1),
                    );
                  }}
                >
                  İpucu ({currentHintIndex + 1}/{currentQuestion.hints.length})
                </Button>

                {showHint && (
                  <Alert severity="info" className="mt-2">
                    {currentQuestion.hints[currentHintIndex]}
                  </Alert>
                )}
              </div>
            )}

            {/* Immediate Feedback — Pratik modu (d=1.29) */}
            {config.immediateFeedback && feedbackVisible && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3 }}
              >
                <Alert
                  severity={feedbackCorrect ? 'success' : 'error'}
                  className="mt-4"
                  sx={{ borderRadius: 2 }}
                >
                  <div className="mb-1">
                    <strong>{feedbackCorrect ? 'Doğru!' : 'Yanlış'}</strong>
                    {!feedbackCorrect && currentQuestion.correctAnswer && (
                      <span> — Doğru cevap: <strong>{currentQuestion.correctAnswer}</strong></span>
                    )}
                  </div>
                  {currentQuestion.explanation && (
                    <div className="text-sm mt-1">
                      {currentQuestion.explanation}
                    </div>
                  )}
                </Alert>

                {/* F8: Error Type Selector — shown after wrong answer */}
                {!feedbackCorrect && onErrorTypeSelect && (
                  <ErrorTypeSelector
                    questionId={currentQuestion.id}
                    onSelect={onErrorTypeSelect}
                  />
                )}

                {/* F19: Mnemonic Hint — memory aid for the concept */}
                <MnemonicHint questionId={currentQuestion.id} compact />
              </motion.div>
            )}

            {/* Review Mode - Show Explanation */}
            {reviewMode && config.showCorrectAnswers && (
              <Alert
                severity={
                  answers[currentQuestion.id] === currentQuestion.correctAnswer
                    ? 'success'
                    : 'error'
                }
                className="mt-4"
              >
                <div className="mb-2">
                  <strong>Doğru Cevap:</strong> {currentQuestion.correctAnswer}
                </div>
                {currentQuestion.explanation && (
                  <div>
                    <strong>Açıklama:</strong> {currentQuestion.explanation}
                  </div>
                )}
                {/* F19: Mnemonic Hint in review mode */}
                <MnemonicHint questionId={currentQuestion.id} />
              </Alert>
            )}
          </motion.div>
        </AnimatePresence>
      </div>

      {/* Footer Navigation */}
      <div className="p-4 border-t border-gray-200 bg-white">
        <div className="flex justify-between items-center">
          <Button
            variant="outlined"
            startIcon={<NavigateBefore />}
            onClick={handlePrevious}
            disabled={isFirstQuestion}
          >
            Önceki
          </Button>

          <div className="flex gap-1">
            {config.questions.map((q, index) => (
              <Tooltip key={q.id} title={`Soru ${index + 1}`}>
                <div
                  className={clsx(
                    'w-8 h-8 rounded-full flex items-center justify-center text-xs cursor-pointer',
                    'transition-all duration-200',
                    index === currentIndex
                      ? 'bg-blue-500 text-white scale-110'
                      : answers[q.id]
                      ? 'bg-green-100 text-green-700'
                      : 'bg-gray-200 text-gray-600',
                    flagged.has(q.id) && 'ring-2 ring-yellow-400',
                  )}
                  onClick={() => setCurrentIndex(index)}
                >
                  {index + 1}
                </div>
              </Tooltip>
            ))}
          </div>

          {!reviewMode ? (
            isLastQuestion ? (
              <Button
                variant="contained"
                color="success"
                endIcon={<Send />}
                onClick={() => handleSubmit(false)}
              >
                Gönder
              </Button>
            ) : (
              <Button
                variant="contained"
                endIcon={<NavigateNext />}
                onClick={handleNext}
              >
                Sonraki
              </Button>
            )
          ) : (
            <Button
              variant="contained"
              onClick={() => onExit?.()}
            >
              Çıkış
            </Button>
          )}
        </div>
      </div>
    </Paper>
  );
}

export default QuizInterface;
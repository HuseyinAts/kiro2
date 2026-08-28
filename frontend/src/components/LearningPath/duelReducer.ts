export type DuelPhase =
  | 'idle'
  | 'matchmaking'
  | 'waiting'
  | 'playing'
  | 'round_result'
  | 'finished'
  | 'ai_playing';

export interface DuelQuestion {
  id: string;
  content: string;
  options: { key: string; text: string }[];
  subject: string;
  difficulty?: number;
}

export interface RoundResult {
  questionOrder: number;
  myAnswer: string;
  isCorrect: boolean;
  myScore: number;
  opponentScore: number;
  opponentAnswered: boolean;
}

export interface DuelRating {
  elo_rating: number;
  wins: number;
  losses: number;
  draws: number;
  peak_rating: number;
}

export interface DuelState {
  rating: DuelRating | null;
  loadingRating: boolean;
  phase: DuelPhase;
  sessionId: string | null;
  useAiBot: boolean;
  matchmakeError: string | null;
  myScore: number;
  opponentScore: number;
  opponentAnswered: boolean;
  questions: DuelQuestion[];
  currentQIndex: number;
  selectedAnswer: string | null;
  roundResult: RoundResult | null;
  roundHistory: RoundResult[];
  answerSubmitting: boolean;
}

export const initialDuelState: DuelState = {
  rating: null,
  loadingRating: false,
  phase: 'idle',
  sessionId: null,
  useAiBot: false,
  matchmakeError: null,
  myScore: 0,
  opponentScore: 0,
  opponentAnswered: false,
  questions: [],
  currentQIndex: 0,
  selectedAnswer: null,
  roundResult: null,
  roundHistory: [],
  answerSubmitting: false,
};

export type DuelAction =
  | { type: 'SET_RATING'; payload: DuelRating | null }
  | { type: 'SET_LOADING_RATING'; payload: boolean }
  | { type: 'START_MATCHMAKING' }
  | { type: 'MATCHMAKING_ERROR'; payload: string }
  | { type: 'MATCH_FOUND'; payload: { sessionId: string; questions?: DuelQuestion[] } }
  | { type: 'START_AI_BOT'; payload: { questions: DuelQuestion[] } }
  | { type: 'SET_QUESTIONS'; payload: DuelQuestion[] }
  | { type: 'UPDATE_QUESTION'; payload: { index: number; question: DuelQuestion } }
  | { type: 'NEXT_QUESTION'; payload: number }
  | { type: 'SUBMIT_ANSWER'; payload: string }
  | { type: 'ANSWER_RESULT'; payload: RoundResult }
  | { type: 'OPPONENT_ANSWERED'; payload: { score?: number } }
  | { type: 'ROUND_COMPLETE'; payload: { myScore: number; opponentScore: number } }
  | { type: 'FINISH_DUEL'; payload: { myScore: number; opponentScore: number } }
  | { type: 'RESET_GAME' }
  | { type: 'SET_ANSWER_SUBMITTING'; payload: boolean };

export function duelReducer(state: DuelState, action: DuelAction): DuelState {
  switch (action.type) {
    case 'SET_RATING':
      return { ...state, rating: action.payload };
    case 'SET_LOADING_RATING':
      return { ...state, loadingRating: action.payload };
    case 'START_MATCHMAKING':
      return {
        ...state,
        phase: 'matchmaking',
        matchmakeError: null,
        myScore: 0,
        opponentScore: 0,
        roundHistory: [],
      };
    case 'MATCHMAKING_ERROR':
      return { ...state, matchmakeError: action.payload };
    case 'MATCH_FOUND':
      return {
        ...state,
        sessionId: action.payload.sessionId,
        useAiBot: false,
        phase: 'waiting',
        ...(action.payload.questions ? { questions: action.payload.questions } : {})
      };
    case 'START_AI_BOT':
      return {
        ...state,
        useAiBot: true,
        sessionId: null,
        questions: action.payload.questions,
        currentQIndex: 0,
        myScore: 0,
        opponentScore: 0,
        opponentAnswered: false,
        roundHistory: [],
        selectedAnswer: null,
        phase: 'ai_playing',
      };
    case 'SET_QUESTIONS':
      return { ...state, questions: action.payload };
    case 'UPDATE_QUESTION': {
      const nextQ = [...state.questions];
      nextQ[action.payload.index] = action.payload.question;
      return { ...state, questions: nextQ };
    }
    case 'NEXT_QUESTION':
      return {
        ...state,
        currentQIndex: action.payload,
        selectedAnswer: null,
        opponentAnswered: false,
        phase: 'playing',
      };
    case 'SUBMIT_ANSWER':
      return { ...state, selectedAnswer: action.payload, answerSubmitting: true };
    case 'SET_ANSWER_SUBMITTING':
      return { ...state, answerSubmitting: action.payload };
    case 'ANSWER_RESULT':
      return {
        ...state,
        roundResult: action.payload,
        roundHistory: [...state.roundHistory, action.payload],
        myScore: action.payload.myScore,
        opponentScore: action.payload.opponentScore,
        opponentAnswered: action.payload.opponentAnswered,
        phase: 'round_result',
        answerSubmitting: false,
      };
    case 'OPPONENT_ANSWERED':
      return {
        ...state,
        opponentAnswered: true,
        ...(action.payload.score !== undefined ? { opponentScore: action.payload.score } : {})
      };
    case 'ROUND_COMPLETE':
      return { ...state, myScore: action.payload.myScore, opponentScore: action.payload.opponentScore };
    case 'FINISH_DUEL':
      return {
        ...state,
        myScore: action.payload.myScore,
        opponentScore: action.payload.opponentScore,
        phase: 'finished',
      };
    case 'RESET_GAME':
      return { ...initialDuelState, rating: state.rating };
    default:
      return state;
  }
}

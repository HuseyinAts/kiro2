import {
  CheckCircle,
  RadioButtonUnchecked,
  WarningAmber,
  Star,
  Timer,
  School,
} from '@mui/icons-material';
import { Tooltip, Chip, LinearProgress } from '@mui/material';
import clsx from 'clsx';
import { motion } from 'framer-motion';
import { MasteryBadge } from './MasteryBadge';

export interface PathNodeData {
  id: string
  title: string
  description: string
  type: 'lesson' | 'quiz' | 'project' | 'milestone'
  status: 'completed' | 'current' | 'locked' | 'available'
  progress: number
  estimatedTime: string
  difficulty: 'beginner' | 'intermediate' | 'advanced'
  points?: number
  mastery?: number
  prerequisites?: string[]
  resources?: number
  position: { x: number; y: number }
  quiz?: {
    quiz_id: string
    question_count: number
    passing_score: number
  }
}

interface PathNodeProps {
  node: PathNodeData
  onClick?: (node: PathNodeData) => void
  isHighlighted?: boolean
  showDetails?: boolean
}

export function PathNode({
  node,
  onClick,
  isHighlighted,
  showDetails = true,
}: PathNodeProps) {
  const getIcon = () => {
    switch (node.status) {
      case 'completed':
        return <CheckCircle className="text-green-500" />;
      case 'current':
        return <RadioButtonUnchecked className="text-blue-500 animate-pulse" />;
      case 'locked':
        return <WarningAmber className="text-amber-500" />;
      default:
        return <RadioButtonUnchecked className="text-gray-300" />;
    }
  };

  const getTypeIcon = () => {
    switch (node.type) {
      case 'lesson':
        return <School fontSize="small" />;
      case 'quiz':
        return '📝';
      case 'project':
        return '🚀';
      case 'milestone':
        return <Star fontSize="small" />;
      default:
        return '📚';
    }
  };

  const getDifficultyColor = () => {
    switch (node.difficulty) {
      case 'beginner':
        return 'success';
      case 'intermediate':
        return 'warning';
      case 'advanced':
        return 'error';
      default:
        return 'default';
    }
  };

  const nodeVariants = {
    initial: { scale: 0, opacity: 0 },
    animate: {
      scale: 1,
      opacity: 1,
      transition: {
        type: 'spring',
        stiffness: 260,
        damping: 20,
      },
    },
    hover: {
      scale: 1.05,
      transition: { duration: 0.2 },
    },
    tap: {
      scale: 0.95,
    },
  };

  return (
    <motion.div
      variants={nodeVariants}
      initial="initial"
      animate="animate"
      whileHover="hover"
      whileTap="tap"
      style={{
        position: 'absolute',
        left: node.position.x,
        top: node.position.y,
      }}
      className={clsx(
        'cursor-pointer',
        isHighlighted && 'z-10',
      )}
    >
      <Tooltip
        title={
          <div className="p-2">
            <h4 className="font-semibold mb-1">{node.title}</h4>
            <p className="text-sm mb-2">{node.description}</p>
            {node.status === 'locked' && (
              <p className="text-xs text-amber-300 mb-1">
                ⚠️ Bu konu seviyenin üstünde — önce önerilen konuları tamamlamanızı öneriyoruz.
              </p>
            )}
            <div className="flex items-center gap-2 text-xs">
              <Timer fontSize="small" />
              <span>{node.estimatedTime}</span>
              {node.points && (
                <>
                  <Star fontSize="small" />
                  <span>{node.points} puan</span>
                </>
              )}
            </div>
          </div>
        }
        arrow
        placement="top"
      >
        <div
          onClick={() => onClick?.(node)}
          className={clsx(
            'relative rounded-2xl border-2 bg-white shadow-lg',
            'transition-all duration-300 p-4',
            node.status === 'completed' && 'border-green-500 bg-green-50',
            node.status === 'current' && 'border-blue-500 bg-blue-50 animate-pulse',
            node.status === 'locked' && 'border-amber-300 bg-amber-50/50 opacity-80',
            node.status === 'available' && 'border-gray-300 hover:border-blue-400',
            isHighlighted && 'ring-4 ring-blue-200 ring-offset-2',
          )}
        >
          {/* Status Icon */}
          <div className="absolute -top-2 -right-2">
            {getIcon()}
          </div>

          {/* Content */}
          <div className="flex items-start gap-3">
            <div className={clsx(
              'w-10 h-10 rounded-lg flex items-center justify-center',
              node.status === 'completed' ? 'bg-green-100' :
              node.status === 'current' ? 'bg-blue-100' :
              node.status === 'locked' ? 'bg-gray-100' :
              'bg-gray-50',
            )}>
              {getTypeIcon()}
            </div>

            <div className="flex-1">
              <h3 className={clsx(
                'font-semibold text-sm mb-1',
                node.status === 'locked' ? 'text-amber-700' : 'text-gray-800',
              )}>
                {node.title}
              </h3>

              {showDetails && (
                <>
                  <p className="text-xs text-gray-600 mb-2 line-clamp-2">
                    {node.description}
                  </p>

                  {/* Progress Bar */}
                  {node.progress > 0 && node.progress < 100 && (
                    <LinearProgress
                      variant="determinate"
                      value={node.progress}
                      className="mb-2"
                      sx={{ height: 4, borderRadius: 2 }}
                    />
                  )}

                  {/* Mastery Badge */}
                  {node.mastery != null && node.mastery > 0 && (
                    <div className="mb-2">
                      <MasteryBadge mastery={node.mastery} compact />
                    </div>
                  )}

                  {/* Tags */}
                  <div className="flex flex-wrap gap-1">
                    <Chip
                      label={node.difficulty}
                      size="small"
                      color={getDifficultyColor() as any}
                      variant="outlined"
                      className="text-xs"
                    />

                    {node.resources && node.resources > 0 && (
                      <Chip
                        label={`${node.resources} kaynak`}
                        size="small"
                        variant="outlined"
                        className="text-xs"
                      />
                    )}

                    {/* Quiz Badge */}
                    {node.quiz && (
                      <Chip
                        label={`📝 ${node.quiz.question_count} Soru`}
                        size="small"
                        color="secondary"
                        className="text-xs"
                      />
                    )}

                    {node.status === 'current' && (
                      <Chip
                        label="Aktif"
                        size="small"
                        color="primary"
                        className="text-xs animate-pulse"
                      />
                    )}
                  </div>
                </>
              )}
            </div>
          </div>

          {/* Completion Badge */}
          {node.status === 'completed' && node.points && (
            <div className="absolute -bottom-2 left-1/2 transform -translate-x-1/2">
              <div className="bg-yellow-400 text-white text-xs px-2 py-1 rounded-full flex items-center gap-1">
                <Star fontSize="inherit" />
                <span>{node.points}</span>
              </div>
            </div>
          )}
        </div>
      </Tooltip>
    </motion.div>
  );
}
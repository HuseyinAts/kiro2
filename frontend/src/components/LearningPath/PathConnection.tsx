import clsx from 'clsx';
import { motion } from 'framer-motion';

interface PathConnectionProps {
  from: { x: number; y: number }
  to: { x: number; y: number }
  isActive?: boolean
  isCompleted?: boolean
  curved?: boolean
  animated?: boolean
}

export function PathConnection({
  from,
  to,
  isActive,
  isCompleted,
  curved = true,
  animated = true,
}: PathConnectionProps) {
  // Calculate control points for curved path
  const midX = (from.x + to.x) / 2;
  const midY = (from.y + to.y) / 2;
  const controlPoint1X = curved ? midX : from.x;
  const controlPoint1Y = curved ? from.y : midY;
  const controlPoint2X = curved ? midX : to.x;
  const controlPoint2Y = curved ? to.y : midY;

  const pathData = curved
    ? `M ${from.x} ${from.y} C ${controlPoint1X} ${controlPoint1Y}, ${controlPoint2X} ${controlPoint2Y}, ${to.x} ${to.y}`
    : `M ${from.x} ${from.y} L ${to.x} ${to.y}`;

  return (
    <svg
      style={{
        position: 'absolute',
        left: 0,
        top: 0,
        width: '100%',
        height: '100%',
        pointerEvents: 'none',
        zIndex: 0,
      }}
    >
      <defs>
        {/* Gradient for active connections */}
        <linearGradient id="activeGradient" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" stopColor="#3b82f6" stopOpacity="0.3" />
          <stop offset="50%" stopColor="#3b82f6" stopOpacity="1" />
          <stop offset="100%" stopColor="#3b82f6" stopOpacity="0.3" />
        </linearGradient>

        {/* Animated marker for active paths */}
        <circle id="movingDot" r="4" fill="#3b82f6">
          {animated && isActive && (
            <animateMotion
              dur="2s"
              repeatCount="indefinite"
              path={pathData}
            />
          )}
        </circle>

        {/* Arrow marker */}
        <marker
          id="arrowhead"
          markerWidth="10"
          markerHeight="10"
          refX="9"
          refY="3"
          orient="auto"
        >
          <polygon
            points="0 0, 10 3, 0 6"
            fill={isCompleted ? '#10b981' : isActive ? '#3b82f6' : '#9ca3af'}
          />
        </marker>
      </defs>

      {/* Shadow for depth */}
      <motion.path
        d={pathData}
        fill="none"
        stroke="rgba(0,0,0,0.1)"
        strokeWidth="6"
        strokeLinecap="round"
        style={{
          transform: 'translate(2px, 2px)',
          filter: 'blur(2px)',
        }}
      />

      {/* Main connection line */}
      <motion.path
        d={pathData}
        fill="none"
        stroke={
          isCompleted ? '#10b981' :
          isActive ? 'url(#activeGradient)' :
          '#d1d5db'
        }
        strokeWidth={isActive ? '4' : '3'}
        strokeLinecap="round"
        strokeDasharray={isActive && !isCompleted ? '10 5' : '0'}
        markerEnd="url(#arrowhead)"
        initial={{ pathLength: 0, opacity: 0 }}
        animate={{
          pathLength: 1,
          opacity: 1,
        }}
        transition={{
          pathLength: { duration: 1, ease: 'easeInOut' },
          opacity: { duration: 0.5 },
        }}
        className={clsx(
          isActive && !isCompleted && 'animate-pulse',
        )}
      />

      {/* Animated dots along active path */}
      {animated && isActive && !isCompleted && (
        <>
          <circle r="3" fill="#3b82f6">
            <animateMotion
              dur="3s"
              repeatCount="indefinite"
              path={pathData}
            />
          </circle>
          <circle r="3" fill="#3b82f6">
            <animateMotion
              dur="3s"
              begin="1s"
              repeatCount="indefinite"
              path={pathData}
            />
          </circle>
          <circle r="3" fill="#3b82f6">
            <animateMotion
              dur="3s"
              begin="2s"
              repeatCount="indefinite"
              path={pathData}
            />
          </circle>
        </>
      )}

      {/* Glow effect for active connections */}
      {isActive && (
        <motion.path
          d={pathData}
          fill="none"
          stroke="#3b82f6"
          strokeWidth="8"
          strokeLinecap="round"
          opacity="0.3"
          style={{
            filter: 'blur(8px)',
          }}
          animate={{
            opacity: [0.2, 0.5, 0.2],
          }}
          transition={{
            duration: 2,
            repeat: Infinity,
            ease: 'easeInOut',
          }}
        />
      )}
    </svg>
  );
}
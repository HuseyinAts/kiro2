import { motion, AnimatePresence } from 'framer-motion';
import { useCognitiveStore } from '../../store/cognitiveStore';

/**
 * 2026 Adaptive Cognitive UX Layer
 * Applies subtle global visual changes depending on the student's cognitive state.
 */
export function GlobalCognitiveWrapper() {
  const mode = useCognitiveStore(state => state.mode);

  return (
    <AnimatePresence>
      {mode === 'FOCUS' && (
        <motion.div
          key="focus-vignette"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 1.5, ease: 'easeInOut' }}
          style={{
            position: 'fixed',
            inset: 0,
            pointerEvents: 'none',
            zIndex: 9998,
            // Deep vignette to tunnel focus to the center
            background: 'radial-gradient(circle, transparent 40%, rgba(15, 23, 42, 0.4) 100%)',
          }}
        />
      )}
      {mode === 'OVERLOAD' && (
        <motion.div
          key="overload-chill"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 2, ease: 'easeInOut' }}
          style={{
            position: 'fixed',
            inset: 0,
            pointerEvents: 'none',
            zIndex: 9998,
            // Cooling blue filter to reduce stress
            background: 'rgba(56, 189, 248, 0.05)',
            backdropFilter: 'saturate(80%) hue-rotate(15deg)',
          }}
        />
      )}
    </AnimatePresence>
  );
}

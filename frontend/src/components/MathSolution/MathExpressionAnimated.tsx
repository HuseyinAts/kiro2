/**
 * Animasyonlu Matematik İfadesi Bileşeni
 * Requirements: REQ-51.27 (Değişen kısmı vurgulama)
 *
 * Bu bileşen:
 * - Matematiksel ifadelerdeki değişiklikleri vurgular
 * - Smooth transitions ile değişimleri gösterir
 * - Highlight changes (değişiklikleri vurgulama)
 */

import { motion, AnimatePresence } from 'framer-motion';
import * as React from 'react';
import {  useEffect, useState  } from 'react';

import { sanitizeHTML } from '../../utils/sanitize';

import { useAnimationContext } from './AnimationController';

interface MathExpressionAnimatedProps {
  expression: string;
  previousExpression?: string;
  highlightColor?: string;
  className?: string;
}

const MathExpressionAnimated: React.FC<MathExpressionAnimatedProps> = ({
  expression,
  previousExpression,
  highlightColor = '#FCD34D', // Yellow-300
  className = '',
}) => {
  const { enabled, getTransitionConfig } = useAnimationContext();
  const [showHighlight, setShowHighlight] = useState(false);
  const [changedParts, setChangedParts] = useState<string[]>([]);

  // Değişen kısımları tespit et
  useEffect(() => {
    if (previousExpression && expression !== previousExpression) {
      // Basit diff algoritması - gerçek uygulamada daha sofistike olabilir
      const changed = findChangedParts(previousExpression, expression);
      setChangedParts(changed);
      setShowHighlight(true);

      // 2 saniye sonra vurgulamayı kaldır
      const timer = setTimeout(() => {
        setShowHighlight(false);
      }, 2000);

      return () => clearTimeout(timer);
    }
  }, [expression, previousExpression]);

  // Değişen kısımları bul (basit implementasyon)
  const findChangedParts = (prev: string, current: string): string[] => {
    const changed: string[] = [];

    // Basit karakter karşılaştırması
    const maxLen = Math.max(prev.length, current.length);
    let changeStart = -1;

    for (let i = 0; i < maxLen; i++) {
      if (prev[i] !== current[i]) {
        if (changeStart === -1) {
          changeStart = i;
        }
      } else if (changeStart !== -1) {
        changed.push(current.substring(changeStart, i));
        changeStart = -1;
      }
    }

    if (changeStart !== -1) {
      changed.push(current.substring(changeStart));
    }

    return changed;
  };

  // Vurgulama ile ifadeyi render et
  const renderHighlightedExpression = () => {
    if (!showHighlight || changedParts.length === 0) {
      return expression;
    }

    let result = expression;
    changedParts.forEach((part) => {
      result = result.replace(
        part,
        `<span style="background-color: ${highlightColor}; padding: 2px 4px; border-radius: 4px; animation: pulse 1s ease-in-out;">${part}</span>`,
      );
    });

    return result;
  };

  const transitionConfig = getTransitionConfig();

  return (
    <div className={`relative ${className}`}>
      <AnimatePresence mode="wait">
        <motion.div
          key={expression}
          initial={enabled ? { opacity: 0, y: 10, scale: 0.95 } : undefined}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={enabled ? { opacity: 0, y: -10, scale: 0.95 } : undefined}
          transition={transitionConfig}
          className="text-center"
        >
          {/* SECURITY FIX #4: Sanitize HTML before rendering */}
          <div
            className="text-2xl font-mono text-gray-800 inline-block"
            dangerouslySetInnerHTML={{ __html: sanitizeHTML(renderHighlightedExpression()) }}
          />
        </motion.div>
      </AnimatePresence>

      {/* Pulse animation CSS */}
      <style>{`
        @keyframes pulse {
          0%, 100% {
            transform: scale(1);
          }
          50% {
            transform: scale(1.05);
          }
        }
      `}</style>
    </div>
  );
};

export default MathExpressionAnimated;

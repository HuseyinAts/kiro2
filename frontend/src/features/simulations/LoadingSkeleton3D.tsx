/**
 * LoadingSkeleton3D — Loading placeholder for 3D scenes
 * FAZ-6: 3D Simulasyon Modüller
 */
import React from 'react';

interface LoadingSkeleton3DProps {
  height?: string;
  label?: string;
  className?: string;
}

export const LoadingSkeleton3D: React.FC<LoadingSkeleton3DProps> = ({
  height = 'h-80',
  label = '3D simülasyon yükleniyor...',
  className = '',
}) => (
  <div
    className={`relative ${height} w-full rounded-2xl overflow-hidden bg-gray-900 ${className}`}
    aria-label={label}
    aria-busy="true"
  >
    {/* Animated grid */}
    <div
      className="absolute inset-0 opacity-10"
      style={{
        backgroundImage:
          'linear-gradient(rgba(255,255,255,0.1) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.1) 1px, transparent 1px)',
        backgroundSize: '40px 40px',
      }}
    />

    {/* Pulsing orbs */}
    <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 flex gap-6">
      {[0, 1, 2].map((i) => (
        <div
          key={i}
          className="w-16 h-16 rounded-full bg-purple-500/30 animate-pulse"
          style={{ animationDelay: `${i * 200}ms` }}
        />
      ))}
    </div>

    {/* Label */}
    <div className="absolute bottom-4 left-0 right-0 text-center">
      <p className="text-xs text-white/30 animate-pulse">{label}</p>
    </div>
  </div>
);

export default LoadingSkeleton3D;

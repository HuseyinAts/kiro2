import * as React from 'react';
import { font } from '../tokens';

/** Lig sıralaması avatar paleti (prototip PAL ile birebir) */
export const AVATAR_PAL = ['#3B82F6', '#8B5CF6', '#1FB683', '#EC4899', '#06B6D4', '#F59E0B', '#FF6F5C', '#0EA5E9', '#E8836B', '#14B8A6', '#FF8A5B'];

export interface AvatarProps {
  initials: string;
  size?: number; // 24-70
  bg?: string;
  /** podyum vurgusu — ör. '#F59E0B' */
  ring?: string;
}

export function Avatar({ initials, size = 38, bg = AVATAR_PAL[0], ring }: AvatarProps) {
  return (
    <span aria-hidden="true" style={{ width: size, height: size, flexShrink: 0,
      borderRadius: Math.round(size * 0.29),
      backgroundColor: bg, color: '#fff',
      display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
      fontFamily: font.sans, fontWeight: 800, fontSize: Math.round(size * 0.34),
      border: ring ? `3px solid ${ring}` : undefined }}>
      {initials}
    </span>
  );
}

import { useCurrentFrame, useVideoConfig } from 'remotion';
import React from 'react';

export interface WipeTransitionProps {
  duration: number;
  direction: 'left' | 'right' | 'up' | 'down';
  overlayColor: string;
}

/**
 * Wipe transition effect - directional screen wipe
 */
export const WipeTransition: React.FC<WipeTransitionProps> = ({ duration, direction, overlayColor }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  
  // Calculate progress from 0 to 1
  const progress = frame / (duration * fps);
  
  return (
    <div 
      className="absolute inset-0"
      style={{ 
        backgroundColor: overlayColor,
        clipPath: getWipeClipPath(direction, progress)
      }}
    />
  );
};

function getWipeClipPath(direction: string, progress: number): string {
  const p = Math.min(100, Math.max(0, progress * 100));
  
  switch(direction) {
    case 'left':
      // Wipe from left to right
      return `polygon(${p}% 0, 100% 0, 100% 100%, ${p}% 100%)`;
    case 'right':
      // Wipe from right to left
      return `polygon(0 0, ${100-p}% 0, ${100-p}% 100%, 0 100%)`;
    case 'up':
      // Wipe from top to bottom
      return `polygon(0 ${p}%, 100% ${p}%, 100% 100%, 0 100%)`;
    case 'down':
      // Wipe from bottom to top
      return `polygon(0 0, 100% 0, 100% ${100-p}%, 0 ${100-p}%)`;
    default:
      return `polygon(0 0, 0% 0, 100% 100%, 0 100%)`;
  }
}

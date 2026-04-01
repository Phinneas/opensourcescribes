import { useCurrentFrame, useVideoConfig, interpolate } from 'remotion';
import React from 'react';

export interface DissolveTransitionProps {
  duration: number;
  overlayColor: string;
}

/**
 * Smooth dissolve/cross-fade transition
 */
export const DissolveTransition: React.FC<DissolveTransitionProps> = ({ duration, overlayColor }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  
  // Smooth fade in and out
  const opacity = interpolate(
    frame,
    [0, duration * fps * 0.3, duration * fps * 0.7, duration * fps],
    [0, 1, 1, 0]
  );
  
  return (
    <div 
      className="absolute inset-0"
      style={{ 
        backgroundColor: overlayColor,
        opacity: opacity as number,
      }}
    />
  );
};

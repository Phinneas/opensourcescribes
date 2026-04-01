import { useCurrentFrame, useVideoConfig, interpolate, spring } from 'remotion';
import React from 'react';

export interface ZoomTransitionProps {
  duration: number;
  zoomIn: boolean;
  overlayColor: string;
}

/**
 * Zoom transition effect - smooth zoom in/out
 */
export const ZoomTransition: React.FC<ZoomTransitionProps> = ({ duration, zoomIn, overlayColor }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  
  // Smooth zoom animation
  const zoomProgress = spring({
    frame: frame,
    fps,
    config: {
      damping: 15,
      mass: 0.8,
      stiffness: 120,
    },
    from: 0,
    to: 1,
  });
  
  // Calculate scale factor
  const scale = interpolate(zoomProgress, [0, 1], zoomIn ? [2, 1] : [1, 2]) as number;
  
  return (
    <div 
      className="absolute inset-0"
      style={{ 
        backgroundColor: overlayColor,
        transform: `scale(${scale})`,
        transformOrigin: 'center',
        opacity: interpolate(zoomProgress, [0, 0.8, 0.9, 1], [0, 1, 1, 0]) as number,
      }}
    />
  );
};

import { useCurrentFrame, useVideoConfig, interpolate } from 'remotion';
import React from 'react';

export interface LoaderTransitionProps {
  duration: number;
  overlayColor: string;
  textColor?: string;
}

/**
 * Loading transition with animated spinner and tech aesthetic
 */
export const LoaderTransition: React.FC<LoaderTransitionProps> = ({ duration, overlayColor, textColor = '#ffffff' }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  
  // Rotation animation for spinner
  const rotation = interpolate(frame, [0, duration * fps], [0, 360], {
    extrapolateRight: 'extend',
  }) as number;
  
  // Fade in/out
  const opacity = interpolate(
    frame,
    [0, 15, duration * fps - 15, duration * fps],
    [0, 1, 1, 0]
  );
  
  return (
    <div 
      className="absolute inset-0 flex items-center justify-center"
      style={{ 
        backgroundColor: overlayColor,
        opacity: opacity as number,
      }}
    >
      <div className="flex flex-col items-center gap-6">
        {/* Animated spinner */}
        <div 
          className="w-20 h-20 border-4 rounded-full"
          style={{
            borderColor: textColor,
            borderTopColor: 'transparent',
            transform: `rotate(${rotation}deg)`,
          }}
        />
        
        {/* Loading text */}
        <div 
          className="text-2xl font-semibold tracking-wider"
          style={{ color: textColor }}
        >
          Loading...
        </div>
        
        {/* Progress bar */}
        <div className="w-64 h-1 overflow-hidden bg-opacity-30" style={{ backgroundColor: textColor }}>
          <div
            className="h-full"
            style={{
              backgroundColor: textColor,
              width: `${Math.min(100, (frame / (duration * fps)) * 100)}%`,
            }}
          />
        </div>
      </div>
    </div>
  );
};

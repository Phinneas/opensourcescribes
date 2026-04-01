import { Sequence, useCurrentFrame, useVideoConfig, interpolate } from 'remotion';
import React from 'react';

export interface TypewriterOverlayProps {
  text: string;
  duration: number;
  delay?: number;
  position?: 'center' | 'bottom' | 'top';
  fontSize?: 'small' | 'medium' | 'large';
}

/**
 * Text overlay with typewriter effect
 * Features: character-by-character typing, customizable position and size
 */
export const TypewriterOverlay: React.FC<TypewriterOverlayProps> = ({
  text,
  duration,
  delay = 1.0,
  position = 'center',
  fontSize = 'medium',
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const delayFrames = Math.round(delay * fps);
  const startFrame = delayFrames;
  const durationFrames = Math.round(duration * fps);

  // Position styles
  const positionStyles = {
    center: 'top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2',
    bottom: 'bottom-12 left-1/2 -translate-x-1/2',
    top: 'top-12 left-1/2 -translate-x-1/2',
  };

  // Font size styles
  const fontSizeStyles = {
    small: 'text-2xl',
    medium: 'text-4xl',
    large: 'text-6xl',
  };

  // Fade animation
  const opacity = interpolate(frame, [startFrame, startFrame + 20, durationFrames - 20, durationFrames], [0, 1, 1, 0]);

  // Typing animation
  const typeDuration = 4.0; // Time to type entire text
  const progress = Math.min(1, Math.max(0, (frame - startFrame) / (typeDuration * fps)));
  const currentLength = Math.round(text.length * progress);

  // Cursor blink
  const cursorOpacity = 0.5 + 0.5 * Math.sin((frame - startFrame) / 3);

  return (
    <Sequence durationInFrames={durationFrames}>
      <div
        className={`absolute ${positionStyles[position]} px-8 py-6 bg-zinc-900/95 text-white rounded-2xl border border-zinc-700 shadow-2xl backdrop-blur-md max-w-3xl text-center`}
        style={{ opacity }}
      >
        <p className={`${fontSizeStyles[fontSize]} font-semibold bg-clip-text text-transparent bg-gradient-to-r from-white to-zinc-300 leading-relaxed`}>
          {text.substring(0, currentLength)}
          {frame < delayFrames + typeDuration * fps && (
            <span
              className="inline-block w-1 h-8 bg-white ml-1"
              style={{ opacity: cursorOpacity as number }}
            />
          )}
        </p>
      </div>
    </Sequence>
  );
};

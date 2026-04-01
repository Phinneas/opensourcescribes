import { Sequence, useCurrentFrame, useVideoConfig, interpolate, spring } from 'remotion';
import React from 'react';

export interface ProjectOverlayProps {
  name: string;
  url: string;
  description?: string;
  category?: string;
  lastUpdated?: string;
  duration: number;
  delay?: number; // Delay before overlay appears
}

/**
 * Main project info overlay component
 * Features: slide-in animation, gradient text, typewriter effect for URL, category tags
 */
export const ProjectOverlay: React.FC<ProjectOverlayProps> = ({
  name,
  url,
  description,
  category,
  lastUpdated,
  duration,
  delay = 1.0, // Default: overlay appears 1 second after video starts
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const delayFrames = Math.round(delay * fps);
  const startFrame = delayFrames;
  const durationFrames = Math.round(duration * fps);

  // Slide-in animation from left
  const translateX = spring({
    frame: frame - startFrame,
    fps,
    config: {
      damping: 15,
      mass: 0.5,
      stiffness: 80,
    },
    from: -300,
    to: 0,
  });

  // Fade animation
  const opacity = interpolate(frame, [startFrame, startFrame + 15, durationFrames - 15, durationFrames], [0, 1, 1, 0]);

  return (
    <Sequence durationInFrames={durationFrames}>
      <div
        className="absolute bottom-20 left-16 p-8 bg-zinc-900/95 text-white rounded-2xl border border-zinc-700 shadow-2xl backdrop-blur-md"
        style={{
          transform: `translateX(${translateX}px)`,
          opacity,
        }}
      >
        <div className="flex flex-col gap-3">
          {/* Category Tag */}
          {category && <CategoryTag category={category} />}
          
          {/* Project Name */}
          <h1 className="text-6xl font-extrabold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 via-teal-400 to-purple-500 leading-tight">
            {name}
          </h1>
          
          {/* URL with Typewriter Effect */}
          <TypewriterURL url={url} delay={delay + 0.5} />
          
          {/* Description */}
          {description && (
            <p className="text-xl text-zinc-300 mt-2 leading-relaxed max-w-2xl">
              {description}
            </p>
          )}
          
          {/* Last Updated */}
          {lastUpdated && (
            <div className="flex items-center gap-2 mt-3">
              <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
              <span className="text-sm text-zinc-400 font-mono">
                Last updated: {lastUpdated}
              </span>
            </div>
          )}
        </div>
      </div>
    </Sequence>
  );
};

/**
 * Category tag with slide-in animation
 */
const CategoryTag: React.FC<{ category: string }> = ({ category }) => {
  const frame = useCurrentFrame();

  const opacity = interpolate(frame, [0, 15], [0, 1], {
    extrapolateRight: 'clamp',
  });

  return (
    <div
      className="inline-block px-4 py-1.5 bg-gradient-to-r from-blue-600 to-purple-600 rounded-full text-sm font-semibold uppercase tracking-wider"
      style={{ opacity }}
    >
      {category}
    </div>
  );
};

/**
 * URL with typewriter effect
 */
const TypewriterURL: React.FC<{ url: string; delay: number }> = ({ url, delay }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const delayFrames = Math.round(delay * fps);
  const textLength = url.length;
  const typeDuration = 2.0; // Time to type the URL

  const currentLength = Math.min(
    textLength,
    Math.max(0, Math.round(interpolate(frame, [delayFrames, delayFrames + typeDuration * fps], [0, textLength])))
  );

  const cursorOpacity = interpolate(
    frame,
    [delayFrames + typeDuration * fps, delayFrames + typeDuration * fps + 10],
    [1, 0],
    { extrapolateRight: 'clamp' }
  );

  return (
    <div className="flex items-center gap-2">
      <div className="w-2 h-2 rounded-full bg-teal-400" />
      <pre className="text-lg text-zinc-300 font-mono tracking-tight">
        {url.substring(0, currentLength)}
        <span
          className="inline-block w-1.5 h-6 bg-white ml-0.5"
          style={{ opacity: cursorOpacity }}
        />
      </pre>
    </div>
  );
};

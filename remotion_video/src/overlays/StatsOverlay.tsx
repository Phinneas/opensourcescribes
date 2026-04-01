import { Sequence, useCurrentFrame, useVideoConfig, interpolate } from 'remotion';
import React from 'react';

export interface StatsOverlayProps {
  stars: number;
  forks: number;
  issues?: number;
  commits?: number;
  duration: number;
  delay?: number;
}

/**
 * Animated statistics overlay with counter animations and progress bars
 * Features: number counting animation, staggered fade-ins, animated progress bars
 */
export const StatsOverlay: React.FC<StatsOverlayProps> = ({
  stars,
  forks,
  issues = 0,
  commits = 0,
  duration,
  delay = 1.0,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const delayFrames = Math.round(delay * fps);
  const startFrame = delayFrames;
  const durationFrames = Math.round(duration * fps);

  // Main container fade-in
  const opacity = interpolate(frame, [startFrame, startFrame + 12], [0, 1], {
    extrapolateRight: 'clamp',
  });

  return (
    <Sequence durationInFrames={durationFrames}>
      <div
        className="absolute top-6 right-6 p-6 bg-zinc-900/95 text-white rounded-xl border border-zinc-700 shadow-2xl backdrop-blur-md min-w-64"
        style={{ opacity }}
      >
        <div className="flex flex-col gap-4">
          {/* Stars Counter */}
          <StatItem
            label="Stars"
            value={stars}
            color="from-yellow-400 to-orange-500"
            delay={delay + 0.1}
  duration={duration} />

          {/* Forks Counter */}
          <StatItem
            label="Forks"
            value={forks}
            color="from-blue-400 to-indigo-500"
            delay={delay + 0.3}
            duration={duration} />

          {/* Issues Counter (if available) */}
          {issues > 0 && (
            <StatItem
              label="Issues"
              value={issues}
              color="from-green-400 to-emerald-500"
              delay={delay + 0.5}
              duration={duration} />
          )}

          {/* Commits Counter (if available) */}
          {commits > 0 && (
            <StatItem
              label="Commits"
              value={commits}
              color="from-purple-400 to-pink-500"
              delay={delay + 0.7}
              duration={duration} />
          )}
        </div>
      </div>
    </Sequence>
  );
};

interface StatItemProps {
  label: string;
  value: number;
  color: string;
  delay: number;
  duration: number;
}

/**
 * Individual stat item with counter animation and progress bar
 */
const StatItem: React.FC<StatItemProps> = ({ label, value, color, delay, duration }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const startFrame = Math.round(delay * fps);

  // Counter animation
  const counterValue = interpolate(
    frame,
    [startFrame, startFrame + 60],
    [0, value],
    { extrapolateRight: 'clamp' }
  );

  // Fade-in
  const opacity = interpolate(frame, [startFrame, startFrame + 10], [0, 1], {
    extrapolateRight: 'clamp',
  });

  // Progress bar animation
  const progressWidth = interpolate(
    frame,
    [startFrame, startFrame + 40],
    [0, 100],
    { extrapolateRight: 'clamp' }
  ) as number;

  // Format number with commas
  const formattedValue = Math.floor(counterValue).toLocaleString();

  return (
    <div className="flex flex-col gap-2" style={{ opacity }}>
      {/* Label and Value */}
      <div className="flex items-baseline justify-between">
        <span className="text-sm font-semibold text-zinc-400 uppercase tracking-wide">{label}</span>
        <span className={`text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r ${color}`}>
          {formattedValue}
        </span>
      </div>

      {/* Progress Bar */}
      <div className="h-1.5 bg-zinc-800 rounded-full overflow-hidden">
        <div
          className={`h-full bg-gradient-to-r ${color} rounded-full transition-all`}
          style={{
            width: `${progressWidth}%`,
          }}
        />
      </div>
    </div>
  );
};

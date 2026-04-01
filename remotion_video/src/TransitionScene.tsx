import { AbsoluteFill, useCurrentFrame, useVideoConfig, spring, interpolate } from 'remotion';
import React from 'react';
import './index.css';

export interface TransitionSceneProps {
  style: 'wipe' | 'sweep' | 'flash';
}

/**
 * TransitionScene - Short (~1s) animated transition between segments
 * 
 * Options:
 * - Horizontal wipe with light streak
 * - Diagonal sweep
 * - Flash cut with brand color
 */
export const TransitionScene: React.FC<TransitionSceneProps> = ({ style }) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();

  const renderWipe = () => {
    const wipeX = interpolate(frame, [0, durationInFrames], [-1920, 1920], {
      extrapolateLeft: 'clamp',
      extrapolateRight: 'clamp'
    });

    const wipeOpacity = interpolate(frame, [0, 10, durationInFrames - 10, durationInFrames], [0, 1, 1, 0], {
      extrapolateLeft: 'clamp',
      extrapolateRight: 'clamp'
    });

    return (
      <>
        {/* Left side */}
        <AbsoluteFill style={{
          clipPath: `inset(0 ${1920 - wipeX}px 0 0)`,
          background: '#0a0a1a'
        }} />
        
        {/* Wipe edge with glow */}
        <div style={{
          position: 'absolute',
          left: wipeX,
          top: 0,
          width: '4px',
          height: '1080px',
          background: 'linear-gradient(180deg, transparent, #60a5fa, #a855f7, transparent)',
          opacity: wipeOpacity,
          boxShadow: '0 0 30px rgba(96, 165, 250, 0.8)',
          transform: `translateX(-50%)`
        }} />
      </>
    );
  };

  const renderSweep = () => {
    const sweepProgress = spring({
      frame,
      fps,
      config: { damping: 20, stiffness: 100 }
    });

    const angle = interpolate(sweepProgress, [0, 1], [45, 225]);
    const opacity = interpolate(frame, [0, 5, durationInFrames - 5, durationInFrames], [0, 0.9, 0.9, 0], {
      extrapolateLeft: 'clamp',
      extrapolateRight: 'clamp'
    });

    return (
      <div style={{
        position: 'absolute',
        width: '2700px',
        height: '200px',
        background: 'linear-gradient(90deg, transparent, #0a0a1a, transparent)',
        left: '-390px',
        top: '50%',
        transform: `translateY(-50%) rotate(${angle}deg)`,
        opacity: opacity,
        boxShadow: '0 0 50px rgba(96, 165, 250, 0.6)'
      }} />
    );
  };

  const renderFlash = () => {
    const flashIntensity = interpolate(
      frame,
      [0, durationInFrames * 0.3, durationInFrames * 0.7, durationInFrames],
      [0, 1, 1, 0],
      {
        extrapolateLeft: 'clamp',
        extrapolateRight: 'clamp'
      }
    );

    return (
      <AbsoluteFill style={{
        background: `radial-gradient(circle, rgba(96, 165, 250, ${flashIntensity}) 0%, rgba(168, 85, 247, ${flashIntensity * 0.8}) 50%, transparent 70%)`
      }} />
    );
  };

  return (
    <AbsoluteFill style={{
      background: '#0a0a1a'
    }}>
      {style === 'wipe' && renderWipe()}
      {style === 'sweep' && renderSweep()}
      {style === 'flash' && renderFlash()}
    </AbsoluteFill>
  );
};

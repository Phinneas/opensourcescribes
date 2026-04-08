import { AbsoluteFill, useCurrentFrame, useVideoConfig, spring, interpolate } from 'remotion';
import React from 'react';
import './index.css';

export interface IntroSceneProps {
  episodeTitle: string;
  channelName: string;
}

/**
 * IntroScene - Branded animated intro sequence (~6 seconds)
 * 
 * Design:
 * - Channel name/logo animates in (fade + slight upward drift)
 * - Episode title appears below with typewriter effect
 * - Background: dark gradient with subtle animated particle field
 * - Fully programmatic React animation — no external image dependency
 */
export const IntroScene: React.FC<IntroSceneProps> = ({ episodeTitle, channelName }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Channel name fade animation
  const channelOpacity = spring({
    frame,
    fps,
    config: { damping: 15, stiffness: 80 }
  });
  const channelY = interpolate(channelOpacity, [0, 1], [50, 0]);

  // Episode title typewriter effect
  const titleOpacity = spring({
    frame: frame - 30,
    fps,
    config: { damping: 12, stiffness: 70 }
  });

  // Particle animation (subtle floating circles)
  const particles = Array.from({ length: 20 }, (_, i) => {
    const size = 30 + Math.random() * 50;
    const x = Math.random() * 1920;
    const y = Math.random() * 1080;
    const speed = 0.5 + Math.random() * 1;
    const opacity = 0.1 + Math.random() * 0.2;

    return { id: i, size, x, y, speed, opacity };
  });

  return (
    <AbsoluteFill style={{
      background: 'linear-gradient(135deg, #0a0a1a 0%, #1a1a3a 50%, #0a0a2a 100%)',
      fontFamily: 'Inter, -apple-system, sans-serif'
    }}>
      {/* Animated particle field */}
      {particles.map(p => (
        <div
          key={p.id}
          style={{
            position: 'absolute',
            width: p.size,
            height: p.size,
            borderRadius: '50%',
            background: `rgba(100, 150, 255, ${p.opacity})`,
            left: p.x,
            top: p.y + (frame * p.speed) % 1080,
            filter: 'blur(8px)',
            opacity: channelOpacity
          }}
        />
      ))}

      {/* Grid overlay */}
      <AbsoluteFill style={{
        background: `
          linear-gradient(rgba(100, 150, 255, 0.03) 1px, transparent 1px),
          linear-gradient(90deg, rgba(100, 150, 255, 0.03) 1px, transparent 1px)
        `,
        backgroundSize: '50px 50px',
        opacity: channelOpacity
      }} />

      {/* Content container */}
      <AbsoluteFill style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        gap: '40px'
      }}>
        {/* Channel name */}
        <div style={{
          opacity: channelOpacity,
          transform: `translateY(${channelY}px)`,
          textAlign: 'center'
        }}>
          <h1 style={{
            fontSize: '64px',
            fontWeight: '700',
            background: 'linear-gradient(135deg, #60a5fa 0%, #a855f7 100%)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            margin: 0,
            letterSpacing: '-2px'
          }}>
            {channelName}
          </h1>
          <div style={{
            height: '4px',
            width: '200px',
            background: 'linear-gradient(90deg, transparent, #60a5fa, #a855f7, transparent)',
            margin: '20px auto 0',
            borderRadius: '2px'
          }} />
        </div>

        {/* Episode title */}
        <div style={{
          opacity: titleOpacity,
          transform: `translateY(${20}px)`,
          textAlign: 'center'
        }}>
          <p style={{
            fontSize: '32px',
            color: '#e0e7ff',
            margin: 0,
            fontWeight: '400',
            letterSpacing: '1px'
          }}>
            {episodeTitle}
          </p>
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

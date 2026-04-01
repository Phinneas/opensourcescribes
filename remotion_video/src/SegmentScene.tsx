import { AbsoluteFill, useCurrentFrame, useVideoConfig, spring, interpolate, staticFile } from 'remotion';
import React from 'react';
import './index.css';

export interface SegmentSceneProps {
  imagePath: string;
  projectName: string;
  stars: number;
  forks: number;
  language: string;
  topics: string[];
}

/**
 * SegmentScene - Animated segment with Seedream background and overlays
 * 
 * Design:
 * - Seedream image background with Ken Burns zoom/pan
 * - Project name overlaid (top-left or bottom-left)
 * - Stats bar (stars, forks, language) animates in
 * - Topic pill badges
 */
export const SegmentScene: React.FC<SegmentSceneProps> = ({
  imagePath,
  projectName,
  stars,
  forks,
  language,
  topics
}) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();

  // Ken Burns effect (slow scale 1.0 → 1.08)
  const scale = interpolate(frame, [0, durationInFrames], [1.0, 1.08], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp'
  });
  
  // Slight pan movement
  const translateX = interpolate(frame, [0, durationInFrames], [0, -30], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp'
  });
  
  const translateY = interpolate(frame, [0, durationInFrames], [0, 20], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp'
  });

  // Project name overlay fade-in
  const nameOpacity = spring({
    frame: frame - 15,
    fps,
    config: { damping: 12, stiffness: 70 }
  });
  const nameTranslateX = interpolate(nameOpacity, [0, 1], [500, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp'
  });

  // Stats bar slide-up
  const statsOpacity = spring({
    frame: frame - 30,
    fps,
    config: { damping: 15, stiffness: 80 }
  });
  const statsTranslateY = interpolate(statsOpacity, [0, 1], [100, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp'
  });

  // Topic badges staggered animation
  const topicBADGES = topics.slice(0, 4).map((topic, i) => {
    const badgeOpacity = spring({
      frame: frame - 60 - (i * 10),
      fps,
      config: { damping: 14, stiffness: 75 }
    });
    return { topic, opacity: badgeOpacity };
  });

  // Helper to format numbers
  const formatNumber = (num: number): string => {
    if (num >= 1000) {
      return `${(num / 1000).toFixed(1)}k`;
    }
    return num.toString();
  };

  return (
    <AbsoluteFill style={{
      background: '#0a0a1a',
      fontFamily: 'Inter, -apple-system, sans-serif'
    }}>
      {/* Seedream background with Ken Burns */}
      <AbsoluteFill style={{
        overflow: 'hidden'
      }}>
        <img
          src={staticFile(imagePath)}
          style={{
            width: '1920px',
            height: '1080px',
            objectFit: 'cover',
            transform: `scale(${scale}) translate(${translateX}px, ${translateY}px)`,
            opacity: 0.85
          }}
          alt={projectName}
        />

        {/* Dark gradient overlay for text readability */}
        <AbsoluteFill style={{
          background: 'linear-gradient(180deg, rgba(10, 10, 26, 0.3) 0%, rgba(10, 10, 26, 0.7) 50%, rgba(10, 10, 26, 0.9) 100%)'
        }} />
      </AbsoluteFill>

      {/* Project name overlay */}
      <div style={{
        position: 'absolute',
        left: '60px',
        bottom: '280px',
        opacity: nameOpacity,
        transform: `translateX(${nameTranslateX}px)`
      }}>
        <h1 style={{
          fontSize: '56px',
          fontWeight: '700',
          color: '#ffffff',
          margin: 0,
          lineHeight: '1.1',
          textShadow: '0 4px 20px rgba(0, 0, 0, 0.8)'
        }}>
          {projectName}
        </h1>
      </div>

      {/* Stats bar */}
      <div style={{
        position: 'absolute',
        left: '60px',
        bottom: '60px',
        opacity: statsOpacity,
        transform: `translateY(${statsTranslateY}px)`
      }}>
        <div style={{
          display: 'flex',
          gap: '24px',
          alignItems: 'center'
        }}>
          {/* Stars */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px'
          }}>
            <div style={{
              width: '28px',
              height: '28px',
              borderRadius: '50%',
              background: 'linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '16px'
            }}>
              ★
            </div>
            <span style={{
              fontSize: '28px',
              fontWeight: '600',
              color: '#ffffff'
            }}>
              {formatNumber(stars)}
            </span>
          </div>

          {/* Forks */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px'
          }}>
            <div style={{
              width: '28px',
              height: '28px',
              borderRadius: '50%',
              background: 'linear-gradient(135deg, #60a5fa 0%, #3b82f6 100%)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '16px'
            }}>
              ⑂
            </div>
            <span style={{
              fontSize: '28px',
              fontWeight: '600',
              color: '#ffffff'
            }}>
              {formatNumber(forks)}
            </span>
          </div>

          {/* Language */}
          {language && (
            <div style={{
              padding: '8px 20px',
              background: 'rgba(255, 255, 255, 0.15)',
              backdropFilter: 'blur(10px)',
              borderRadius: '20px',
              border: '1px solid rgba(255, 255, 255, 0.2)'
            }}>
              <span style={{
                fontSize: '24px',
                fontWeight: '500',
                color: '#e0e7ff'
              }}>
                {language}
              </span>
            </div>
          )}
        </div>

        {/* Topic badges */}
        {topicBADGES.length > 0 && (
          <div style={{
            display: 'flex',
            gap: '12px',
            marginTop: '20px',
            flexWrap: 'wrap',
            maxWidth: '800px'
          }}>
            {topicBADGES.map((badge, i) => (
              <div
                key={i}
                style={{
                  padding: '6px 16px',
                  background: 'linear-gradient(135deg, rgba(96, 165, 250, 0.2) 0%, rgba(168, 85, 247, 0.2) 100%)',
                  backdropFilter: 'blur(10px)',
                  borderRadius: '16px',
                  border: '1px solid rgba(100, 150, 255, 0.3)',
                  opacity: badge.opacity
                }}
              >
                <span style={{
                  fontSize: '18px',
                  fontWeight: '500',
                  color: '#c4b5fd'
                }}>
                  {badge.topic}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </AbsoluteFill>
  );
};

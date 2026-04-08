import {
  AbsoluteFill,
  useCurrentFrame,
  useVideoConfig,
  spring,
  interpolate,
  staticFile,
  Sequence,
} from 'remotion';
import React from 'react';
import './index.css';

export interface SegmentSceneProps {
  screenshotPath: string;   // full-page GitHub screenshot filename (in public/)
  projectName: string;
  description: string;
  stars: number;
  forks: number;
  language: string;
  topics: string[];
  // Timing overrides (seconds) — defaults match config.json segment_duration=42
  titleDuration?: number;   // default 4s
  zoomInDuration?: number;  // default 2s
  zoomOutDuration?: number; // default 2s
}

const COLORS = {
  bg:        '#080c14',
  bgAlt:     '#0d1520',
  teal:      '#00d4ff',
  tealDim:   '#00a8c8',
  green:     '#00ff88',
  greenDim:  '#00cc6a',
  white:     '#ffffff',
  gray:      '#8899aa',
  gridLine:  'rgba(0, 212, 255, 0.06)',
  glow:      'rgba(0, 212, 255, 0.15)',
};

/** Format star/fork counts */
const fmt = (n: number): string =>
  n >= 1000 ? `${(n / 1000).toFixed(1)}k` : String(n);

// ---------------------------------------------------------------------------
// Title card — codestream aesthetic
// ---------------------------------------------------------------------------
const TitleCard: React.FC<{
  projectName: string;
  description: string;
  stars: number;
  forks: number;
  language: string;
  topics: string[];
  frame: number;
  fps: number;
}> = ({ projectName, description, stars, forks, language, topics, frame, fps }) => {

  const nameOpacity = spring({ frame: frame - 5, fps, config: { damping: 14, stiffness: 80 } });
  const nameX = interpolate(nameOpacity, [0, 1], [-80, 0], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });

  const descOpacity = spring({ frame: frame - 18, fps, config: { damping: 14, stiffness: 70 } });
  const statsOpacity = spring({ frame: frame - 28, fps, config: { damping: 14, stiffness: 70 } });

  return (
    <AbsoluteFill style={{ background: COLORS.bg, fontFamily: 'monospace, "Courier New"' }}>

      {/* Grid background */}
      <AbsoluteFill style={{
        backgroundImage: `
          linear-gradient(${COLORS.gridLine} 1px, transparent 1px),
          linear-gradient(90deg, ${COLORS.gridLine} 1px, transparent 1px)
        `,
        backgroundSize: '60px 60px',
      }} />

      {/* Top teal accent bar */}
      <div style={{
        position: 'absolute', top: 0, left: 0, right: 0, height: '3px',
        background: `linear-gradient(90deg, transparent, ${COLORS.teal}, ${COLORS.green}, transparent)`,
      }} />

      {/* Corner accents */}
      <div style={{
        position: 'absolute', top: '40px', left: '60px',
        width: '60px', height: '60px',
        borderTop: `2px solid ${COLORS.teal}`,
        borderLeft: `2px solid ${COLORS.teal}`,
        opacity: 0.6,
      }} />
      <div style={{
        position: 'absolute', bottom: '40px', right: '60px',
        width: '60px', height: '60px',
        borderBottom: `2px solid ${COLORS.green}`,
        borderRight: `2px solid ${COLORS.green}`,
        opacity: 0.6,
      }} />

      {/* Center glow */}
      <div style={{
        position: 'absolute',
        top: '50%', left: '50%',
        transform: 'translate(-50%, -50%)',
        width: '800px', height: '400px',
        background: `radial-gradient(ellipse, ${COLORS.glow} 0%, transparent 70%)`,
      }} />

      {/* Project name */}
      <div style={{
        position: 'absolute',
        top: '50%', left: '50%',
        transform: `translate(calc(-50% + ${nameX}px), -50%)`,
        opacity: nameOpacity,
        textAlign: 'center',
        width: '1600px',
        marginTop: '-80px',
      }}>
        {/* Prefix label */}
        <div style={{
          fontSize: '22px',
          letterSpacing: '8px',
          color: COLORS.teal,
          marginBottom: '16px',
          textTransform: 'uppercase',
          opacity: 0.8,
        }}>
          {'// open source'}
        </div>

        {/* Main name */}
        <h1 style={{
          fontSize: '96px',
          fontWeight: '900',
          color: COLORS.white,
          margin: 0,
          lineHeight: 1.0,
          letterSpacing: '-2px',
          textShadow: `0 0 40px ${COLORS.teal}44, 0 0 80px ${COLORS.teal}22`,
        }}>
          {projectName}
        </h1>

        {/* Teal underline */}
        <div style={{
          width: '200px', height: '2px',
          background: `linear-gradient(90deg, transparent, ${COLORS.teal}, transparent)`,
          margin: '24px auto',
          opacity: nameOpacity,
        }} />
      </div>

      {/* Description */}
      <div style={{
        position: 'absolute',
        top: '50%', left: '50%',
        transform: 'translate(-50%, calc(-50% + 120px))',
        opacity: descOpacity,
        textAlign: 'center',
        width: '1200px',
      }}>
        <p style={{
          fontSize: '32px',
          color: COLORS.gray,
          margin: 0,
          lineHeight: 1.5,
          fontFamily: 'Inter, -apple-system, sans-serif',
          fontWeight: '400',
        }}>
          {description}
        </p>
      </div>

      {/* Stats bar */}
      <div style={{
        position: 'absolute',
        bottom: '80px', left: '50%',
        transform: 'translateX(-50%)',
        opacity: statsOpacity,
        display: 'flex',
        gap: '48px',
        alignItems: 'center',
      }}>
        {/* Stars */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <span style={{ color: '#fbbf24', fontSize: '24px' }}>★</span>
          <span style={{ color: COLORS.white, fontSize: '28px', fontWeight: '600' }}>{fmt(stars)}</span>
          <span style={{ color: COLORS.gray, fontSize: '18px' }}>stars</span>
        </div>

        <div style={{ width: '1px', height: '30px', background: COLORS.gridLine }} />

        {/* Forks */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <span style={{ color: COLORS.teal, fontSize: '24px' }}>⑂</span>
          <span style={{ color: COLORS.white, fontSize: '28px', fontWeight: '600' }}>{fmt(forks)}</span>
          <span style={{ color: COLORS.gray, fontSize: '18px' }}>forks</span>
        </div>

        {language && (
          <>
            <div style={{ width: '1px', height: '30px', background: COLORS.gridLine }} />
            <div style={{
              padding: '8px 24px',
              border: `1px solid ${COLORS.teal}44`,
              borderRadius: '4px',
              background: `${COLORS.teal}11`,
            }}>
              <span style={{ color: COLORS.teal, fontSize: '22px', fontWeight: '500' }}>{language}</span>
            </div>
          </>
        )}

        {/* Topic badges */}
        {topics.slice(0, 3).map((t, i) => (
          <div key={i} style={{
            padding: '8px 20px',
            border: `1px solid ${COLORS.green}33`,
            borderRadius: '4px',
            background: `${COLORS.green}0a`,
          }}>
            <span style={{ color: COLORS.greenDim, fontSize: '18px' }}>{t}</span>
          </div>
        ))}
      </div>

      {/* Bottom accent bar */}
      <div style={{
        position: 'absolute', bottom: 0, left: 0, right: 0, height: '2px',
        background: `linear-gradient(90deg, transparent, ${COLORS.green}, ${COLORS.teal}, transparent)`,
      }} />
    </AbsoluteFill>
  );
};

// ---------------------------------------------------------------------------
// GitHub page scroll scene
// ---------------------------------------------------------------------------
const GitHubScroll: React.FC<{
  screenshotPath: string;
  projectName: string;
  frame: number;
  fps: number;
  durationInFrames: number;
  zoomInDuration: number;
  zoomOutDuration: number;
}> = ({ screenshotPath, projectName, frame, fps, durationInFrames, zoomInDuration, zoomOutDuration }) => {

  const zoomInFrames  = Math.round(zoomInDuration * fps);
  const zoomOutFrames = Math.round(zoomOutDuration * fps);
  const scrollFrames  = durationInFrames - zoomInFrames - zoomOutFrames;

  // Scale: start far (0.28), zoom to full (1.0), zoom back out (0.28)
  const scale = (() => {
    if (frame < zoomInFrames) {
      return interpolate(frame, [0, zoomInFrames], [0.28, 1.0], {
        extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
      });
    } else if (frame < zoomInFrames + scrollFrames) {
      return 1.0;
    } else {
      return interpolate(
        frame,
        [zoomInFrames + scrollFrames, durationInFrames],
        [1.0, 0.28],
        { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
      );
    }
  })();

  // Scroll Y: only moves during the scroll phase
  // Moves the image upward (negative translateY) to simulate scrolling down
  const scrollProgress = frame < zoomInFrames ? 0
    : frame > zoomInFrames + scrollFrames ? 1
    : (frame - zoomInFrames) / scrollFrames;

  // 2200px total scroll travel — enough to cover a typical GitHub page
  const translateY = interpolate(scrollProgress, [0, 1], [0, -2200], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
  });

  // Fade out page label during zoom out
  const labelOpacity = interpolate(
    frame,
    [zoomInFrames + scrollFrames - 10, zoomInFrames + scrollFrames + 15],
    [1, 0],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
  );

  return (
    <AbsoluteFill style={{ background: '#0d1117', overflow: 'hidden' }}>

      {/* GitHub page image */}
      <div style={{
        position: 'absolute',
        top: 0, left: 0,
        width: '100%',
        height: '100%',
        display: 'flex',
        alignItems: 'flex-start',
        justifyContent: 'center',
        transformOrigin: 'top center',
        transform: `scale(${scale}) translateY(${translateY}px)`,
      }}>
        <img
          src={staticFile(screenshotPath)}
          style={{
            width: '1920px',
            display: 'block',
          }}
          alt={projectName}
        />
      </div>

      {/* Subtle vignette edges */}
      <AbsoluteFill style={{
        background: `
          linear-gradient(to right, rgba(0,0,0,0.4) 0%, transparent 8%, transparent 92%, rgba(0,0,0,0.4) 100%)
        `,
        pointerEvents: 'none',
      }} />

      {/* Repo name watermark — bottom left during scroll */}
      <div style={{
        position: 'absolute',
        bottom: '32px', left: '48px',
        opacity: labelOpacity * (frame > zoomInFrames ? 1 : 0),
      }}>
        <span style={{
          fontFamily: 'monospace',
          fontSize: '20px',
          color: 'rgba(0, 212, 255, 0.5)',
          letterSpacing: '2px',
        }}>
          github.com › {projectName.toLowerCase()}
        </span>
      </div>
    </AbsoluteFill>
  );
};

// ---------------------------------------------------------------------------
// Main export
// ---------------------------------------------------------------------------
export const SegmentScene: React.FC<SegmentSceneProps> = ({
  screenshotPath,
  projectName,
  description,
  stars,
  forks,
  language,
  topics,
  titleDuration  = 4,
  zoomInDuration = 2,
  zoomOutDuration = 2,
}) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();

  const titleFrames  = Math.round(titleDuration * fps);
  const scrollFrames = durationInFrames - titleFrames;

  return (
    <AbsoluteFill>
      {/* Phase 1: Title card */}
      <Sequence from={0} durationInFrames={titleFrames}>
        <TitleCard
          projectName={projectName}
          description={description}
          stars={stars}
          forks={forks}
          language={language}
          topics={topics}
          frame={frame}
          fps={fps}
        />
      </Sequence>

      {/* Phase 2: GitHub scroll */}
      <Sequence from={titleFrames} durationInFrames={scrollFrames}>
        <GitHubScroll
          screenshotPath={screenshotPath}
          projectName={projectName}
          frame={frame - titleFrames}
          fps={fps}
          durationInFrames={scrollFrames}
          zoomInDuration={zoomInDuration}
          zoomOutDuration={zoomOutDuration}
        />
      </Sequence>
    </AbsoluteFill>
  );
};

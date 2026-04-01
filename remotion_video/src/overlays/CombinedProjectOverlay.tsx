import { useCurrentFrame, useVideoConfig, interpolate } from 'remotion';
import React from 'react';

export interface CombinedProjectOverlayProps {
  name: string;
  language: string;
  license: string;
  stars: number;
  forks: number;
  bullet1: string;
  bullet2: string;
  bullet3: string;
  duration: number;
}

const DISSOLVE_FRAMES = 18; // 0.75s at 24fps
const CPS = 70; // characters per second — fast "code streaming" feel

/**
 * Combined project overlay: terminal aesthetic, code-stream style.
 * Bottom-left: project name typewriter + language/license tags + 3 bullet points.
 * Top-right: animated star/fork counters.
 * Dissolves in over first 0.75s, dissolves out over last 0.75s.
 * Renders on a transparent background (composite via FFmpeg overlay filter).
 */
export const CombinedProjectOverlay: React.FC<CombinedProjectOverlayProps> = ({
  name,
  language,
  license,
  stars,
  forks,
  bullet1,
  bullet2,
  bullet3,
  duration,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const totalFrames = Math.round(duration * fps);

  // Master dissolve — both panels share this opacity envelope
  const opacity = interpolate(
    frame,
    [0, DISSOLVE_FRAMES, totalFrames - DISSOLVE_FRAMES, totalFrames],
    [0, 1, 1, 0],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
  );

  return (
    <div style={{ position: 'absolute', inset: 0, opacity }}>
      <TerminalPanel
        name={name}
        language={language}
        license={license}
        bullet1={bullet1}
        bullet2={bullet2}
        bullet3={bullet3}
        fps={fps}
      />
      <StatsPanel stars={stars} forks={forks} fps={fps} />
    </div>
  );
};

// ---------------------------------------------------------------------------
// Terminal panel — bottom-left
// ---------------------------------------------------------------------------

const TerminalPanel: React.FC<{
  name: string;
  language: string;
  license: string;
  bullet1: string;
  bullet2: string;
  bullet3: string;
  fps: number;
}> = ({ name, language, license, bullet1, bullet2, bullet3, fps }) => {
  const frame = useCurrentFrame();

  // Name types immediately after dissolve-in
  const nameStart = DISSOLVE_FRAMES;
  const nameDuration = Math.max(Math.round(fps * 0.4), Math.round((name.length / CPS) * fps));
  const nameChars = Math.min(
    name.length,
    Math.max(0, Math.floor(((frame - nameStart) / nameDuration) * name.length))
  );

  // Language/license tags fade in right after name finishes
  const tagsStart = nameStart + nameDuration;
  const tagsOpacity = interpolate(frame, [tagsStart, tagsStart + 10], [0, 1], {
    extrapolateRight: 'clamp',
  });

  // Bullet 1 starts after tags appear
  const b1Start = tagsStart + 10;
  const b1Duration = Math.max(Math.round(fps * 0.3), Math.round((bullet1.length / CPS) * fps));
  const b1Chars = Math.min(
    bullet1.length,
    Math.max(0, Math.floor(((frame - b1Start) / b1Duration) * bullet1.length))
  );

  // Bullet 2 starts after bullet 1 finishes
  const b2Start = b1Start + b1Duration;
  const b2Duration = Math.max(Math.round(fps * 0.3), Math.round((bullet2.length / CPS) * fps));
  const b2Chars = Math.min(
    bullet2.length,
    Math.max(0, Math.floor(((frame - b2Start) / b2Duration) * bullet2.length))
  );

  // Bullet 3 starts after bullet 2
  const b3Start = b2Start + b2Duration;
  const b3Duration = Math.max(Math.round(fps * 0.3), Math.round((bullet3.length / CPS) * fps));
  const b3Chars = Math.min(
    bullet3.length,
    Math.max(0, Math.floor(((frame - b3Start) / b3Duration) * bullet3.length))
  );

  // Block cursor blink (8 frames on, 8 off)
  const cursorVisible = frame % 16 < 8;
  const cursor = cursorVisible ? '█' : ' ';

  // Determine which line is currently being typed (for cursor placement)
  const typingName = frame >= nameStart && nameChars < name.length;
  const typingB1 = frame >= b1Start && b1Chars < bullet1.length;
  const typingB2 = frame >= b2Start && b2Chars < bullet2.length;
  const typingB3 = frame >= b3Start && b3Chars < bullet3.length;

  return (
    <div
      style={{
        position: 'absolute',
        bottom: 56,
        left: 56,
        maxWidth: 820,
        padding: '24px 32px',
        background: 'rgba(0, 8, 4, 0.90)',
        border: '1px solid rgba(0, 255, 140, 0.28)',
        borderRadius: 3,
        fontFamily: '"Courier New", Courier, monospace',
        boxShadow: '0 0 40px rgba(0, 255, 120, 0.10), 0 4px 24px rgba(0,0,0,0.6)',
      }}
    >
      {/* Project name with $ prompt */}
      <div
        style={{
          fontSize: 40,
          fontWeight: 'bold',
          color: '#00ff96',
          letterSpacing: 0.5,
          marginBottom: 10,
          lineHeight: 1.15,
        }}
      >
        <span style={{ color: '#00aaff', marginRight: 10 }}>$</span>
        {name.substring(0, nameChars)}
        {typingName && (
          <span style={{ color: '#00ff96', opacity: cursorVisible ? 1 : 0 }}>{cursor}</span>
        )}
      </div>

      {/* Language + License tags */}
      <div style={{ display: 'flex', gap: 8, marginBottom: 14, opacity: tagsOpacity }}>
        {language && language !== 'Unknown' && (
          <span
            style={{
              fontSize: 15,
              padding: '3px 11px',
              background: 'rgba(0, 170, 255, 0.12)',
              border: '1px solid rgba(0, 170, 255, 0.45)',
              borderRadius: 3,
              color: '#00aaff',
            }}
          >
            {language}
          </span>
        )}
        {license && license !== 'None' && license !== 'NOASSERTION' && (
          <span
            style={{
              fontSize: 15,
              padding: '3px 11px',
              background: 'rgba(0, 255, 140, 0.08)',
              border: '1px solid rgba(0, 255, 140, 0.35)',
              borderRadius: 3,
              color: '#00ff96',
            }}
          >
            {license}
          </span>
        )}
      </div>

      {/* Bullet 1 */}
      {bullet1 && (
        <BulletLine
          text={bullet1}
          chars={b1Chars}
          showCursor={typingB1}
          cursor={cursor}
          cursorVisible={cursorVisible}
        />
      )}

      {/* Bullet 2 — only render once b1 starts */}
      {bullet2 && b1Chars > 0 && (
        <BulletLine
          text={bullet2}
          chars={b2Chars}
          showCursor={typingB2}
          cursor={cursor}
          cursorVisible={cursorVisible}
        />
      )}

      {/* Bullet 3 — only render once b2 starts */}
      {bullet3 && b2Chars > 0 && (
        <BulletLine
          text={bullet3}
          chars={b3Chars}
          showCursor={typingB3}
          cursor={cursor}
          cursorVisible={cursorVisible}
        />
      )}
    </div>
  );
};

// ---------------------------------------------------------------------------
// Bullet line
// ---------------------------------------------------------------------------

const BulletLine: React.FC<{
  text: string;
  chars: number;
  showCursor: boolean;
  cursor: string;
  cursorVisible: boolean;
}> = ({ text, chars, showCursor, cursor, cursorVisible }) => (
  <div
    style={{
      fontSize: 19,
      color: '#aaffdd',
      marginBottom: 5,
      lineHeight: 1.45,
    }}
  >
    <span style={{ color: '#00ff96', marginRight: 8 }}>▸</span>
    {text.substring(0, chars)}
    {showCursor && (
      <span style={{ color: '#00ff96', opacity: cursorVisible ? 1 : 0 }}>{cursor}</span>
    )}
  </div>
);

// ---------------------------------------------------------------------------
// Stats panel — top-right
// ---------------------------------------------------------------------------

const StatsPanel: React.FC<{ stars: number; forks: number; fps: number }> = ({
  stars,
  forks,
  fps,
}) => {
  const frame = useCurrentFrame();
  const countStart = DISSOLVE_FRAMES;
  const countDuration = Math.round(fps * 2.0);

  const starsVal = Math.floor(
    interpolate(frame, [countStart, countStart + countDuration], [0, stars], {
      extrapolateRight: 'clamp',
    })
  );

  const forksVal = Math.floor(
    interpolate(
      frame,
      [countStart + Math.round(fps * 0.35), countStart + countDuration + Math.round(fps * 0.35)],
      [0, forks],
      { extrapolateRight: 'clamp' }
    )
  );

  return (
    <div
      style={{
        position: 'absolute',
        top: 56,
        right: 56,
        minWidth: 230,
        padding: '18px 26px',
        background: 'rgba(0, 8, 4, 0.90)',
        border: '1px solid rgba(0, 255, 140, 0.28)',
        borderRadius: 3,
        fontFamily: '"Courier New", Courier, monospace',
        boxShadow: '0 0 40px rgba(0, 255, 120, 0.10), 0 4px 24px rgba(0,0,0,0.6)',
      }}
    >
      <StatRow icon="★" label="stars" value={starsVal.toLocaleString()} color="#ffd700" />
      <StatRow icon="⑂" label="forks" value={forksVal.toLocaleString()} color="#00aaff" />
    </div>
  );
};

const StatRow: React.FC<{
  icon: string;
  label: string;
  value: string;
  color: string;
}> = ({ icon, label, value, color }) => (
  <div
    style={{
      display: 'flex',
      alignItems: 'baseline',
      gap: 8,
      marginBottom: 10,
    }}
  >
    <span style={{ color, fontSize: 20 }}>{icon}</span>
    <span style={{ color: '#88ccaa', fontSize: 15, minWidth: 46 }}>{label}</span>
    <span
      style={{
        color,
        fontSize: 26,
        fontWeight: 'bold',
        marginLeft: 'auto',
        paddingLeft: 12,
      }}
    >
      {value}
    </span>
  </div>
);

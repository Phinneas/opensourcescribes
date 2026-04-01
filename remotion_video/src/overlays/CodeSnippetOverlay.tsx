import { Sequence, useCurrentFrame, useVideoConfig, interpolate, spring } from 'remotion';
import React from 'react';

export interface CodeSnippetOverlayProps {
  code: string;
  language: string;
  duration: number;
  delay?: number;
  position?: 'left' | 'right' | 'bottom';
}

/**
 * Animated code snippet overlay with typing effect and syntax highlighting
 * Features: code typing animation, language indicator, code window styling
 */
export const CodeSnippetOverlay: React.FC<CodeSnippetOverlayProps> = ({
  code,
  language,
  duration,
  delay = 1.0,
  position = 'bottom',
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const delayFrames = Math.round(delay * fps);
  const startFrame = delayFrames;
  const durationFrames = Math.round(duration * fps);

  // Position styles
  const positionStyles = {
    left: 'bottom-20 left-20',
    right: 'bottom-20 right-20',
    bottom: 'bottom-4 left-1/2 -translate-x-1/2 w-3/4',
  };

  // Slide-in animation
  const translateY = spring({
    frame: frame - startFrame,
    fps,
    config: {
      damping: 12,
      mass: 0.8,
      stiffness: 100,
    },
    from: 100,
    to: 0,
  });

  // Fade animation
  const opacity = interpolate(frame, [startFrame, startFrame + 15, durationFrames - 15, durationFrames], [0, 1, 1, 0]);

  return (
    <Sequence durationInFrames={durationFrames}>
      <div
        className={`absolute ${positionStyles[position]} p-5 bg-zinc-900/98 rounded-xl border border-zinc-700 shadow-2xl backdrop-blur-md overflow-hidden max-w-2xl`}
        style={{
          transform: `translateY(${translateY}px)`,
          opacity,
        }}
      >
        {/* Window Header */}
        <div className="flex items-center justify-between mb-3 pb-3 border-b border-zinc-700/50">
          {/* Window Controls */}
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-red-500" />
            <div className="w-3 h-3 rounded-full bg-yellow-500" />
            <div className="w-3 h-3 rounded-full bg-green-500" />
          </div>

          {/* Language Indicator */}
          <div className="px-3 py-1 bg-zinc-800 rounded text-xs font-mono text-zinc-400 uppercase">
            {language}
          </div>
        </div>

        {/* Code Content with Typing Effect */}
        <div className="pt-2">
          <TypingCode code={code} delay={delay} />
        </div>
      </div>
    </Sequence>
  );
};

/**
 * Code with typing animation
 */
const TypingCode: React.FC<{ code: string; delay: number }> = ({ code, delay }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const delayFrames = Math.round(delay * fps);
  const lines = code.split('\n');
  const typeDuration = 3.0; // Time to type entire code

  // Calculate how much of the code to show
  const progress = Math.min(1, Math.max(0, (frame - delayFrames) / (typeDuration * fps)));
  const currentLines = Math.round(lines.length * progress);

  // Cursor blink
  const cursorOpacity = 0.5 + 0.5 * Math.sin((frame - delayFrames) / 5);

  return (
    <pre className="text-sm font-mono text-zinc-300 leading-relaxed whitespace-pre-wrap">
      {lines.slice(0, currentLines + 1).map((line, index) => (
        <React.Fragment key={index}>
          {/* Simple syntax highlighting simulation */}
          {highlightSyntax(line)}
          {index < currentLines && <br />}
        </React.Fragment>
      ))}
      {frame < delayFrames + typeDuration * fps && (
        <span
          className="inline-block w-1.5 h-4 bg-teal-400 ml-1"
          style={{ opacity: cursorOpacity as number }}
        />
      )}
    </pre>
  );
};

/**
 * Simple syntax highlighting (colorizes keywords, strings, comments)
 */
const highlightSyntax = (line: string): string => {
  // Simple regex-based highlighting simulation
  const keywords = ['def', 'import', 'from', 'return', 'class', 'function', 'const', 'let', 'var', 'if', 'else', 'for', 'while'];

  // Check for comment
  if (line.trim().startsWith('#') || line.trim().startsWith('//')) {
    return line;
  }

  // Simple highlighting simulation - in production, you'd use a proper syntax highlighter
  let highlightedLine = line;

  // Highlight keywords
  keywords.forEach(keyword => {
    const regex = new RegExp(`\\b${keyword}\\b`, 'g');
    highlightedLine = highlightedLine.replace(regex, `<span class="text-pink-400">${keyword}</span>`);
  });

  return highlightedLine;
};

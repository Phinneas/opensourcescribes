import { interpolate, Video, useCurrentFrame, useVideoConfig, Series, staticFile } from 'remotion';
import React from 'react';
import './index.css';

export type ClipType = 'intro' | 'project' | 'subscribe' | 'outro';

export interface ClipDesc {
  src: string;
  durationInSeconds: number;
  type: ClipType;
  name: string;
  url: string;
}

export const MainComposition: React.FC<{ clips: ClipDesc[] }> = ({ clips }) => {
  const { fps } = useVideoConfig();

  // If we don't have clips yet, just render empty or placeholder
  if (!clips || clips.length === 0) {
    return (
      <div className="flex-1 bg-black flex items-center justify-center text-white text-4xl">
        Loading...
      </div>
    );
  }

  return (
    <Series>
      {clips.map((clip, idx) => {
        const durationInFrames = Math.max(1, Math.round(clip.durationInSeconds * fps));
        return (
          <Series.Sequence durationInFrames={durationInFrames} key={idx}>
            <ClipRenderer clip={clip} />
          </Series.Sequence>
        );
      })}
    </Series>
  );
};

const ClipRenderer: React.FC<{ clip: ClipDesc }> = ({ clip }) => {
  const frame = useCurrentFrame();

  // We fade in the video from black
  const opacity = interpolate(frame, [0, 15], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // A sleek lower-third style for projects
  return (
    <div className="flex-1 bg-black relative">
      <Video src={staticFile(clip.src)} style={{ opacity, width: '100%', height: '100%', objectFit: 'cover' }} />

      {clip.type === 'project' && clip.name && (
        <LowerThird name={clip.name} url={clip.url} />
      )}
    </div>
  );
};

const LowerThird: React.FC<{ name: string; url: string }> = ({ name, url }) => {
  const frame = useCurrentFrame();

  // Slide in from left
  const translateX = interpolate(frame, [0, 30], [-1000, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <div
      className="absolute bottom-16 left-16 p-8 bg-zinc-900/90 text-white rounded-xl border border-zinc-700 shadow-2xl backdrop-blur-md"
      style={{
        transform: `translateX(${translateX}px)`,
      }}
    >
      <div className="flex flex-col gap-2">
        <h1 className="text-5xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-purple-500">
          {name}
        </h1>
        <p className="text-2xl text-zinc-300 font-mono tracking-tight">{url}</p>
      </div>
    </div>
  );
};

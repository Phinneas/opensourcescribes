import { interpolate, Video, useCurrentFrame, useVideoConfig, Series, staticFile, Sequence } from 'remotion';
import React from 'react';
import './index.css';
import { IntroScene } from './IntroScene';
import { SegmentScene } from './SegmentScene';
import { TransitionScene } from './TransitionScene';

export type ClipType = 'intro' | 'project' | 'subscribe' | 'outro';

export interface ClipDesc {
  src: string;
  durationInSeconds: number;
  type: ClipType;
  name: string;
  url: string;
  img?: string;
  stats?: {
    stars?: number;
    forks?: number;
    language?: string;
    topics?: string[];
  };
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
            <ClipRenderer clip={clip} isFirstProject={clip.type === 'project' && idx === 1} />
          </Series.Sequence>
        );
      })}
    </Series>
  );
};

const ClipRenderer: React.FC<{ clip: ClipDesc; isFirstProject?: boolean }> = ({ clip, isFirstProject }) => {
  const frame = useCurrentFrame();

  // We fade in the video from black
  const opacity = interpolate(frame, [0, 15], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  if (clip.type === 'intro') {
    return (
      <div className="flex-1 bg-black relative" style={{ opacity }}>
        <Video src={staticFile(clip.src)} style={{ opacity: 0 }} volume={1} />
        <IntroScene channelName="OpenSourceScribes" episodeTitle="GitHub Roundup" />
      </div>
    );
  }

  if (clip.type === 'project') {
    return (
      <div className="flex-1 bg-black relative" style={{ opacity }}>
        <Video src={staticFile(clip.src)} style={{ opacity: 0 }} volume={1} />
        <SegmentScene
           screenshotPath={clip.img || clip.src || ''}
           projectName={clip.name}
           description={''}
           stars={clip.stats?.stars || 0}
           forks={clip.stats?.forks || 0}
           language={clip.stats?.language || "Open Source"}
           topics={clip.stats?.topics || []}
        />
        {/* Render transition wipe over the first 30 frames, but maybe skip if it's the very first project clip after intro */}
        {!isFirstProject && (
           <Sequence durationInFrames={30}>
             <TransitionScene style="wipe" />
           </Sequence>
        )}
      </div>
    );
  }

  // A sleek lower-third style for subscribe/outro clips
  return (
    <div className="flex-1 bg-black relative">
      <Video src={staticFile(clip.src)} style={{ opacity, width: '100%', height: '100%', objectFit: 'cover' }} />
    </div>
  );
};

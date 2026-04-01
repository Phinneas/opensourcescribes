import { AbsoluteFill } from 'remotion';
import React from 'react';
import './index.css';
import {
  ProjectOverlay,
  StatsOverlay,
  CodeSnippetOverlay,
  TypewriterOverlay,
  CombinedProjectOverlay,
} from './overlays';

export type OverlayType = 'project' | 'stats' | 'code' | 'typewriter' | 'combined';

export interface OverlayCompositionProps {
  overlayType: OverlayType;
  // Project overlay props
  name?: string;
  url?: string;
  description?: string;
  category?: string;
  lastUpdated?: string;
  // Stats overlay props
  stars?: number;
  forks?: number;
  issues?: number;
  commits?: number;
  // Code overlay props
  code?: string;
  language?: string;
  // Typewriter overlay props
  text?: string;
  // Combined overlay props (language reused from above)
  license?: string;
  bullet1?: string;
  bullet2?: string;
  bullet3?: string;
  // Common props
  duration: number;
  delay?: number;
  position?: 'left' | 'right' | 'bottom' | 'center' | 'top';
  fontSize?: 'small' | 'medium' | 'large';
}

/**
 * Main composition for generating standalone overlays.
 * Renders with transparent background so FFmpeg can composite over video.
 * Use --codec=vp8 when rendering for alpha-channel webm output.
 */
export const OverlayComposition: React.FC<OverlayCompositionProps> = (props) => {
  const { duration } = props;

  return (
    <AbsoluteFill style={{ backgroundColor: 'transparent' }}>

      {/* Combined terminal overlay — project name, language, license, stars, forks, bullets */}
      {props.overlayType === 'combined' && props.name && (
        <CombinedProjectOverlay
          name={props.name}
          language={props.language ?? ''}
          license={props.license ?? ''}
          stars={props.stars ?? 0}
          forks={props.forks ?? 0}
          bullet1={props.bullet1 ?? ''}
          bullet2={props.bullet2 ?? ''}
          bullet3={props.bullet3 ?? ''}
          duration={duration}
        />
      )}

      {/* Original single-purpose overlays kept intact */}
      {props.overlayType === 'project' && props.name && props.url && (
        <ProjectOverlay
          name={props.name}
          url={props.url}
          description={props.description}
          category={props.category}
          lastUpdated={props.lastUpdated}
          duration={duration}
          delay={props.delay}
        />
      )}

      {props.overlayType === 'stats' && props.stars !== undefined && props.forks !== undefined && (
        <StatsOverlay
          stars={props.stars}
          forks={props.forks}
          issues={props.issues}
          commits={props.commits}
          duration={duration}
          delay={props.delay}
        />
      )}

      {props.overlayType === 'code' && props.code && props.language && (
        <CodeSnippetOverlay
          code={props.code}
          language={props.language}
          duration={duration}
          delay={props.delay}
          position={props.position as 'left' | 'right' | 'bottom' || 'bottom'}
        />
      )}

      {props.overlayType === 'typewriter' && props.text && (
        <TypewriterOverlay
          text={props.text}
          duration={duration}
          delay={props.delay}
          position={props.position as 'center' | 'bottom' | 'top' || 'center'}
          fontSize={props.fontSize || 'medium'}
        />
      )}

    </AbsoluteFill>
  );
};

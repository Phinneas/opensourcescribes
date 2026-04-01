import { AbsoluteFill } from 'remotion';
import React from 'react';
import './index.css';
import { WipeTransition, ZoomTransition, DissolveTransition, LoaderTransition } from './transitions';

export type TransitionType = 'wipe' | 'zoom' | 'dissolve' | 'loader';

export interface TransitionCompositionProps {
  transitionType: TransitionType;
  duration: number;
  overlayColor?: string;
  direction?: 'left' | 'right' | 'up' | 'down';
  zoomIn?: boolean;
  textColor?: string;
}

/**
 * Main composition for generating standalone transition clips
 */
export const TransitionComposition: React.FC<TransitionCompositionProps> = (props) => {
  const { duration } = props;

  return (
    <AbsoluteFill style={{ backgroundColor: 'transparent' }}>
      {/* Render appropriate transition type */}
      {props.transitionType === 'wipe' && (
        <WipeTransition
          duration={duration}
          direction={props.direction || 'left'}
          overlayColor={props.overlayColor || '#1a1a2e'}
        />
      )}

      {props.transitionType === 'zoom' && (
        <ZoomTransition
          duration={duration}
          zoomIn={props.zoomIn !== undefined ? props.zoomIn : true}
          overlayColor={props.overlayColor || '#1a1a2e'}
        />
      )}

      {props.transitionType === 'dissolve' && (
        <DissolveTransition
          duration={duration}
          overlayColor={props.overlayColor || '#1a1a2e'}
        />
      )}

      {props.transitionType === 'loader' && (
        <LoaderTransition
          duration={duration}
          overlayColor={props.overlayColor || '#1a1a2e'}
          textColor={props.textColor || '#ffffff'}
        />
      )}
    </AbsoluteFill>
  );
};

import React from "react";
import "./index.css";
import { Composition } from "remotion";
import { MainComposition, ClipDesc } from "./Composition";
import { OverlayComposition, OverlayCompositionProps } from "./OverlayComposition";
import { TransitionComposition, TransitionCompositionProps } from "./TransitionComposition";
import { IntroScene, IntroSceneProps } from "./IntroScene";
import { SegmentScene, SegmentSceneProps } from "./SegmentScene";
import { TransitionScene, TransitionSceneProps } from "./TransitionScene";

// Default placeholder for dev preview
const defaultProps: { clips: ClipDesc[] } = {
  clips: [
    {
      src: "", // blank in dev mode unless loaded
      durationInSeconds: 3,
      type: "intro",
      name: "",
      url: "",
    }
  ],
};

const FPS = 30; // Updated to match video_settings.fps

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="Main"
        component={MainComposition}
        calculateMetadata={({ props }) => {
          let durationInFrames = 0;
          if (props.clips) {
            for (const clip of props.clips as ClipDesc[]) {
              durationInFrames += Math.max(1, Math.round(clip.durationInSeconds * FPS));
            }
          }
          return {
            durationInFrames: durationInFrames > 0 ? durationInFrames : FPS * 3,
            props,
          };
        }}
        defaultProps={defaultProps}
        fps={FPS}
        width={1920}
        height={1080}
      />

      {/* New OpenSourceScribes specific compositions */}
      <Composition
        id="IntroScene"
        component={IntroScene as unknown as React.FC<Record<string, unknown>>}
        calculateMetadata={({ props }) => {
          const introProps = props as unknown as IntroSceneProps;
          return {
            durationInFrames: FPS * 6, // 6 seconds
            props: introProps as unknown as Record<string, unknown>,
          };
        }}
        defaultProps={{
          episodeTitle: "GitHub Roundup",
          channelName: "OpenSourceScribes",
        } as unknown as Record<string, unknown>}
        fps={FPS}
        width={1920}
        height={1080}
      />

      <Composition
        id="SegmentScene"
        component={SegmentScene as unknown as React.FC<Record<string, unknown>>}
        calculateMetadata={({ props }) => {
          const segmentProps = props as unknown as SegmentSceneProps;
          return {
            durationInFrames: FPS * 8, // 8 seconds
            props: segmentProps as unknown as Record<string, unknown>,
          };
        }}
        defaultProps={{
          imagePath: "assets/wavespeed/example.png",
          projectName: "Example Project",
          stars: 1000,
          forks: 100,
          language: "TypeScript",
          topics: ["ai", "automation"],
        } as unknown as Record<string, unknown>}
        fps={FPS}
        width={1920}
        height={1080}
      />

      <Composition
        id="TransitionScene"
        component={TransitionScene as unknown as React.FC<Record<string, unknown>>}
        calculateMetadata={({ props }) => {
          const transitionProps = props as unknown as TransitionSceneProps;
          return {
            durationInFrames: FPS * 1, // 1 second
            props: transitionProps as unknown as Record<string, unknown>,
          };
        }}
        defaultProps={{
          style: "wipe" as "wipe" | "sweep" | "flash",
        } as unknown as Record<string, unknown>}
        fps={FPS}
        width={1920}
        height={1080}
      />

      {/* Legacy compositions for backward compatibility */}
      <Composition
        id="OverlayGenerator"
        component={OverlayComposition as unknown as React.FC<Record<string, unknown>>}
        calculateMetadata={({ props }) => {
          const overlayProps = props as unknown as OverlayCompositionProps;
          return {
            durationInFrames: Math.round(overlayProps.duration * FPS),
            props: overlayProps as unknown as Record<string, unknown>,
          };
        }}
        defaultProps={{
          overlayType: "project",
          name: "Example Project",
          url: "github.com/example/project",
          description: "This is a sample description",
          category: "Development",
          lastUpdated: "2026-03-08",
          duration: 6,
          delay: 1.0,
        } as unknown as Record<string, unknown>}
        fps={FPS}
        width={1920}
        height={1080}
      />
      <Composition
        id="TransitionGenerator"
        component={TransitionComposition as unknown as React.FC<Record<string, unknown>>}
        calculateMetadata={({ props }) => {
          const transitionProps = props as unknown as TransitionCompositionProps;
          return {
            durationInFrames: Math.round(transitionProps.duration * FPS),
            props: transitionProps as unknown as Record<string, unknown>,
          };
        }}
        defaultProps={{
          transitionType: "wipe",
          duration: 1.0,
          direction: "left",
          overlayColor: "#1a1a2e",
        } as unknown as Record<string, unknown>}
        fps={FPS}
        width={1920}
        height={1080}
      />
    </>
  );
};

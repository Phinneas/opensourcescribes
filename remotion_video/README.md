# Remotion Video Enhancement System

<p align="center">
  <a href="https://github.com/remotion-dev/logo">
    <picture>
      <source media="(prefers-color-scheme: dark)" srcset="https://github.com/remotion-dev/logo/raw/main/animated-logo-banner-dark.apng">
      <img alt="Animated Remotion Logo" src="https://github.com/remotion-dev/logo/raw/main/animated-logo-banner-light.gif">
    </picture>
  </a>
</p>

## Overview

This Remotion project provides animated overlay components for the OpenSourceScribes video pipeline. It generates professional-grade, animated graphical overlays that can be composited with FFmpeg-generated video segments.

**Purpose**: Enhance GitHub repository videos with animated statistics, code snippets, and project information overlays without using expensive AI video generation.

## Available Overlay Components

### 1. **ProjectOverlay** - Project Information Display
- Gradient text for project name
- Typewriter effect for GitHub URLs
- Category tags and last updated indicators
- Slide-in animations

### 2. **StatsOverlay** - Animated Statistics
- Number counting animations (0 → final value)
- Progress bars for metrics
- Color-coded stats (stars, forks, issues, commits)
- Staggered fade-in effects

### 3. **CodeSnippetOverlay** - Code Demonstrations
- macOS-style code window decoration
- Typing animation for code
- Language indicators
- Simple syntax highlighting

### 4. **TypewriterOverlay** - Text animations
- Character-by-character typing
- Blinking cursor effects
- Multiple positioning options
- Configurable font sizes

## Commands

**Install Dependencies**

```console
npm i
```

**Start Preview**

```console
npm run dev
```

**Render project overlay**
```console
npx remotion render OverlayGenerator \
  --props='{"overlayType":"project","name":"React","url":"github.com/facebook/react","duration":8,"delay":1.0}' \
  --output=assets/overlay_react.mp4
```

**Render stats overlay**
```console
npx remotion render OverlayGenerator \
  --props='{"overlayType":"stats","stars":180000,"forks":37000,"duration":6,"delay":1.0}' \
  --output=assets/overlay_react_stats.mp4
```

**Upgrade Remotion**

```console
npx remotion upgrade
```

## Integration with OpenSourceScribes Pipeline

These overlays are designed to work with the main video pipeline:

1. **Generate overlays** using Remotion CLI (automated via Python wrapper)
2. **Apply Ken Burns effect** to screenshots using FFmpeg
3. **Compose overlays** over animated videos using FFmpeg
4. **Concatenate segments** into final video with transitions

**Cost Benefits**: 100% free alternative to MiniMax overlay generation

## Component Documentation

Full documentation for each overlay component is available in [`src/overlays/README.md`](src/overlays/README.md)

## Docs

Get started with Remotion by reading the [fundamentals page](https://www.remotion.dev/docs/the-fundamentals).

## Help

We provide help on our [Discord server](https://discord.gg/6VzzNDwUwV).

## Issues

Found an issue with Remotion? [File an issue here](https://github.com/remotion-dev/remotion/issues/new).

## License

Note that for some entities a company license is needed. [Read the terms here](https://github.com/remotion-dev/remotion/blob/main/LICENSE.md).

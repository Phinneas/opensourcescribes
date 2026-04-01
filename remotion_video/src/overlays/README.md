# Remotion Overlay Components

## Overview

This directory contains React components designed to create animated overlays that can be composited over video segments in the OpenSourceScribes pipeline. These overlays provide enhanced visual information about GitHub repositories beyond static text.

## Component Types

### 1. ProjectOverlay (`ProjectOverlay.tsx`)

**Purpose**: Display comprehensive project information with animated elements

**Features**:
- Slide-in animation from left
- Gradient text effect for project name
- Typewriter effect for GitHub URL
- Category tag with fade-in animation
- Optional description text
- Last updated indicator with pulsing dot

**Props**:
```typescript
{
  name: string;           // Project name (required)
  url: string;            // GitHub URL (required)
  description?: string;   // Optional project description
  category?: string;      // Optional category tag
  lastUpdated?: string;   // Optional last updated date
  duration: number;       // Total overlay duration in seconds (required)
  delay?: number;         // Delay before overlay appears (default: 1.0s)
}
```

**Example Usage**:
```python
npx remotion render OverlayGenerator \
  --props='{"overlayType":"project","name":"React","url":"github.com/facebook/react","category":"JavaScript","duration":8,"delay":1.5}' \
  --output=assets/overlay_react.mp4
```

---

### 2. StatsOverlay (`StatsOverlay.tsx`)

**Purpose**: Display animated repository statistics with counter effects

**Features**:
- Number counting animation (0 → final value)
- Staggered fade-in for multiple stats
- Animated progress bars
- Color-coded metrics (stars=gold, forks=blue, issues=green, commits=purple)

**Props**:
```typescript
{
  stars: number;         // Star count (required)
  forks: number;         // Fork count (required)
  issues?: number;       // Optional issue count
  commits?: number;      // Optional commit count
  duration: number;      // Total overlay duration in seconds (required)
  delay?: number;        // Delay before overlay appears (default: 1.0s)
}
```

**Example Usage**:
```python
npx remotion render OverlayGenerator \
  --props='{"overlayType":"stats","stars":180000,"forks":37000,"duration":6,"delay":1.0}' \
  --output=assets/overlay_react_stats.mp4
```

---

### 3. CodeSnippetOverlay (`CodeSnippetOverlay.tsx`)

**Purpose**: Display animated code snippets with window decoration

**Features**:
- Code typing animation (character-by-character)
- macOS-style window controls
- Language indicator
- Simple syntax highlighting simulation
- Configurable positioning

**Props**:
```typescript
{
  code: string;          // Code content (required)
  language: string;      // Programming language (required)
  duration: number;      // Total overlay duration in seconds (required)
  delay?: number;        // Delay before overlay appears (default: 1.0s)
  position?: 'left' | 'right' | 'bottom';  // Overlay position (default: 'bottom')
}
```

**Example Usage**:
```python
npx remotion render OverlayGenerator \
  --props='{"overlayType":"code","code":"def hello():\n    print('Hello, World!')","language":"Python","duration":8,"position":"left"}' \
  --output=assets/overlay_code_demo.mp4
```

---

### 4. TypewriterOverlay (`TypewriterOverlay.tsx`)

**Purpose**: Display text with typewriter animation effect

**Features**:
- Character-by-character typing
- Blinking cursor animation
- Configurable sizing
- Multiple positioning options
- Gradient text effect

**Props**:
```typescript
{
  text: string;          // Text to display (required)
  duration: number;      // Total overlay duration in seconds (required)
  delay?: number;        // Delay before typing starts (default: 1.0s)
  position?: 'center' | 'bottom' | 'top';  // Text position (default: 'center')
  fontSize?: 'small' | 'medium' | 'large';  // Font size (default: 'medium')
}
```

**Example Usage**:
```python
npx remotion render OverlayGenerator \
  --props='{"overlayType":"typewriter","text":"Welcome to OpenSourceScribes!","duration":5,"position":"center","fontSize":"large"}' \
  --output=assets/overlay_welcome.mp4
```

---

## Integration with Python Pipeline

To use these overlays in the OpenSourceScribes video pipeline:

1. **Generate individual overlays** using a Python wrapper script (see `remotion_overlay_generator.py`)
2. **Composite overlays** over Ken Burns video segments using FFmpeg
3. **Timing overlay appearance** to match audio narration

---

## Common Configurations

### Standard Project Segment Overlay
```json
{
  "overlayType": "project",
  "duration": 8,
  "delay": 1.0
}
```

### Quick Stats Display
```json
{
  "overlayType": "stats",
  "duration": 5,
  "delay": 1.0
}
```

### Code Demonstration
```json
{
  "overlayType": "code",
  "duration": 10,
  "delay": 2.0,
  "position": "bottom"
}
```

### Transition Text
```json
{
  "overlayType": "typewriter",
  "duration": 4,
  "delay": 0.5,
  "position": "center"
}
```

---

## Visual Design Notes

- **Background**: Semi-transparent zinc-900 (95% opacity)
- **Borders**: Subtle zinc-700 borders for containment
- **Text**: White primary text with zinc-300 secondary
- **Gradients**: Blue-to-purple gradients for branding
- **Animations**: Spring physics for natural motion
- **Timing**: 1s fade-in, maintain visibility, 0.5s fade-out

---

## Performance Considerations

- Overlays render quickly (typically 1-2 seconds per overlay)
- PNG sequence export allows transparency compositing
- Can be pre-rendered and cached for reuse
- Remotion CLI handles background rendering efficiently

---

## Future Enhancements

Planned improvements for overlay components:
- [ ] Advanced syntax highlighting with proper parsers
- [ ] Network graph visualization
- [ ] Contribution history heatmaps
- [ ] Animated emojis for project features
- [ ] Real-time data fetching during render
- [ ] Custom color themes per category

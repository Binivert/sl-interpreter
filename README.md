<div align="center">

![SLIS System Banner](assets/header-banner.svg)

**Real-time sign language gesture recognition powered by MediaPipe and machine learning.**

Translate hand gestures into text and speech directly in your browser—no installation required.

</div>

![Divider](assets/divider-glow.svg)

## Screenshot

<div align="center">

<!-- SCREENSHOT PLACEHOLDER: Replace with actual application screenshot -->
<!-- Recommended: 1280x720 or 1920x1080 PNG/JPG -->
```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│                    [ SCREENSHOT HERE ]                          │
│                                                                 │
│              Application interface screenshot                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

</div>

![Divider](assets/divider-standard.svg)

![Section: Overview](assets/section-overview.svg)

## System Overview

SLIS captures video from your webcam, detects hands using MediaPipe's 21-landmark model, extracts geometric features from hand poses, and classifies gestures using either pre-trained MediaPipe models or custom KNN classifiers you train yourself.

Recognized gestures are displayed on screen and optionally spoken aloud using the Web Speech API. The entire system runs client-side in the browser with no server communication required.

| Aspect | Detail |
|:-------|:-------|
| **Input** | Webcam video stream (640×480) |
| **Detection** | MediaPipe HandLandmarker (21 points per hand) |
| **Classification** | MediaPipe GestureRecognizer or KNN (k=5) |
| **Output** | Text display + Text-to-Speech |
| **Storage** | IndexedDB for trained modules |
| **Deployment** | Single HTML file, zero dependencies |

![Divider](assets/divider-circuit.svg)

![Section: Features](assets/section-features.svg)

## Core Features

| Feature | Description |
|:--------|:------------|
| ![Icon](assets/icon-detection.svg) **Hand Detection** | Tracks up to 2 hands simultaneously with 21 landmarks each |
| ![Icon](assets/icon-gesture.svg) **Gesture Recognition** | Classifies hand poses into named gestures with confidence scores |
| ![Icon](assets/icon-training.svg) **Custom Training** | Train your own gestures by capturing samples directly in the UI |
| ![Icon](assets/icon-voice.svg) **Voice Output** | Speaks recognized gestures using system TTS voices |
| ![Icon](assets/icon-module.svg) **Module System** | Save, load, import, and export trained gesture modules |
| ![Icon](assets/icon-skeleton.svg) **Skeleton Overlay** | Visual feedback showing detected hand structure |
| ![Icon](assets/icon-settings.svg) **Adjustable Settings** | Configure confidence threshold, debounce timing, sensitivity |
| ![Icon](assets/icon-offline.svg) **Offline Capable** | Works without internet after initial model load |

![Divider](assets/divider-glow.svg)

![Section: How It Works](assets/section-howitworks.svg)

## How It Works

![Data Flow Diagram](assets/diagram-dataflow.svg)

### Processing Pipeline

Each video frame passes through these stages:

| Stage | Input | Output | Time |
|:------|:------|:-------|:-----|
| **Capture** | Webcam stream | RGB frame (640×480) | ~33ms |
| **Detection** | RGB frame | 21 landmarks × 2 hands | ~15ms |
| **Extraction** | Landmarks | 166-dim feature vector | <1ms |
| **Classification** | Features | Gesture label + confidence | <5ms |
| **Debounce** | Raw predictions | Filtered output | configurable |
| **Output** | Filtered gesture | UI update + TTS | immediate |

### Feature Vector Composition

The 166-dimensional feature vector contains:

| Component | Dimensions | Description |
|:----------|:-----------|:------------|
| Normalized XYZ | 63 | Wrist-centered coordinates for 21 landmarks |
| Finger angles | 5 | Curl angle for each finger |
| Fingertip distances | 5 | Distance from wrist to each fingertip |
| Inter-finger distances | 10 | Pairwise distances between fingertips |
| Second hand | 83 | Same features (zero-padded if absent) |

![Divider](assets/divider-standard.svg)

![Section: Structure](assets/section-structure.svg)

## System Structure

![Components Diagram](assets/diagram-components.svg)

### Core Components

| Component | Responsibility |
|:----------|:---------------|
| **SLISApp** | Main application controller, coordinates all subsystems |
| **ModuleDB** | IndexedDB wrapper for persistent module storage |
| **KNNClassifier** | K-nearest neighbors implementation for custom gestures |
| **FeatureExtractor** | Converts landmarks to normalized feature vectors |
| **MediaPipe** | Hand detection and pre-trained gesture recognition |

### Training Workflow

![Training Diagram](assets/diagram-training.svg)

| Step | Action | Recommendation |
|:-----|:-------|:---------------|
| 1 | Create new module | Give it a descriptive name |
| 2 | Add gesture | Enter gesture name (e.g., "Hello") |
| 3 | Capture samples | Press SPACE to record, aim for 50+ samples |
| 4 | Vary your pose | Different angles, distances, lighting |
| 5 | Repeat for each gesture | More gestures = richer vocabulary |
| 6 | Finish training | Module saves to IndexedDB automatically |

![Divider](assets/divider-circuit.svg)

![Section: Installation](assets/section-installation.svg)

## Installation & File Structure

```bash
# Clone or download the repository
git clone https://github.com/your-repo/slis.git
cd slis

# No build step required - open directly
open index.html

# Or serve locally for development
python -m http.server 8000
# Then visit http://localhost:8000
```

### Project Structure

```
slis/
├── index.html          # Complete application (single file)
├── README.md           # This documentation
└── assets/             # Optional: exported modules, screenshots
    ├── *.task          # MediaPipe gesture recognizer models
    └── *.json          # Exported trained modules
```

### Requirements

| Requirement | Minimum |
|:------------|:--------|
| Browser | Chrome 90+, Edge 90+, Firefox 90+ |
| Camera | Any webcam |
| Internet | Required only for initial model download |

![Divider](assets/divider-glow.svg)

![Section: Demo](assets/section-demo.svg)

## Demo

<div align="center">

<!-- VIDEO PLACEHOLDER: Replace with actual demo video -->
<!-- Recommended: MP4/WebM embed or YouTube/Vimeo link -->
```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│                    [ DEMO VIDEO HERE ]                          │
│                                                                 │
│              Embed video or link to demonstration               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

</div>

![Divider](assets/divider-standard.svg)

<div align="center">

![Footer](assets/footer.svg)

</div>

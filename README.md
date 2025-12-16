<div align="center">

![SLIS Header](assets/header.svg)

**AI-powered real-time sign language recognition using computer vision and machine learning.**

Transform hand gestures into text and speech directly in your browser — no server required, no data leaves your device.

</div>

---

## System Overview

The Sign Language Interpretation System (SLIS) is a browser-based application that interprets sign language gestures in real-time. Using your webcam, it detects hand positions, extracts geometric features from 21 landmark points per hand, and classifies gestures using machine learning.

**Two Recognition Modes:**

| Mode | Description |
|:-----|:------------|
| **Pre-trained** | MediaPipe's GestureRecognizer for common ASL gestures |
| **Custom-trained** | K-Nearest Neighbors classifier you train with your own samples |

All processing happens locally using WebAssembly and WebGL acceleration. No account required.

### Screenshot

<div align="center">

<!-- INSERT APPLICATION SCREENSHOT HERE -->
<!-- Recommended: 1280x720 or 1920x1080 PNG/JPG showing the main interface -->
`[ Application Screenshot Placeholder ]`

</div>

---

![Divider](assets/divider.svg)

## Core Features

| Feature | Icon | Description |
|:--------|:----:|:------------|
| **Hand Detection** | ![Detection](assets/icon-detection.svg) | Tracks up to 2 hands simultaneously, extracting 21 3D landmark points per hand at 30+ FPS using MediaPipe |
| **Gesture Recognition** | ![Recognition](assets/icon-recognition.svg) | Classifies hand poses with confidence scoring, temporal smoothing, and debounce filtering to prevent flickering |
| **Voice Output** | ![Voice](assets/icon-voice.svg) | Converts recognized gestures to speech using the Web Speech API with configurable voice settings |
| **Custom Training** | ![Training](assets/icon-training.svg) | Train your own gestures by capturing samples directly in the browser — no coding or external tools required |
| **Persistent Storage** | ![Storage](assets/icon-storage.svg) | Saves trained models and settings to IndexedDB, preserving your data across browser sessions |
| **Adaptive Interface** | ![Interface](assets/icon-interface.svg) | Resizable split-panel layout with draggable divider, skeleton overlay toggle, and responsive design |

---

![Divider](assets/divider.svg)

## How It Works

![Data Pipeline](assets/diagram-pipeline.svg)

### Processing Pipeline Explained

The system processes video frames through six sequential stages:

**Stage 1: Capture**
The webcam captures RGB video frames at approximately 30 frames per second. Each frame is passed to the detection stage.

**Stage 2: Detect**
MediaPipe HandLandmarker (running as a WebAssembly module with WebGL acceleration) identifies hands in the frame and extracts 21 3D landmark points per hand. These landmarks represent key positions: wrist, thumb joints, finger joints, and fingertips.

**Stage 3: Extract**
Raw landmarks are transformed into a normalized, rotation-invariant 166-dimensional feature vector:

| Component | Dimensions | Purpose |
|:----------|:-----------|:--------|
| Normalized coordinates | 63 per hand | Wrist-centered XYZ positions for all 21 landmarks |
| Finger angles | 5 per hand | Bend angle of each finger (thumb through pinky) |
| Fingertip distances | 5 per hand | Distance from each fingertip to the wrist |
| Inter-finger distances | 10 per hand | Pairwise distances between all fingertips |

**Stage 4: Classify**
The feature vector is compared against stored training examples using K-Nearest Neighbors (k=5) with inverse distance weighting. The algorithm finds the 5 most similar stored gestures and votes on the classification.

**Stage 5: Filter**
Results pass through confidence threshold and temporal debounce filters. This prevents rapid flickering between gestures and ensures only confident predictions are shown.

**Stage 6: Output**
The recognized gesture is displayed as text and optionally spoken using the Web Speech API.

### Processing Performance

| Metric | Value |
|:-------|:------|
| Frame rate | ~30 FPS |
| Detection latency | 15-25ms |
| Total pipeline latency | 30-50ms |
| Hands tracked | Up to 2 simultaneously |

---

![Divider](assets/divider.svg)

## System Components

![Architecture Diagram](assets/diagram-architecture.svg)

### Core Components

| Component | Responsibility |
|:----------|:---------------|
| **SLISApp** | Main application controller managing state, camera lifecycle, UI coordination, and event handling |
| **MediaPipe HandLandmarker** | WebAssembly module for real-time hand detection and landmark extraction with WebGL acceleration |
| **FeatureExtractor** | Transforms raw landmark data into normalized, rotation-invariant feature vectors |
| **KNNClassifier** | K-Nearest Neighbors classifier (k=5) with inverse distance weighting for gesture classification |
| **GestureRecognizer** | MediaPipe's pre-trained model for common ASL signs (fallback mode) |
| **ModuleDB** | IndexedDB wrapper providing persistent storage for trained models and configuration |
| **SpeechSynthesis** | Web Speech API interface for text-to-speech output with voice selection |

### Data Flow Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Webcam    │────▶│  MediaPipe  │────▶│  Features   │
│   Input     │     │  Detection  │     │  Extractor  │
└─────────────┘     └─────────────┘     └──────┬──────┘
                                               │
                    ┌─────────────┐     ┌──────▼──────┐
                    │   Speech    │◀────│     KNN     │
                    │   Output    │     │  Classifier │
                    └─────────────┘     └──────┬──────┘
                                               │
                                        ┌──────▼──────┐
                                        │  ModuleDB   │
                                        │  (Storage)  │
                                        └─────────────┘
```

---

![Divider](assets/divider.svg)

## Installation

### Pre-requirements

| Requirement | Specification |
|:------------|:--------------|
| Browser | Chrome 90+, Edge 90+, Firefox 100+ |
| Hardware | Webcam, WebGL 2.0 support |
| Permissions | Camera access |
| Storage | ~50MB for models and data |

### Setup

```bash
# No build process required — single HTML file application

# Option 1: Direct file access
# Open index.html in a modern browser

# Option 2: Local development server (Python)
python -m http.server 8000
# Navigate to http://localhost:8000

# Option 3: Local development server (Node.js)
npx serve .
# Navigate to the displayed URL

# Option 4: Using the optional Python backend
pip install -r requirements.txt
uvicorn src.server:app --reload
```

### Quick Start

1. Open `index.html` in Chrome or Edge
2. Allow camera access when prompted
3. Position your hand in front of the webcam
4. Watch real-time gesture recognition in action

---

![Divider](assets/divider.svg)

## Usage

![Usage Diagram](assets/diagram-usage.svg)

### Recognition Mode

The main interface displays your webcam feed with an overlay showing detected hand landmarks. Recognized gestures appear as text below the video, and can be spoken aloud.

**Controls:**
- **Toggle Skeleton**: Show/hide the hand landmark overlay
- **Toggle Voice**: Enable/disable speech output
- **Voice Selection**: Choose from available system voices

### Training Mode

Create custom gestures by capturing training samples:

1. **Enter gesture name** in the training panel
2. **Position your hand** to show the gesture
3. **Click "Capture"** to record a sample (capture 10-20 samples per gesture)
4. **Repeat** with variations in hand position and angle
5. **Test** your gesture in recognition mode

**Training Tips:**
- Capture samples with slight variations in position and rotation
- Use consistent lighting conditions
- Include samples from different distances
- Minimum 5 samples per gesture, recommended 15-20

### Model Management

| Action | Description |
|:-------|:------------|
| **Save Model** | Exports trained gestures to a downloadable JSON file |
| **Load Model** | Imports a previously saved model file |
| **Clear Model** | Removes all trained gestures from memory |
| **Reset** | Clears current session and reloads defaults |

---

![Divider](assets/divider.svg)

## File Structure

| Path | Description |
|:-----|:------------|
| `index.html` | Complete application (HTML + CSS + JS) — single file, no build required |
| `requirements.txt` | Optional Python backend dependencies |
| `src/` | Optional Python server modules |
| `src/__init__.py` | Package initialization with version info |
| `readme/` | Documentation and assets |
| `readme/readme.md` | This documentation file |
| `readme/assets/` | SVG diagrams and icons |

### Technology Stack

| Layer | Technology |
|:------|:-----------|
| Frontend | Vanilla HTML5, CSS3, JavaScript (ES6+) |
| Hand Detection | MediaPipe HandLandmarker (WebAssembly + WebGL) |
| Classification | Custom KNN implementation |
| Storage | IndexedDB |
| Speech | Web Speech API |
| Backend (optional) | FastAPI, Uvicorn |

---

![Divider](assets/divider.svg)

## Demonstration

<div align="center">

<!-- INSERT DEMO VIDEO HERE -->
<!-- Recommended: MP4/WebM, 30-60 seconds, showing gesture recognition in action -->
`[ Demo Video Placeholder ]`

*Video demonstration showing real-time gesture recognition and custom training workflow*

</div>

---

![Footer](assets/footer.svg)

/**
 * SLIS - Sign Language Interpretation System
 * Main Application v2.0
 * 
 * Browser-only implementation using MediaPipe Tasks Vision
 */

import {
    GestureRecognizer,
    FilesetResolver,
    DrawingUtils
} from "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.3";

// ============================================
// Application State
// ============================================
const APP = {
    // Elements
    video: null,
    canvas: null,
    ctx: null,
    drawingUtils: null,
    
    // Camera
    stream: null,
    isRunning: false,
    isMirrored: true,
    
    // Recognition
    gestureRecognizer: null,
    lastVideoTime: -1,
    results: null,
    
    // Models
    models: [],
    currentModel: null,
    
    // Settings
    showSkeleton: true,
    confidenceThreshold: 0.5,
    maxHands: 2,
    speakDelay: 1000,
    
    // Voice
    voices: [],
    selectedVoice: null,
    voiceRate: 1.0,
    voicePitch: 1.0,
    autoSpeak: false,
    lastSpoken: null,
    speakTimeout: null,
    
    // Sentence
    sentence: [],
    
    // Capture
    captures: [],
    gestureName: '',
    
    // Performance
    fps: 0,
    frameCount: 0,
    lastFpsTime: 0,
    
    // Debug
    debugMinimized: false
};

// ============================================
// Logging & Notifications
// ============================================
function log(type, message, data = null) {
    const time = new Date().toLocaleTimeString('en-US', { hour12: false });
    const logEl = document.getElementById('debug-log');
    
    // Console
    const fn = type === 'error' ? console.error : type === 'warn' ? console.warn : console.log;
    fn(`[${type.toUpperCase()}] ${message}`, data ?? '');
    
    // UI
    if (logEl) {
        const entry = document.createElement('div');
        entry.className = 'debug-entry';
        entry.innerHTML = `
            <span class="debug-time">${time}</span>
            <span class="debug-type ${type}">${type}</span>
            <span class="debug-msg">${message}${data ? ' → ' + (typeof data === 'object' ? JSON.stringify(data) : data) : ''}</span>
        `;
        logEl.appendChild(entry);
        logEl.scrollTop = logEl.scrollHeight;
        
        // Limit entries
        while (logEl.children.length > 150) {
            logEl.removeChild(logEl.firstChild);
        }
    }
}

function toast(title, message, type = 'info') {
    const container = document.getElementById('toast-container');
    const icons = { success: '✓', error: '✗', warning: '⚠', info: 'ℹ' };
    
    const el = document.createElement('div');
    el.className = `toast ${type}`;
    el.innerHTML = `
        <span class="toast-icon">${icons[type]}</span>
        <div class="toast-content">
            <div class="toast-title">${title}</div>
            <div class="toast-message">${message}</div>
        </div>
        <button class="toast-close" onclick="this.parentElement.remove()">×</button>
    `;
    
    container.appendChild(el);
    setTimeout(() => el.remove(), 4000);
}

function updateStatus(id, active) {
    const el = document.getElementById(id);
    if (el) el.classList.toggle('active', active);
}

// ============================================
// Model Management
// ============================================
async function initializeVision() {
    log('info', 'Initializing MediaPipe Vision...');
    try {
        const vision = await FilesetResolver.forVisionTasks(
            "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.3/wasm"
        );
        log('success', 'MediaPipe Vision initialized');
        return vision;
    } catch (err) {
        log('error', 'Failed to initialize Vision', err.message);
        throw err;
    }
}

async function loadModel(modelPath, modelName) {
    log('info', `Loading model: ${modelName}`);
    document.getElementById('model-status-text').textContent = 'Loading...';
    document.getElementById('model-status-text').classList.remove('loaded');
    
    try {
        // Close existing
        if (APP.gestureRecognizer) {
            APP.gestureRecognizer.close();
            APP.gestureRecognizer = null;
        }
        
        const vision = await initializeVision();
        
        APP.gestureRecognizer = await GestureRecognizer.createFromOptions(vision, {
            baseOptions: {
                modelAssetPath: modelPath,
                delegate: "GPU"
            },
            runningMode: "VIDEO",
            numHands: APP.maxHands
        });
        
        APP.currentModel = modelName;
        
        // Update UI
        document.getElementById('current-model-name').textContent = modelName;
        document.getElementById('model-status-text').textContent = 'Ready';
        document.getElementById('model-status-text').classList.add('loaded');
        updateStatus('status-model', true);
        
        toast('Model Loaded', `${modelName} is ready`, 'success');
        log('success', `Model loaded: ${modelName}`);
        
        return true;
    } catch (err) {
        log('error', 'Model load failed', err.message);
        document.getElementById('model-status-text').textContent = 'Error';
        toast('Model Error', err.message, 'error');
        updateStatus('status-model', false);
        return false;
    }
}

async function loadDefaultModel() {
    const url = "https://storage.googleapis.com/mediapipe-models/gesture_recognizer/gesture_recognizer/float16/1/gesture_recognizer.task";
    await loadModel(url, "MediaPipe Default");
}

async function handleModelFile(file) {
    if (!file.name.endsWith('.task')) {
        toast('Invalid File', 'Please select a .task file', 'error');
        return;
    }
    
    log('info', `Uploading model: ${file.name}`);
    
    const url = URL.createObjectURL(file);
    const name = file.name.replace('.task', '');
    
    // Add to list
    APP.models.push({ name, url, file });
    updateModelList();
    
    // Load it
    await loadModel(url, name);
}

function updateModelList() {
    const list = document.getElementById('model-list');
    list.innerHTML = '';
    
    APP.models.forEach((m, i) => {
        const el = document.createElement('div');
        el.className = `model-item ${m.name === APP.currentModel ? 'active' : ''}`;
        el.innerHTML = `
            <span>${m.name}</span>
            <div>
                <button class="btn btn-tiny" onclick="window.SLIS.switchModel(${i})">Load</button>
                <button class="btn btn-tiny btn-danger" onclick="window.SLIS.removeModel(${i})">×</button>
            </div>
        `;
        list.appendChild(el);
    });
}

// Expose to window for onclick handlers
window.SLIS = {
    switchModel: async (i) => {
        const m = APP.models[i];
        if (m) {
            await loadModel(m.url, m.name);
            updateModelList();
        }
    },
    removeModel: (i) => {
        const m = APP.models[i];
        if (m) {
            URL.revokeObjectURL(m.url);
            APP.models.splice(i, 1);
            updateModelList();
            log('info', `Removed model: ${m.name}`);
        }
    }
};

// ============================================
// Camera
// ============================================
async function startCamera() {
    log('info', 'Starting camera...');
    
    try {
        APP.stream = await navigator.mediaDevices.getUserMedia({
            video: { width: { ideal: 1280 }, height: { ideal: 720 }, facingMode: 'user' }
        });
        
        APP.video.srcObject = APP.stream;
        await APP.video.play();
        
        // Setup canvas
        APP.canvas.width = APP.video.videoWidth;
        APP.canvas.height = APP.video.videoHeight;
        APP.ctx = APP.canvas.getContext('2d');
        APP.drawingUtils = new DrawingUtils(APP.ctx);
        
        APP.isRunning = true;
        
        // UI updates
        document.getElementById('video-overlay').classList.add('hidden');
        document.getElementById('video-container').classList.add('active');
        document.getElementById('btn-start-camera').disabled = true;
        document.getElementById('btn-stop-camera').disabled = false;
        updateStatus('status-camera', true);
        
        toast('Camera Active', 'Webcam started successfully', 'success');
        log('success', 'Camera started', { w: APP.video.videoWidth, h: APP.video.videoHeight });
        
        // Start loop
        requestAnimationFrame(processFrame);
        
    } catch (err) {
        log('error', 'Camera failed', err.message);
        toast('Camera Error', err.message, 'error');
    }
}

function stopCamera() {
    APP.isRunning = false;
    
    if (APP.stream) {
        APP.stream.getTracks().forEach(t => t.stop());
        APP.stream = null;
    }
    
    APP.video.srcObject = null;
    APP.ctx?.clearRect(0, 0, APP.canvas.width, APP.canvas.height);
    
    document.getElementById('video-overlay').classList.remove('hidden');
    document.getElementById('video-container').classList.remove('active');
    document.getElementById('btn-start-camera').disabled = false;
    document.getElementById('btn-stop-camera').disabled = true;
    updateStatus('status-camera', false);
    
    // Reset displays
    document.getElementById('gesture-name').textContent = '--';
    document.getElementById('confidence-fill').style.width = '0%';
    document.getElementById('confidence-text').textContent = '0%';
    document.getElementById('hand-counter').textContent = 'Hands: 0';
    
    log('info', 'Camera stopped');
    toast('Camera Stopped', 'Webcam turned off', 'info');
}

// ============================================
// Frame Processing & Detection
// ============================================
function processFrame(timestamp) {
    if (!APP.isRunning) return;
    
    // FPS calculation
    APP.frameCount++;
    if (timestamp - APP.lastFpsTime >= 1000) {
        APP.fps = APP.frameCount;
        APP.frameCount = 0;
        APP.lastFpsTime = timestamp;
        document.getElementById('fps-counter').textContent = `FPS: ${APP.fps}`;
    }
    
    // Clear canvas
    APP.ctx.clearRect(0, 0, APP.canvas.width, APP.canvas.height);
    
    // Skip if no model or same frame
    if (!APP.gestureRecognizer || APP.video.currentTime === APP.lastVideoTime) {
        requestAnimationFrame(processFrame);
        return;
    }
    APP.lastVideoTime = APP.video.currentTime;
    
    try {
        // Run recognition
        APP.results = APP.gestureRecognizer.recognizeForVideo(APP.video, timestamp);
        
        // Draw & process
        drawLandmarks();
        processGestures();
        
    } catch (err) {
        // Only log occasionally to avoid spam
        if (APP.frameCount % 60 === 0) {
            log('error', 'Detection error', err.message);
        }
    }
    
    requestAnimationFrame(processFrame);
}

function drawLandmarks() {
    if (!APP.results?.landmarks || !APP.showSkeleton) return;
    
    const handCount = APP.results.landmarks.length;
    document.getElementById('hand-counter').textContent = `Hands: ${handCount}`;
    
    for (let i = 0; i < APP.results.landmarks.length; i++) {
        const landmarks = APP.results.landmarks[i];
        const handedness = APP.results.handednesses[i]?.[0]?.categoryName || 'Unknown';
        
        // Colors based on hand
        const isLeft = handedness === 'Left';
        const connectorColor = isLeft ? '#00d4ff' : '#8b5cf6';
        const landmarkColor = isLeft ? '#ff00ff' : '#10b981';
        
        // Draw connectors
        APP.drawingUtils.drawConnectors(
            landmarks,
            GestureRecognizer.HAND_CONNECTIONS,
            { color: connectorColor, lineWidth: 4 }
        );
        
        // Draw landmarks
        APP.drawingUtils.drawLandmarks(landmarks, {
            color: landmarkColor,
            lineWidth: 1,
            radius: 5
        });
    }
}

function processGestures() {
    if (!APP.results?.gestures?.length) {
        document.getElementById('gesture-name').textContent = '--';
        document.getElementById('confidence-fill').style.width = '0%';
        document.getElementById('confidence-text').textContent = '0%';
        document.getElementById('handedness-display').querySelector('.value').textContent = '--';
        return;
    }
    
    // Get best gesture
    const gesture = APP.results.gestures[0][0];
    const name = gesture.categoryName;
    const confidence = gesture.score;
    const handedness = APP.results.handednesses[0]?.[0]?.categoryName || 'Unknown';
    
    // Update UI
    document.getElementById('gesture-name').textContent = name || '--';
    document.getElementById('confidence-fill').style.width = `${confidence * 100}%`;
    document.getElementById('confidence-text').textContent = `${(confidence * 100).toFixed(0)}%`;
    document.getElementById('handedness-display').querySelector('.value').textContent = handedness;
    
    // Check threshold
    if (confidence < APP.confidenceThreshold) return;
    if (name === 'None' || !name) return;
    
    // Auto-speak with debounce
    if (APP.autoSpeak && name !== APP.lastSpoken) {
        clearTimeout(APP.speakTimeout);
        APP.speakTimeout = setTimeout(() => {
            speak(name);
            APP.lastSpoken = name;
            setTimeout(() => { APP.lastSpoken = null; }, APP.speakDelay);
        }, 300);
    }
}

// ============================================
// Voice Output
// ============================================
function initVoices() {
    const loadVoices = () => {
        APP.voices = speechSynthesis.getVoices();
        const select = document.getElementById('voice-select');
        select.innerHTML = '';
        
        if (!APP.voices.length) {
            select.innerHTML = '<option>No voices</option>';
            return;
        }
        
        APP.voices.forEach((v, i) => {
            const opt = document.createElement('option');
            opt.value = i;
            opt.textContent = `${v.name} (${v.lang})`;
            if (v.default) opt.selected = true;
            select.appendChild(opt);
        });
        
        APP.selectedVoice = APP.voices.find(v => v.default) || APP.voices[0];
        updateStatus('status-voice', true);
        log('success', `Loaded ${APP.voices.length} voices`);
    };
    
    loadVoices();
    speechSynthesis.onvoiceschanged = loadVoices;
}

function speak(text) {
    if (!text || !speechSynthesis) return;
    
    speechSynthesis.cancel();
    
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.voice = APP.selectedVoice;
    utterance.rate = APP.voiceRate;
    utterance.pitch = APP.voicePitch;
    
    utterance.onerror = (e) => log('error', 'Speech error', e.error);
    
    speechSynthesis.speak(utterance);
    log('info', `Speaking: ${text}`);
}

// ============================================
// Sentence Builder
// ============================================
function addToSentence(text) {
    if (!text || text === 'None' || text === '--') return;
    APP.sentence.push(text);
    updateSentenceDisplay();
}

function updateSentenceDisplay() {
    const el = document.getElementById('sentence-display');
    if (!APP.sentence.length) {
        el.innerHTML = '<span class="placeholder">Press \'G\' or click \'+\' to add gestures...</span>';
    } else {
        el.textContent = APP.sentence.join(' ');
    }
}

function backspaceSentence() {
    APP.sentence.pop();
    updateSentenceDisplay();
}

function clearSentence() {
    APP.sentence = [];
    updateSentenceDisplay();
}

function copySentence() {
    const text = APP.sentence.join(' ');
    if (text) {
        navigator.clipboard.writeText(text);
        toast('Copied', 'Sentence copied to clipboard', 'success');
    }
}

function speakSentence() {
    const text = APP.sentence.join(' ');
    if (text) speak(text);
}

// ============================================
// Gesture Capture
// ============================================
function captureGesture() {
    if (!APP.isRunning) {
        toast('Camera Off', 'Start the camera first', 'warning');
        return;
    }
    
    if (!APP.results?.landmarks?.length) {
        toast('No Hands', 'No hands detected in frame', 'error');
        log('warn', 'Capture failed - no hands detected');
        return;
    }
    
    const name = document.getElementById('gesture-name-input').value.trim();
    if (!name) {
        toast('Name Required', 'Enter a gesture name first', 'warning');
        document.getElementById('gesture-name-input').focus();
        return;
    }
    
    APP.gestureName = name;
    
    // Capture data
    const data = {
        timestamp: Date.now(),
        gestureName: name,
        landmarks: APP.results.landmarks.map(hand => 
            hand.map(lm => ({ x: lm.x, y: lm.y, z: lm.z }))
        ),
        handedness: APP.results.handednesses.map(h => h[0]?.categoryName),
        worldLandmarks: APP.results.worldLandmarks?.map(hand =>
            hand.map(lm => ({ x: lm.x, y: lm.y, z: lm.z }))
        )
    };
    
    APP.captures.push(data);
    
    // Update UI
    document.getElementById('sample-count').textContent = APP.captures.length;
    document.getElementById('landmark-count').textContent = data.landmarks.flat().length;
    document.getElementById('btn-export-captures').disabled = false;
    
    // Add thumbnail
    const preview = document.getElementById('capture-preview');
    const thumb = document.createElement('div');
    thumb.className = 'capture-thumb';
    thumb.textContent = APP.captures.length;
    preview.appendChild(thumb);
    
    // Visual feedback
    const container = document.getElementById('video-container');
    container.classList.add('capturing');
    setTimeout(() => container.classList.remove('capturing'), 150);
    
    log('success', `Captured frame ${APP.captures.length}`, { gesture: name, hands: data.landmarks.length });
    toast('Captured', `Frame ${APP.captures.length} for "${name}"`, 'success');
}

function clearCaptures() {
    APP.captures = [];
    APP.gestureName = '';
    document.getElementById('sample-count').textContent = '0';
    document.getElementById('landmark-count').textContent = '0';
    document.getElementById('capture-preview').innerHTML = '';
    document.getElementById('btn-export-captures').disabled = true;
    toast('Cleared', 'All captures cleared', 'info');
}

function exportCaptures() {
    if (!APP.captures.length) {
        toast('No Data', 'Nothing to export', 'warning');
        return;
    }
    
    const data = {
        exportedAt: new Date().toISOString(),
        gestureName: APP.gestureName,
        totalFrames: APP.captures.length,
        frames: APP.captures
    };
    
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `gesture_${APP.gestureName}_${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
    
    toast('Exported', `${APP.captures.length} frames exported`, 'success');
    log('success', 'Exported captures', { frames: APP.captures.length });
}

// ============================================
// Screenshot
// ============================================
function takeScreenshot() {
    if (!APP.isRunning) {
        toast('Camera Off', 'Start camera first', 'warning');
        return;
    }
    
    const canvas = document.createElement('canvas');
    canvas.width = APP.video.videoWidth;
    canvas.height = APP.video.videoHeight;
    const ctx = canvas.getContext('2d');
    
    // Draw mirrored video
    ctx.translate(canvas.width, 0);
    ctx.scale(-1, 1);
    ctx.drawImage(APP.video, 0, 0);
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    
    // Draw landmarks overlay
    ctx.translate(canvas.width, 0);
    ctx.scale(-1, 1);
    ctx.drawImage(APP.canvas, 0, 0);
    
    const link = document.createElement('a');
    link.download = `slis_${Date.now()}.png`;
    link.href = canvas.toDataURL();
    link.click();
    
    toast('Screenshot', 'Image saved', 'success');
}

// ============================================
// Event Listeners
// ============================================
function setupEvents() {
    // Camera
    document.getElementById('btn-start-camera').onclick = startCamera;
    document.getElementById('btn-stop-camera').onclick = stopCamera;
    document.getElementById('btn-screenshot').onclick = takeScreenshot;
    
    document.getElementById('btn-toggle-skeleton').onclick = () => {
        APP.showSkeleton = !APP.showSkeleton;
        document.getElementById('btn-toggle-skeleton').innerHTML = 
            `<span class="icon">🦴</span> Skeleton: ${APP.showSkeleton ? 'ON' : 'OFF'}`;
    };
    
    document.getElementById('btn-flip-camera').onclick = () => {
        APP.isMirrored = !APP.isMirrored;
        const transform = APP.isMirrored ? 'scaleX(-1)' : 'scaleX(1)';
        APP.video.style.transform = transform;
        APP.canvas.style.transform = transform;
    };
    
    // Model upload
    const uploadArea = document.getElementById('upload-area');
    const fileInput = document.getElementById('model-file-input');
    
    uploadArea.onclick = () => fileInput.click();
    uploadArea.ondragover = (e) => { e.preventDefault(); uploadArea.classList.add('dragover'); };
    uploadArea.ondragleave = () => uploadArea.classList.remove('dragover');
    uploadArea.ondrop = (e) => {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
        if (e.dataTransfer.files[0]) handleModelFile(e.dataTransfer.files[0]);
    };
    fileInput.onchange = (e) => { if (e.target.files[0]) handleModelFile(e.target.files[0]); };
    
    document.getElementById('btn-load-default').onclick = loadDefaultModel;
    
    // Voice
    document.getElementById('auto-speak-toggle').onchange = (e) => {
        APP.autoSpeak = e.target.checked;
        log('info', `Auto-speak: ${APP.autoSpeak}`);
    };
    
    document.getElementById('voice-select').onchange = (e) => {
        APP.selectedVoice = APP.voices[e.target.value];
    };
    
    document.getElementById('voice-rate').oninput = (e) => {
        APP.voiceRate = parseFloat(e.target.value);
        document.getElementById('rate-value').textContent = APP.voiceRate.toFixed(1);
    };
    
    document.getElementById('voice-pitch').oninput = (e) => {
        APP.voicePitch = parseFloat(e.target.value);
        document.getElementById('pitch-value').textContent = APP.voicePitch.toFixed(1);
    };
    
    document.getElementById('btn-test-voice').onclick = () => speak('Hello, this is a voice test.');
    
    // Settings
    document.getElementById('confidence-threshold').oninput = (e) => {
        APP.confidenceThreshold = parseInt(e.target.value) / 100;
        document.getElementById('threshold-value').textContent = `${e.target.value}%`;
    };
    
    document.getElementById('max-hands').onchange = async (e) => {
        APP.maxHands = parseInt(e.target.value);
        if (APP.gestureRecognizer) {
            await APP.gestureRecognizer.setOptions({ numHands: APP.maxHands });
            log('info', `Max hands: ${APP.maxHands}`);
        }
    };
    
    document.getElementById('speak-delay').onchange = (e) => {
        APP.speakDelay = parseInt(e.target.value);
    };
    
    // Sentence
    document.getElementById('btn-add-gesture').onclick = () => {
        const name = document.getElementById('gesture-name').textContent;
        addToSentence(name);
    };
    document.getElementById('btn-add-space').onclick = () => addToSentence(' ');
    document.getElementById('btn-backspace').onclick = backspaceSentence;
    document.getElementById('btn-clear-sentence').onclick = clearSentence;
    document.getElementById('btn-copy-sentence').onclick = copySentence;
    document.getElementById('btn-speak-sentence').onclick = speakSentence;
    
    // Capture
    document.getElementById('btn-capture-gesture').onclick = captureGesture;
    document.getElementById('btn-clear-captures').onclick = clearCaptures;
    document.getElementById('btn-export-captures').onclick = exportCaptures;
    
    document.getElementById('gesture-name-input').onkeypress = (e) => {
        if (e.key === 'Enter') captureGesture();
    };
    
    // Debug
    document.getElementById('btn-clear-debug').onclick = () => {
        document.getElementById('debug-log').innerHTML = '';
    };
    
    document.getElementById('btn-toggle-debug').onclick = () => {
        APP.debugMinimized = !APP.debugMinimized;
        document.getElementById('debug-panel').classList.toggle('minimized', APP.debugMinimized);
        document.getElementById('btn-toggle-debug').textContent = APP.debugMinimized ? '▲' : '▼';
    };
    
    // Keyboard shortcuts
    document.addEventListener('keydown', (e) => {
        if (e.target.tagName === 'INPUT') return;
        
        switch (e.code) {
            case 'Space':
                e.preventDefault();
                captureGesture();
                break;
            case 'KeyG':
                const name = document.getElementById('gesture-name').textContent;
                addToSentence(name);
                break;
            case 'KeyC':
                if (e.ctrlKey || e.metaKey) copySentence();
                break;
        }
    });
}

// ============================================
// Initialize
// ============================================
async function init() {
    log('info', '═══════════════════════════════════════');
    log('info', 'SLIS - Sign Language Interpretation System');
    log('info', '═══════════════════════════════════════');
    
    // Get elements
    APP.video = document.getElementById('webcam');
    APP.canvas = document.getElementById('output-canvas');
    
    // Check browser support
    if (!navigator.mediaDevices?.getUserMedia) {
        log('error', 'Camera API not supported');
        toast('Browser Error', 'Camera not supported in this browser', 'error');
        return;
    }
    
    // Initialize
    initVoices();
    setupEvents();
    
    log('success', 'SLIS initialized');
    toast('Welcome to SLIS', 'Upload a .task model or load the default to begin', 'info');
}

document.addEventListener('DOMContentLoaded', init);
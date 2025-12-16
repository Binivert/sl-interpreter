/**
 * SLIS Main Application
 * Live mode functionality
 */

class SLISApp {
    constructor() {
        this.ws = null;
        this.video = null;
        this.canvas = null;
        this.ctx = null;
        this.isRunning = false;
        this.history = [];
        this.currentSign = null;
        
        this.init();
    }
    
    async init() {
        // Get DOM elements
        this.video = document.getElementById('camera-feed');
        this.canvas = document.getElementById('landmark-overlay');
        this.ctx = this.canvas.getContext('2d');
        
        // Setup event listeners
        this.setupEventListeners();
        
        // Connect WebSocket
        this.connectWebSocket();
        
        // Start camera
        await this.startCamera();
        
        // Load initial status
        await this.loadStatus();
    }
    
    setupEventListeners() {
        // Toggle camera button
        document.getElementById('btn-toggle-camera')?.addEventListener('click', () => {
            this.toggleCamera();
        });
        
        // Toggle landmarks button
        document.getElementById('btn-toggle-landmarks')?.addEventListener('click', () => {
            this.toggleLandmarks();
        });
        
        // Speak button
        document.getElementById('btn-speak')?.addEventListener('click', () => {
            this.speak();
        });
        
        // Clear history button
        document.getElementById('btn-clear-history')?.addEventListener('click', () => {
            this.clearHistory();
        });
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.key === 's' || e.key === 'S') {
                this.speak();
            } else if (e.key === 'c' || e.key === 'C') {
                this.clearHistory();
            }
        });
    }
    
    connectWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws`;
        
        this.ws = new WebSocket(wsUrl);
        
        this.ws.onopen = () => {
            console.log('WebSocket connected');
            this.updateConnectionStatus(true);
        };
        
        this.ws.onclose = () => {
            console.log('WebSocket disconnected');
            this.updateConnectionStatus(false);
            
            // Reconnect after delay
            setTimeout(() => this.connectWebSocket(), 3000);
        };
        
        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
        };
        
        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleMessage(data);
        };
    }
    
    handleMessage(data) {
        switch (data.type) {
            case 'recognition':
                this.updateRecognition(data.sign, data.confidence);
                if (data.landmarks) {
                    this.drawLandmarks(data.landmarks);
                }
                break;
                
            case 'landmarks':
                this.drawLandmarks(data.landmarks);
                break;
                
            case 'status':
                this.updateStatus(data);
                break;
                
            case 'audio':
                this.playAudio(data.data);
                break;
                
            case 'no_detection':
                this.clearLandmarks();
                break;
        }
    }
    
    async startCamera() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({
                video: {
                    width: { ideal: 1280 },
                    height: { ideal: 720 },
                    facingMode: 'user'
                }
            });
            
            this.video.srcObject = stream;
            this.isRunning = true;
            
            // Wait for video to be ready
            await new Promise(resolve => {
                this.video.onloadedmetadata = resolve;
            });
            
            // Set canvas size
            this.canvas.width = this.video.videoWidth;
            this.canvas.height = this.video.videoHeight;
            
            // Start frame processing
            this.processFrames();
            
        } catch (error) {
            console.error('Camera error:', error);
            alert('Failed to access camera. Please ensure camera permissions are granted.');
        }
    }
    
    async processFrames() {
        if (!this.isRunning) return;
        
        // Capture frame and send to server
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            const frameData = this.captureFrame();
            if (frameData) {
                this.ws.send(JSON.stringify({
                    type: 'frame',
                    frame: frameData
                }));
            }
        }
        
        // Schedule next frame
        requestAnimationFrame(() => this.processFrames());
    }
    
    captureFrame() {
        const tempCanvas = document.createElement('canvas');
        tempCanvas.width = this.video.videoWidth;
        tempCanvas.height = this.video.videoHeight;
        
        const tempCtx = tempCanvas.getContext('2d');
        tempCtx.drawImage(this.video, 0, 0);
        
        // Convert to base64
        const dataUrl = tempCanvas.toDataURL('image/jpeg', 0.8);
        return dataUrl.split(',')[1];
    }
    
    updateRecognition(sign, confidence) {
        const signNameEl = document.getElementById('sign-name');
        const confidenceFillEl = document.getElementById('confidence-fill');
        const confidenceTextEl = document.getElementById('confidence-text');
        const subtitleEl = document.getElementById('subtitle-text');
        
        if (signNameEl) signNameEl.textContent = sign;
        if (confidenceFillEl) confidenceFillEl.style.width = `${confidence * 100}%`;
        if (confidenceTextEl) confidenceTextEl.textContent = `${(confidence * 100).toFixed(1)}%`;
        
        // Update subtitle
        if (subtitleEl && sign !== this.currentSign) {
            const currentText = subtitleEl.textContent;
            if (currentText === 'Waiting for signs...') {
                subtitleEl.textContent = sign;
            } else {
                subtitleEl.textContent = currentText + ' ' + sign;
            }
        }
        
        // Add to history
        if (sign !== this.currentSign) {
            this.addToHistory(sign, confidence);
            this.currentSign = sign;
        }
    }
    
    addToHistory(sign, confidence) {
        this.history.push({ sign, confidence, timestamp: Date.now() });
        
        const historyList = document.getElementById('history-list');
        if (historyList) {
            const item = document.createElement('div');
            item.className = 'history-item animate-slideUp';
            item.textContent = `• ${sign}`;
            historyList.insertBefore(item, historyList.firstChild);
            
            // Keep only last 20 items
            while (historyList.children.length > 20) {
                historyList.removeChild(historyList.lastChild);
            }
        }
    }
    
    clearHistory() {
        this.history = [];
        this.currentSign = null;
        
        const historyList = document.getElementById('history-list');
        if (historyList) historyList.innerHTML = '';
        
        const subtitleEl = document.getElementById('subtitle-text');
        if (subtitleEl) subtitleEl.textContent = 'Waiting for signs...';
        
        const signNameEl = document.getElementById('sign-name');
        if (signNameEl) signNameEl.textContent = '—';
    }
    
    drawLandmarks(landmarks) {
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        
        // Draw hand landmarks
        this.ctx.fillStyle = '#00d4ff';
        this.ctx.strokeStyle = '#00d4ff';
        this.ctx.lineWidth = 2;
        
        // Assuming landmarks are in normalized coordinates
        for (let i = 0; i < landmarks.length; i += 3) {
            const x = landmarks[i] * this.canvas.width;
            const y = landmarks[i + 1] * this.canvas.height;
            
            this.ctx.beginPath();
            this.ctx.arc(x, y, 4, 0, Math.PI * 2);
            this.ctx.fill();
        }
    }
    
    clearLandmarks() {
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
    }
    
    speak() {
        const subtitleEl = document.getElementById('subtitle-text');
        const text = subtitleEl?.textContent || '';
        
        if (text && text !== 'Waiting for signs...' && this.ws) {
            this.ws.send(JSON.stringify({
                type: 'speak',
                text: text
            }));
        }
    }
    
    playAudio(hexData) {
        const bytes = new Uint8Array(hexData.match(/.{1,2}/g).map(byte => parseInt(byte, 16)));
        const blob = new Blob([bytes], { type: 'audio/wav' });
        const url = URL.createObjectURL(blob);
        
        const audio = new Audio(url);
        audio.play();
        
        audio.onended = () => URL.revokeObjectURL(url);
    }
    
    toggleCamera() {
        this.isRunning = !this.isRunning;
        if (this.isRunning) {
            this.processFrames();
        }
    }
    
    toggleLandmarks() {
        this.canvas.style.display = this.canvas.style.display === 'none' ? 'block' : 'none';
    }
    
    updateConnectionStatus(connected) {
        const indicator = document.querySelector('.status-indicator');
        const text = document.querySelector('.status-text');
        
        if (indicator) {
            indicator.className = `status-indicator ${connected ? 'status-connected' : ''}`;
        }
        if (text) {
            text.textContent = connected ? 'Connected' : 'Disconnected';
        }
    }
    
    async loadStatus() {
        try {
            const response = await fetch('/api/status');
            const data = await response.json();
            this.updateStatus(data);
        } catch (error) {
            console.error('Failed to load status:', error);
        }
    }
    
    updateStatus(data) {
        const modelEl = document.getElementById('status-model');
        const voiceEl = document.getElementById('status-voice');
        const fpsEl = document.getElementById('status-fps');
        const latencyEl = document.getElementById('status-latency');
        
        if (modelEl && data.model) modelEl.textContent = data.model;
        if (voiceEl && data.voice) voiceEl.textContent = data.voice;
        if (fpsEl && data.fps) fpsEl.textContent = data.fps;
        if (latencyEl && data.latency) latencyEl.textContent = `${data.latency}ms`;
    }
}

// Initialize app
const app = new SLISApp();

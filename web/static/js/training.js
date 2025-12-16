/**
 * SLIS Training Mode
 */

class TrainingApp {
    constructor() {
        this.ws = null;
        this.video = null;
        this.canvas = null;
        this.ctx = null;
        this.isCapturing = false;
        this.samples = [];
        this.currentSignName = '';
        this.requiredSamples = 10;
        
        this.init();
    }
    
    async init() {
        this.video = document.getElementById('camera-feed');
        this.canvas = document.getElementById('landmark-overlay');
        this.ctx = this.canvas.getContext('2d');
        
        this.setupEventListeners();
        this.connectWebSocket();
        await this.startCamera();
        await this.loadExistingSigns();
    }
    
    setupEventListeners() {
        // Capture button
        document.getElementById('btn-capture')?.addEventListener('click', () => {
            this.capture();
        });
        
        // Train button
        document.getElementById('btn-train')?.addEventListener('click', () => {
            this.startTraining();
        });
        
        // Clear button
        document.getElementById('btn-clear')?.addEventListener('click', () => {
            this.clearSamples();
        });
        
        // Sign name input
        document.getElementById('sign-name-input')?.addEventListener('input', (e) => {
            this.currentSignName = e.target.value.trim();
            this.updateUI();
        });
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.code === 'Space' && this.currentSignName) {
                e.preventDefault();
                this.capture();
            }
        });
        
        // Search
        document.getElementById('sign-search')?.addEventListener('input', (e) => {
            this.filterSigns(e.target.value);
        });
    }
    
    connectWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws`;
        
        this.ws = new WebSocket(wsUrl);
        
        this.ws.onopen = () => console.log('WebSocket connected');
        this.ws.onclose = () => setTimeout(() => this.connectWebSocket(), 3000);
        this.ws.onmessage = (event) => this.handleMessage(JSON.parse(event.data));
    }
    
    handleMessage(data) {
        switch (data.type) {
            case 'capture_result':
                this.onCaptureResult(data);
                break;
                
            case 'training_status':
                this.updateTrainingStatus(data);
                break;
                
            case 'training_progress':
                this.updateTrainingProgress(data.progress);
                break;
                
            case 'landmarks':
                this.drawLandmarks(data.landmarks);
                break;
        }
    }
    
    async startCamera() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({
                video: { width: { ideal: 1280 }, height: { ideal: 720 } }
            });
            
            this.video.srcObject = stream;
            await new Promise(resolve => this.video.onloadedmetadata = resolve);
            
            this.canvas.width = this.video.videoWidth;
            this.canvas.height = this.video.videoHeight;
            
            this.processFrames();
        } catch (error) {
            console.error('Camera error:', error);
        }
    }
    
    processFrames() {
        if (this.ws?.readyState === WebSocket.OPEN) {
            const frameData = this.captureFrame();
            if (frameData) {
                this.ws.send(JSON.stringify({ type: 'frame', frame: frameData }));
            }
        }
        requestAnimationFrame(() => this.processFrames());
    }
    
    captureFrame() {
        const tempCanvas = document.createElement('canvas');
        tempCanvas.width = this.video.videoWidth;
        tempCanvas.height = this.video.videoHeight;
        tempCanvas.getContext('2d').drawImage(this.video, 0, 0);
        return tempCanvas.toDataURL('image/jpeg', 0.8).split(',')[1];
    }
    
    capture() {
        if (!this.currentSignName) {
            alert('Please enter a sign name first');
            return;
        }
        
        if (this.samples.length >= this.requiredSamples) {
            return;
        }
        
        // Send capture request
        this.ws.send(JSON.stringify({
            type: 'capture',
            sign_name: this.currentSignName,
            landmarks: this.currentLandmarks
        }));
        
        // Visual feedback
        this.flashCapture();
    }
    
    onCaptureResult(data) {
        this.samples.push(data);
        this.updateSamplesUI();
        this.updateUI();
    }
    
    updateSamplesUI() {
        const grid = document.getElementById('samples-grid');
        if (!grid) return;
        
        grid.innerHTML = '';
        this.samples.forEach((_, i) => {
            const thumb = document.createElement('div');
            thumb.className = 'sample-thumb animate-fadeIn';
            thumb.textContent = i + 1;
            grid.appendChild(thumb);
        });
        
        // Update progress
        const count = document.getElementById('sample-count');
        const progress = document.getElementById('capture-progress');
        
        if (count) count.textContent = `${this.samples.length}/${this.requiredSamples}`;
        if (progress) progress.style.width = `${(this.samples.length / this.requiredSamples) * 100}%`;
    }
    
    updateUI() {
        const trainBtn = document.getElementById('btn-train');
        if (trainBtn) {
            trainBtn.disabled = this.samples.length < this.requiredSamples || !this.currentSignName;
        }
    }
    
    flashCapture() {
        const container = document.querySelector('.camera-container');
        if (container) {
            container.style.boxShadow = '0 0 30px var(--primary-accent)';
            setTimeout(() => container.style.boxShadow = '', 200);
        }
    }
    
    clearSamples() {
        this.samples = [];
        this.updateSamplesUI();
        this.updateUI();
    }
    
    startTraining() {
        if (!this.currentSignName || this.samples.length < this.requiredSamples) {
            return;
        }
        
        // Show training progress section
        const progressSection = document.getElementById('training-progress-section');
        if (progressSection) progressSection.style.display = 'block';
        
        // Send training request
        this.ws.send(JSON.stringify({
            type: 'train',
            sign_name: this.currentSignName
        }));
    }
    
    updateTrainingStatus(data) {
        const icon = document.getElementById('training-icon');
        const message = document.getElementById('training-message');
        const metrics = document.getElementById('training-metrics');
        
        switch (data.status) {
            case 'started':
                if (icon) icon.textContent = '⏳';
                if (message) message.textContent = 'Preparing data...';
                break;
                
            case 'completed':
                if (icon) icon.textContent = '✅';
                if (message) message.textContent = 'Training complete!';
                if (metrics) {
                    metrics.style.display = 'grid';
                    document.getElementById('metric-accuracy').textContent = 
                        `${(data.metrics.final_val_accuracy * 100).toFixed(1)}%`;
                    document.getElementById('metric-loss').textContent = 
                        data.metrics.final_val_loss.toFixed(4);
                }
                this.loadExistingSigns();
                break;
                
            case 'error':
                if (icon) icon.textContent = '❌';
                if (message) message.textContent = `Error: ${data.error}`;
                break;
        }
    }
    
    updateTrainingProgress(progress) {
        const progressBar = document.getElementById('training-progress');
        const message = document.getElementById('training-message');
        
        if (progressBar) progressBar.style.width = `${progress * 100}%`;
        if (message && progress < 1) message.textContent = `Training... ${(progress * 100).toFixed(0)}%`;
    }
    
    async loadExistingSigns() {
        try {
            const response = await fetch('/api/signs');
            const data = await response.json();
            this.renderSigns(data.signs);
        } catch (error) {
            console.error('Failed to load signs:', error);
        }
    }
    
    renderSigns(signs) {
        const grid = document.getElementById('signs-grid');
        const totalEl = document.getElementById('total-signs');
        
        if (totalEl) totalEl.textContent = signs.length;
        
        if (grid) {
            grid.innerHTML = '';
            signs.forEach(sign => {
                const card = document.createElement('div');
                card.className = 'sign-card';
                card.innerHTML = `<div class="sign-card-name">${sign}</div>`;
                grid.appendChild(card);
            });
        }
    }
    
    filterSigns(query) {
        const cards = document.querySelectorAll('.sign-card');
        const lowerQuery = query.toLowerCase();
        
        cards.forEach(card => {
            const name = card.textContent.toLowerCase();
            card.style.display = name.includes(lowerQuery) ? '' : 'none';
        });
    }
    
    drawLandmarks(landmarks) {
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        this.ctx.fillStyle = '#00d4ff';
        
        for (let i = 0; i < landmarks.length; i += 3) {
            const x = landmarks[i] * this.canvas.width;
            const y = landmarks[i + 1] * this.canvas.height;
            
            this.ctx.beginPath();
            this.ctx.arc(x, y, 4, 0, Math.PI * 2);
            this.ctx.fill();
        }
        
        this.currentLandmarks = landmarks;
    }
}

const app = new TrainingApp();

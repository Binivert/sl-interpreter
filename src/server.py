"""FastAPI server for SLIS."""

import asyncio
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from fastapi.responses import HTMLResponse

from src.vision.camera import CameraManager
from src.vision.landmark_extractor import LandmarkExtractor
from src.vision.temporal_buffer import TemporalBuffer
from src.recognition.classifier import GestureClassifier
from src.recognition.model_loader import ModelLoader
from src.recognition.confidence_filter import ConfidenceFilter
from src.audio.tts_engine import TTSEngineFactory
from src.modules.registry import ModuleRegistry
from src.training.capture import CaptureManager
from src.training.trainer import ModelTrainer

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections."""
    
    def __init__(self):
        self.active_connections: list[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"Client connected. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info(f"Client disconnected. Total connections: {len(self.active_connections)}")
    
    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to client: {e}")


def create_app(config: Dict[str, Any]) -> FastAPI:
    """Create and configure the FastAPI application."""
    
    app = FastAPI(
        title="SLIS",
        description="Sign Language Interpretation System",
        version="1.0.0"
    )
    
    # Store config in app state
    app.state.config = config
    
    # Initialize components
    app.state.connection_manager = ConnectionManager()
    app.state.module_registry = ModuleRegistry(config)
    app.state.model_loader = ModelLoader(config)
    app.state.landmark_extractor = LandmarkExtractor(config)
    app.state.temporal_buffer = TemporalBuffer(
        window_size=config["recognition"]["temporal_window"]
    )
    app.state.classifier = GestureClassifier(
        app.state.model_loader,
        config
    )
    app.state.confidence_filter = ConfidenceFilter(
        threshold=config["recognition"]["confidence_threshold"],
        smoothing=config["recognition"]["smoothing_factor"]
    )
    app.state.tts_engine = TTSEngineFactory.create(config["audio"])
    app.state.capture_manager = CaptureManager(config)
    app.state.trainer = ModelTrainer(config)
    
    # Mount static files
    static_path = Path("web/static")
    if static_path.exists():
        app.mount("/static", StaticFiles(directory=str(static_path)), name="static")
    
    # Setup templates
    templates_path = Path("web/templates")
    templates = Jinja2Templates(directory=str(templates_path))
    
    # Routes
    @app.get("/", response_class=HTMLResponse)
    async def index(request: Request):
        return templates.TemplateResponse("index.html", {"request": request})
    
    @app.get("/training", response_class=HTMLResponse)
    async def training(request: Request):
        return templates.TemplateResponse("training.html", {"request": request})
    
    @app.get("/settings", response_class=HTMLResponse)
    async def settings(request: Request):
        return templates.TemplateResponse("settings.html", {"request": request})
    
    # API Routes
    @app.get("/api/status")
    async def get_status():
        return {
            "status": "running",
            "model": app.state.classifier.current_model,
            "voice": app.state.tts_engine.current_voice,
            "signs_count": len(app.state.classifier.labels)
        }
    
    @app.get("/api/models")
    async def get_models():
        return {
            "gesture_models": app.state.model_loader.list_gesture_models(),
            "voice_models": app.state.tts_engine.list_voices(),
            "language_packs": app.state.module_registry.list_language_packs()
        }
    
    @app.put("/api/models/{model_type}/{model_name}")
    async def switch_model(model_type: str, model_name: str):
        try:
            if model_type == "gesture":
                app.state.classifier.load_model(model_name)
            elif model_type == "voice":
                app.state.tts_engine.set_voice(model_name)
            else:
                raise HTTPException(status_code=400, detail=f"Unknown model type: {model_type}")
            return {"status": "success", "model": model_name}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/signs")
    async def get_signs():
        return {"signs": app.state.classifier.labels}
    
    @app.post("/api/speak")
    async def speak(text: str):
        audio_data = app.state.tts_engine.synthesize(text)
        return {"status": "success", "audio_length": len(audio_data)}
    
    # WebSocket endpoint
    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket):
        await app.state.connection_manager.connect(websocket)
        
        try:
            while True:
                data = await websocket.receive_json()
                await handle_websocket_message(app, websocket, data)
        except WebSocketDisconnect:
            app.state.connection_manager.disconnect(websocket)
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
            app.state.connection_manager.disconnect(websocket)
    
    return app


async def handle_websocket_message(app: FastAPI, websocket: WebSocket, data: dict):
    """Handle incoming WebSocket messages."""
    
    msg_type = data.get("type")
    
    if msg_type == "frame":
        # Process video frame
        frame_data = data.get("frame")
        result = await process_frame(app, frame_data)
        if result:
            await websocket.send_json(result)
    
    elif msg_type == "speak":
        text = data.get("text", "")
        audio_data = app.state.tts_engine.synthesize(text)
        await websocket.send_json({
            "type": "audio",
            "data": audio_data.hex()
        })
    
    elif msg_type == "capture":
        sign_name = data.get("sign_name")
        landmarks = data.get("landmarks")
        app.state.capture_manager.add_sample(sign_name, landmarks)
        await websocket.send_json({
            "type": "capture_result",
            "sign_name": sign_name,
            "sample_count": app.state.capture_manager.get_sample_count(sign_name)
        })
    
    elif msg_type == "train":
        sign_name = data.get("sign_name")
        # Start training in background
        asyncio.create_task(train_sign(app, websocket, sign_name))
    
    elif msg_type == "config":
        key = data.get("key")
        value = data.get("value")
        update_config(app, key, value)


async def process_frame(app: FastAPI, frame_data: str) -> Optional[dict]:
    """Process a video frame and return recognition results."""
    
    import base64
    import cv2
    import numpy as np
    
    # Decode frame
    frame_bytes = base64.b64decode(frame_data)
    nparr = np.frombuffer(frame_bytes, np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    if frame is None:
        return None
    
    # Extract landmarks
    landmarks = app.state.landmark_extractor.extract(frame)
    
    if landmarks is None:
        return {"type": "no_detection"}
    
    # Add to temporal buffer
    app.state.temporal_buffer.add(landmarks)
    
    # Get sequence for classification
    sequence = app.state.temporal_buffer.get_sequence()
    
    if sequence is None:
        return {"type": "buffering"}
    
    # Classify gesture
    prediction, confidence = app.state.classifier.predict(sequence)
    
    # Apply confidence filter
    filtered_prediction = app.state.confidence_filter.filter(
        prediction, confidence
    )
    
    if filtered_prediction is None:
        return {
            "type": "low_confidence",
            "landmarks": landmarks.tolist()
        }
    
    return {
        "type": "recognition",
        "sign": filtered_prediction,
        "confidence": float(confidence),
        "landmarks": landmarks.tolist()
    }


async def train_sign(app: FastAPI, websocket: WebSocket, sign_name: str):
    """Train a new sign."""
    
    try:
        await websocket.send_json({
            "type": "training_status",
            "status": "started",
            "sign_name": sign_name
        })
        
        # Get samples
        samples = app.state.capture_manager.get_samples(sign_name)
        
        # Train incrementally
        metrics = await app.state.trainer.train_incremental(
            sign_name,
            samples,
            progress_callback=lambda p: asyncio.create_task(
                websocket.send_json({
                    "type": "training_progress",
                    "progress": p
                })
            )
        )
        
        # Reload classifier
        app.state.classifier.reload()
        
        await websocket.send_json({
            "type": "training_status",
            "status": "completed",
            "sign_name": sign_name,
            "metrics": metrics
        })
        
    except Exception as e:
        logger.error(f"Training error: {e}")
        await websocket.send_json({
            "type": "training_status",
            "status": "error",
            "error": str(e)
        })


def update_config(app: FastAPI, key: str, value: Any):
    """Update runtime configuration."""
    
    if key == "confidence_threshold":
        app.state.confidence_filter.threshold = float(value)
    elif key == "smoothing_factor":
        app.state.confidence_filter.smoothing = float(value)
    elif key == "temporal_window":
        app.state.temporal_buffer.resize(int(value))

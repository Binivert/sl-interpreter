import {
    GestureRecognizer,
    FilesetResolver,
    DrawingUtils
} from "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.3";

const demosSection = document.getElementById("demos");
let gestureRecognizer;
let runningMode = "IMAGE";
let enableWebcamButton;
let webcamRunning = false;
const videoHeight = "360px";
const videoWidth = "480px";
const confidenceThreshold = 0.75;

const modelPaths = {
    "Model 1": "https://raw.githubusercontent.com/Binivert/itsbini/main/dataset.task",
    "Model 2": "https://raw.githubusercontent.com/Binivert/itsbini/main/pro.task",
    "Model 3": "https://raw.githubusercontent.com/Binivert/Yaad/main/gesture_recognizer.task",
    "Model 4": "https://storage.googleapis.com/mediapipe-models/gesture_recognizer/gesture_recognizer/float16/1/gesture_recognizer.task"
};

const createGestureRecognizer = async (modelAssetPath) => {
    const vision = await FilesetResolver.forVisionTasks(
        "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.3/wasm"
    );

    const defaultGestureRecognizer = await GestureRecognizer.createFromOptions(vision, {
        baseOptions: {
            modelAssetPath: modelAssetPath,
            delegate: "GPU"
        },
        runningMode: runningMode
    });

    gestureRecognizer = { default: defaultGestureRecognizer };
    demosSection.classList.remove("invisible");
};

const initGestureRecognizer = async () => {
    const selectedModel = localStorage.getItem('selectedModel') || 'Model 1';
    document.getElementById('modelSelect').value = selectedModel;
    await createGestureRecognizer(modelPaths[selectedModel]);
};

initGestureRecognizer();

const video = document.getElementById("webcam");
const canvasElement = document.getElementById("output_canvas");
const canvasCtx = canvasElement.getContext("2d");
const gestureOutput = document.getElementById("gesture_output");

function hasGetUserMedia() {
    return !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia);
}

if (hasGetUserMedia()) {
    enableWebcamButton = document.getElementById("webcamButton");
    enableWebcamButton.addEventListener("click", enableCam);
} else {
    console.warn("getUserMedia() is not supported by your browser");
}

async function enableCam(event) {
    const loadingMessage = document.getElementById('loadingMessage');

    if (!gestureRecognizer) {
        loadingMessage.innerText = "Please wait for translator to load";
        speak("Please wait for translator to load");
        return;
    }

    const loader = document.getElementById('loader');
    loader.style.display = 'block';
    loadingMessage.innerText = "loaded";

    if (webcamRunning === true) {
        webcamRunning = false;
        enableWebcamButton.innerText = "ENABLE PREDICTIONS";
        speak("Webcam disabled");
        loader.style.display = 'none';
    } else {
        webcamRunning = true;
        enableWebcamButton.innerText = "DISABLE PREDICTIONS";
        speak("Webcam enabled");
        loader.style.display = 'none';
    }

    const constraints = {
        video: true
    };

    navigator.mediaDevices.getUserMedia(constraints).then(function (stream) {
        video.srcObject = stream;
        video.addEventListener("loadeddata", () => {
            loader.style.display = 'none';
            predictWebcam();
        });
    });
}

let lastVideoTime = -1;
let results = undefined;

async function predictWebcam() {
    const webcamElement = document.getElementById("webcam");
    if (runningMode === "IMAGE") {
        runningMode = "VIDEO";
        await gestureRecognizer.default.setOptions({ runningMode: "VIDEO" });
    }
    let nowInMs = Date.now();
    if (video.currentTime !== lastVideoTime) {
        lastVideoTime = video.currentTime;
        results = gestureRecognizer.default.recognizeForVideo(video, nowInMs);
    }

    canvasCtx.save();
    canvasCtx.clearRect(0, 0, canvasElement.width, canvasElement.height);
    const drawingUtils = new DrawingUtils(canvasCtx);

    canvasElement.style.height = videoHeight;
    webcamElement.style.height = videoHeight;
    canvasElement.style.width = videoWidth;
    webcamElement.style.width = videoWidth;

    if (results.landmarks) {
        for (const landmarks of results.landmarks) {
            drawingUtils.drawConnectors(
                landmarks,
                GestureRecognizer.HAND_CONNECTIONS,
                {
                    color: "#00fffc",
                    lineWidth: 5
                }
            );
            drawingUtils.drawLandmarks(landmarks, {
                color: "#000066",
                lineWidth: 2
            });
        }
    }
    canvasCtx.restore();

    if (results.gestures.length > 0) {
        const topGesture = results.gestures[0][0];
        const categoryName = topGesture.categoryName;
        const categoryScore = parseFloat(topGesture.score * 100).toFixed(2);

        if (topGesture.score >= confidenceThreshold) {
            gestureOutput.style.display = "block";
            gestureOutput.style.width = videoWidth;
            const handedness = results.handednesses[0][0].displayName;
            gestureOutput.innerText = `GestureRecognizer: ${categoryName}\n Confidence: ${categoryScore} %\n Handedness: ${handedness}`;
            updateDetectedWords([categoryName]);
        } else {
            gestureOutput.style.display = "none";
        }
    } else {
        gestureOutput.style.display = "none";
    }
    if (webcamRunning === true) {
        window.requestAnimationFrame(predictWebcam);
    }
}

// Forming sentences with detected words
let detectedWords = [];

// Update detectedWords with newWords, allowing non-consecutive duplicates
function updateDetectedWords(newWords) {
    for (const word of newWords) {
        if (detectedWords.length > 0 && word === detectedWords[detectedWords.length - 1]) {
            continue; // Skip consecutive duplicates
        }
        detectedWords.push(word);
        speak(word); // Speak the detected word
    }

    // Update displayed text
    const sentences = formSentences(detectedWords);
    document.getElementById("detectedText").innerText = sentences;
}

// Function to form sentences from detected words
function formSentences(words) {
    let sentence = words.join(' ');
    return sentence;
}

// Text-to-Speech function
function speak(text) {
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 0.9; 
    utterance.pitch = 0.9; 
    utterance.volume = 1; 

    // Select a more human-like voice
    const voices = speechSynthesis.getVoices();
    const selectedVoice = voices.find(voice => voice.name.includes("Natural") || voice.name.includes("Google US English"));
    if (selectedVoice) {
        utterance.voice = selectedVoice;
    }

    speechSynthesis.speak(utterance);
}

// Ensure voices are loaded before speaking
speechSynthesis.onvoiceschanged = () => {
    speak("Initialization complete.");
};

// Event listener for copying formed sentences to clipboard
document.getElementById("copyButton").addEventListener("click", function () {
    const text = formSentences(detectedWords);
    navigator.clipboard.writeText(text).then(function () {
        alert('Text copied to clipboard');
        speak("Text copied to clipboard");
    }, function (err) {
        console.error('Could not copy text: ', err);
    });
});

// Event listener for model selection
document.getElementById('modelSelect').addEventListener('change', async function () {
    const selectedModel = this.value;
    speak(`Model changed to ${selectedModel}. Please wait until it loads.`);
    localStorage.setItem('selectedModel', selectedModel);
    location.reload();
});

// Wait for model to load and speak a message
window.addEventListener('load', () => {
    if (gestureRecognizer) {
        speak("Model loaded successfully");
    }
});

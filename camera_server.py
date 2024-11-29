from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import cv2
import threading
import asyncio

# Initialize FastAPI app
app = FastAPI()

# Set up CORS
origins = [
    "*",  # Update with specific allowed origins if needed
    "http://localhost",
    "http://127.0.0.1",
    "http://oa-s421-09.fast.sheridanc.on.ca",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Thread-safe frame buffer
frame_lock = threading.Lock()
current_frame = None

# Video capture initialization
video_capture = cv2.VideoCapture(0)  # Use 0 for the default camera

# Thread function to continuously capture video frames
def camera_stream():
    global current_frame
    while video_capture.isOpened():
        success, frame = video_capture.read()
        if success:
            _, buffer = cv2.imencode(".jpg", frame)
            with frame_lock:
                current_frame = buffer.tobytes()
        else:
            break

# Start the camera thread
camera_thread = threading.Thread(target=camera_stream, daemon=True)
camera_thread.start()

# Async generator for video frames
async def video_stream():
    while True:
        with frame_lock:
            if current_frame:
                frame = current_frame
                yield (b"--frame\r\n"
                       b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n")
        await asyncio.sleep(0.03)  # Control frame rate

@app.get("/video_feed")
async def video_feed():
    return StreamingResponse(video_stream(), media_type="multipart/x-mixed-replace; boundary=frame")

@app.on_event("shutdown")
def shutdown_event():
    video_capture.release()  # Release the video capture on shutdown

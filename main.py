from fastapi import FastAPI, HTTPException, Path, Response
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List
from robot import Robot
from dynamixel import Dynamixel
import cv2
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import threading
import asyncio

# Initialize FastAPI app
app = FastAPI()

# Set up CORS
origins = [
    "*",
    "http://localhost",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://oa-s421-09.fast.sheridanc.on.ca:8000",
    "http://oa-s421-09.fast.sheridanc.on.ca"
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

# Configure robots
robots = {
    "arm1": Robot(Dynamixel.Config(baudrate=1_000_000, device_name="COM5").instantiate(), servo_ids=[1, 2, 3, 4, 5, 6]),
    "arm2": Robot(Dynamixel.Config(baudrate=1_000_000, device_name="COM6").instantiate(), servo_ids=[1, 2, 3, 4, 5, 6]),
}

# Define the data model for incoming position data
class Position(BaseModel):
    positions: List[int]

class ServoID(BaseModel):
    servo_id: int

# Serve static files (e.g., HTML, CSS, JS)
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def read_index():
    return FileResponse("static/index.html")

@app.get("/video_feed")
async def video_feed():
    return StreamingResponse(video_stream(), media_type="multipart/x-mixed-replace; boundary=frame")

@app.get("/{arm_id}/current_position/")
def get_current_position(arm_id: str = Path(..., description="The ID of the robot arm (e.g., 'arm1' or 'arm2')")):
    if arm_id not in robots:
        raise HTTPException(status_code=404, detail="Robot arm not found")
    try:
        pos = robots[arm_id].read_position()
        return {"current_position": pos}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/{arm_id}/set_position/")
def set_position(arm_id: str, position: Position):
    if arm_id not in robots:
        raise HTTPException(status_code=404, detail="Robot arm not found")
    try:
        robots[arm_id].set_goal_pos(position.positions)
        return {"message": f"Position set successfully for {arm_id}", "target_position": position.positions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/{arm_id}/reboot/")
def reboot_motor(arm_id: str, servo_id: ServoID):
    if arm_id not in robots:
        raise HTTPException(status_code=404, detail="Robot arm not found")
    motor_id = servo_id.servo_id
    try:
        if motor_id not in robots[arm_id].servo_ids:
            raise HTTPException(status_code=404, detail="Motor ID not found in specified robot arm")
        robots[arm_id].reboot(motor_id)
        return {"message": f"Motor {motor_id} on {arm_id} rebooted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.on_event("shutdown")
def shutdown_event():
    video_capture.release()  # Release the video capture on shutdown

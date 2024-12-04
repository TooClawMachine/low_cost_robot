from fastapi import FastAPI, HTTPException, Path, Response
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List
from robot import Robot
from dynamixel import Dynamixel
import cv2
from fastapi.middleware.cors import CORSMiddleware
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

# Configure robots
robots = {
    "arm1": Robot(Dynamixel.Config(baudrate=1_000_000, device_name="COM6").instantiate(), servo_ids=[1, 2, 3, 4, 5, 6]),
    "arm2": Robot(Dynamixel.Config(baudrate=1_000_000, device_name="COM5").instantiate(), servo_ids=[1, 2, 3, 4, 5, 6]),
}

# Define the data model for incoming position data
class Position(BaseModel):
    positions: List[int]

class ServoID(BaseModel):
    servo_id: int

# Serve static files (e.g., HTML, CSS, JS)
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def read_index():
    return FileResponse("static/index.html")

@app.get("/current_position/{arm_id}/")
async def get_current_position(arm_id: str = Path(..., description="The ID of the robot arm (e.g., 'arm1' or 'arm2')")):
    if arm_id not in robots:
        raise HTTPException(status_code=404, detail="Robot arm not found")
    try:
        pos = await asyncio.to_thread(robots[arm_id].read_position)
        return {"current_position": pos}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/{arm_id}/set_position/")
async def set_position(arm_id: str, position: Position):
    if arm_id not in robots:
        raise HTTPException(status_code=404, detail="Robot arm not found")
    try:
        await asyncio.to_thread(robots[arm_id].set_goal_pos, position.positions)
        return {"message": f"Position set successfully for {arm_id}", "target_position": position.positions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/{arm_id}/reboot/")
async def reboot_motor(arm_id: str, servo_id: ServoID):
    if arm_id not in robots:
        raise HTTPException(status_code=404, detail="Robot arm not found")
    motor_id = servo_id.servo_id
    try:
        if motor_id not in robots[arm_id].servo_ids:
            raise HTTPException(status_code=404, detail="Motor ID not found in specified robot arm")
        await asyncio.to_thread(robots[arm_id].reboot, motor_id)
        return {"message": f"Motor {motor_id} on {arm_id} rebooted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.on_event("shutdown")
async def shutdown_event():
    print("Shutting down...")


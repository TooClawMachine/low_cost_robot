from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List
from robot import Robot
from dynamixel import Dynamixel
import os
from fastapi.middleware.cors import CORSMiddleware


# Initialize FastAPI app
app = FastAPI()

# Set up CORS
origins = [
    "*",
    "http://localhost",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://oa-s421-09.fast.sheridanc.on.ca:8000",  # Specific origin causing issues
    "http://oa-s421-09.fast.sheridanc.on.ca"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,          # List of allowed origins
    allow_credentials=True,
    allow_methods=["*"],            # Allow all HTTP methods
    allow_headers=["*"],            # Allow all headers
)

# Set up Dynamixel and Robot instances
# leader_dynamixel = Dynamixel.Config(baudrate=1_000_000, device_name='COM5').instantiate()
# leader = Robot(leader_dynamixel, servo_ids=[1, 2, 3, 4, 5, 6])
# leader.set_trigger_torque()

follower_dynamixel = Dynamixel.Config(baudrate=1_000_000, device_name='COM6').instantiate()
follower = Robot(follower_dynamixel, servo_ids=[1, 2, 3, 4, 5, 6])

# Define the data model for incoming position data
class Position(BaseModel):
    positions: List[int]

class ServoID(BaseModel):
    servo_id: int

# Serve static files (e.g., HTML, CSS, JS)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Define the HTML page endpoint
@app.get("/")
def read_index():
    return FileResponse("static/index.html")

# Endpoint to get the current position of the follower robot
@app.get("/current_position/")
def get_current_position():
    try:
        pos = follower.read_position()
        return {"current_position": pos}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Endpoint to set the follower robot's position
@app.post("/set_position/")
def set_position(position: Position):
    try:
        follower.set_goal_pos(position.positions)
        return {"message": "Position set successfully", "target_position": position.positions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Endpoint to reboot a specific motor
@app.post("/reboot/")
def reboot_motor(servo_id: ServoID):
    motor_id = servo_id.servo_id
    try:
        if motor_id not in follower.servo_ids:
            raise HTTPException(status_code=404, detail="Motor ID not found in follower robot")
        
        follower.reboot(motor_id)
        return {"message": f"Motor {motor_id} rebooted successfully"}
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=str(e))



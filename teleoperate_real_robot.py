from robot import Robot
from dynamixel import Dynamixel

leader_dynamixel = Dynamixel.Config(baudrate=1_000_000, device_name='COM5').instantiate()
follower_dynamixel = Dynamixel.Config(baudrate=1_000_000, device_name='COM6').instantiate()
follower = Robot(follower_dynamixel, servo_ids=[1, 2, 3, 4, 5, 6])
leader = Robot(leader_dynamixel, servo_ids=[1, 2, 3, 4, 5, 6])
leader.set_trigger_torque()


while True:
    follower.set_goal_pos(leader.read_position())

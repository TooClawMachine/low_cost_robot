# Change dynamixel servo's baud rate on windows platform
# This is one of the steps assembling the low-cost robot arm using dynamixel servo: https://github.com/AlexanderKoch-Koch/low_cost_robot/tree/main
# Search for step "Set the baudrate to 1M for all motors"

from dynamixel_sdk import *  # Uses Dynamixel SDK library

# Control table address for baud rate (specific to Dynamixel model, this example uses AX/MX series address)
ADDR_BAUD_RATE = 8  # Address may vary based on your model; check your Dynamixel's documentation.

# Protocol version
PROTOCOL_VERSION = 2.0  # Use 2.0 if your model supports it (e.g., X-series motors)

# Default settings
DEVICE_PORT = "COM5"       # Set to your USB2Dynamixel or serial adapter port (e.g., "COM3")
BAUDRATE = 57600           # Current baud rate, known and valid for initial connection
DXL_ID = 1                 # ID of your Dynamixel
NEW_BAUDRATE = 3           # For 1,000,000 bps (check your model's documentation if a different value is needed)

# Initialize PortHandler and PacketHandler
port_handler = PortHandler(DEVICE_PORT)
packet_handler = PacketHandler(PROTOCOL_VERSION)

# Open port
if not port_handler.openPort():
    print("Failed to open the port")
    quit()

# Set port baudrate to the current known baud rate for initial connection
if not port_handler.setBaudRate(BAUDRATE):
    print("Failed to set the port baudrate")
    quit()

# Write the new baud rate to the Dynamixel
dxl_comm_result, dxl_error = packet_handler.write1ByteTxRx(
    port_handler, DXL_ID, ADDR_BAUD_RATE, NEW_BAUDRATE
)

if dxl_comm_result != COMM_SUCCESS:
    print(f"Communication error: {packet_handler.getTxRxResult(dxl_comm_result)}")
elif dxl_error != 0:
    print(f"Dynamixel error: {packet_handler.getRxPacketError(dxl_error)}")
else:
    print("Baud rate changed successfully to 1,000,000 bps!")

# Close port
port_handler.closePort()

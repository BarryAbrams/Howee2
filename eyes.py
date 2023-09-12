import math, random, time, struct, fcntl, io
import threading
import numpy as np
from utils.servo_hat import PiServoHatWrapper

import socketio

sio = socketio.Client()

# Constants for the person sensor
PERSON_SENSOR_I2C_ADDRESS = 0x62
PERSON_SENSOR_I2C_HEADER_FORMAT = "BBH"
PERSON_SENSOR_I2C_HEADER_BYTE_COUNT = struct.calcsize(PERSON_SENSOR_I2C_HEADER_FORMAT)
PERSON_SENSOR_FACE_FORMAT = "BBBBBBbB"
PERSON_SENSOR_FACE_BYTE_COUNT = struct.calcsize(PERSON_SENSOR_FACE_FORMAT)
PERSON_SENSOR_FACE_MAX = 4
PERSON_SENSOR_RESULT_FORMAT = PERSON_SENSOR_I2C_HEADER_FORMAT + "B" + PERSON_SENSOR_FACE_FORMAT * PERSON_SENSOR_FACE_MAX + "H"
PERSON_SENSOR_RESULT_BYTE_COUNT = struct.calcsize(PERSON_SENSOR_RESULT_FORMAT)
I2C_CHANNEL = 1
I2C_PERIPHERAL = 0x703

class Eyes:
    def __init__(self):
        self.pos = 128,128
        self.socketio = None
        self.emit_pos = 0,0
        self.emit_pos_prev = 1,1
        self.target_pos = 0,0
        self.servos = PiServoHatWrapper()
        self.timestamp = time.time()
        self.last_jump_time = time.time()

        # Initialize I2C connection for the person sensor
        self.i2c_handle = io.open("/dev/i2c-" + str(I2C_CHANNEL), "rb+", buffering=0)
        fcntl.ioctl(self.i2c_handle, I2C_PERIPHERAL, PERSON_SENSOR_I2C_ADDRESS)
        DEBUG_MODE_ADDRESS = 0x07
        DEBUG_MODE_VALUE = 0x00
        # self.i2c_handle.write(bytearray([DEBUG_MODE_ADDRESS, DEBUG_MODE_VALUE]))

        self.eyes_thread = threading.Thread(target=self._run)
        self.eyes_thread.start()

        self.servo_thread = threading.Thread(target=self.servos._run)
        self.servo_thread.start()

        # self.servos.deactivate()
        self.servos.activate()
        
    def _run(self):
        while True:
            # self.look_for_person()  # Call the method to look for a person
            # self.look_for_person_alternate()
            self.look_by_controls()
            self.emit_state()
            self.move_eyes()
            time.sleep(0.05)
            
    def look_for_person(self):
        try:
            read_bytes = self.i2c_handle.read(PERSON_SENSOR_RESULT_BYTE_COUNT)
            offset = 0
            (pad1, pad2, payload_bytes) = struct.unpack_from(PERSON_SENSOR_I2C_HEADER_FORMAT, read_bytes, offset)
            offset += PERSON_SENSOR_I2C_HEADER_BYTE_COUNT
            (num_faces,) = struct.unpack_from("B", read_bytes, offset)
            offset += 1

            # For now, we'll just move the eyes based on the first detected face
            if num_faces > 0:
                (box_confidence, box_left, box_top, box_right, box_bottom, id_confidence, id, is_facing) = struct.unpack_from(PERSON_SENSOR_FACE_FORMAT, read_bytes, offset)
                # Adjust the eyes' position based on the detected face (you can modify this logic as needed)
                self.pos = box_left, box_top

        except OSError as error:
            
            print("No person sensor data found")
            print(error)

    def look_for_person_alternate(self):
        # Get the current time
        current_time = time.time()

        # Check if 5 seconds have passed since the last jump
        if current_time - self.last_jump_time > 5:
            # Choose a new starting point at least 50 away in x and y directions
            x = self.pos[0] + random.choice([-1, 1]) * random.randint(50, 100)
            y = self.pos[1] + random.choice([-1, 1]) * random.randint(50, 100)

            # Clamp the values to ensure they are within the 0-255 range
            x = self.clamp(x, 50, 200)
            y = self.clamp(y, 50, 200)

            self.pos = x, y
            self.last_jump_time = current_time
        else:
            # Continue the random walk
            x, y = self.pos
            dx = random.choice([-3, 0, 3])
            dy = random.choice([-3, 0, 3])
            x = self.clamp(x + dx, 0, 255)
            y = self.clamp(y + dy, 0, 255)
            self.pos = x, y

    def look_by_controls(self):
        x = self.target_pos[0]
        y = self.target_pos[1]
        self.pos = x, y

    def move_eyes(self):
        self.servos.move_eyes(self.pos[0]/255, self.pos[1]/255)

    def _clamp(self, value, range):
        return value/255 * range

    @staticmethod
    def clamp(value, min_value, max_value):
        """Ensure the value stays within the given range."""
        return max(min_value, min(max_value, value))

    def emit_state(self):
        if self.socketio:
            xPos = math.floor(self._clamp(self.pos[0], 8.8))
            yPos = math.floor(self._clamp(self.pos[1], 8.8))
            self.emit_pos = xPos, yPos
            if self.emit_pos != self.emit_pos_prev:
                self.socketio.emit('eyes_change', {'xPos': xPos, "yPos":yPos})
            self.emit_pos_prev = self.emit_pos

WAIT_TIME = 5  # in seconds

def connect_to_server():
    while True:
        try:
            sio.connect('http://localhost:8080')
            print("Connected to server!")
            break
        except socketio.exceptions.ConnectionError as e:
            print(f"Failed to connect to server. Waiting for {WAIT_TIME} seconds before retrying.")
            time.sleep(WAIT_TIME)

if __name__ == '__main__':
  
    eyes = Eyes()

    @sio.on('connect')
    def on_connect():
        sio.emit('message', 'Hello from client!')

    @sio.on('on_pause_blinks')
    def on_pause_blinks(data):
        eyes.servos.pause_blinking()
        print("pause_blinks")

    @sio.on('on_resume_blinks')
    def on_resume_blinks(data):
        eyes.servos.resume_blinking()
        eyes.servos.blink()
        print("resume_blinks")

    @sio.on('on_eye_update')
    def eye_update(data):

        if data["awake_state"] == "awake":
            eyes.servos.activate()
            print("open eyes")
        elif data["awake_state"] == "asleep":
            eyes.servos.deactivate()
            print("close eyes")
       
        print('Eye update:', data)

    @sio.on('eye_position')
    def eye_position(data):
        eyes.target_pos = int(data["x"]), int(data["y"])

        print('Eye update:', data)

    @sio.on('emotion_selected')
    def emotion_selected(data):
        if data == "sleep":
            eyes.servos.deactivate()
        elif data == "idle":
            eyes.servos.activate()
            eyes.servos.opening = 0.5
        elif data == "surprised":
            eyes.servos.activate()
            eyes.servos.opening = 0.85
        elif data == "thinking":
            eyes.servos.activate()
            eyes.servos.opening = 0.3

        print('Emotion:', data)

    connect_to_server()

 
   
    
import time
import board
import busio
import threading
import adafruit_bh1750
import adafruit_lis3dh
import socketio

class LightSensor:
    def __init__(self, i2c):
        self.sensor = adafruit_bh1750.BH1750(i2c)
        self.lux = 0

    def get_lux(self):
        self.lux = self.sensor.lux
        return self.lux 

    def get_label(self):
        lux = self.get_lux()

        if lux < 4:
            return "Dark"
        elif lux < 300:
            return "Light"
        else:
            return "Bright Light"

class MovementSensor:
    def __init__(self, i2c):
        if hasattr(board, "ACCELEROMETER_SCL"):
            i2c = busio.I2C(board.ACCELEROMETER_SCL, board.ACCELEROMETER_SDA)
            self.lis3dh = adafruit_lis3dh.LIS3DH_I2C(i2c, address=0x19)
        else:
            self.lis3dh = adafruit_lis3dh.LIS3DH_I2C(i2c)

        self.lis3dh.range = adafruit_lis3dh.RANGE_2_G
        self.x, self.y, self.z = 0, 0, 0
        self.previous_x, self.previous_y, self.previous_z = 0, 0, 0


    def detect_movement(self, threshold=0.4):
        current_values = [self.x, self.y, self.z]
        previous_values = [self.previous_x, self.previous_y, self.previous_z]
        for curr, prev in zip(current_values, previous_values):
            if abs(curr - prev) > threshold:
                return True
        return False

    def update_values(self):
        self.x, self.y, self.z = [
            value / adafruit_lis3dh.STANDARD_GRAVITY for value in self.lis3dh.acceleration
        ]
        return [self.x, self.y, self.z]

    def get_movement(self):
        return self.detect_movement()

    def update_prev(self):
        self.previous_x, self.previous_y, self.previous_z = self.x, self.y, self.z

class GpioManager:
    def __init__(self, i2c):
        self.i2c_address = 0x42
        self.i2c = i2c
        self.set_animation_state(1) 

    def set_neopixel_color(self, red, green, blue):
        self.i2c.writeto(self.i2c_address, bytes([red, green, blue]))

    def set_animation_state(self, animation_code):
        print("ANIMATION STATE", animation_code)
        self.i2c.writeto(self.i2c_address, bytes([animation_code]))

    def read_button_states(self):
        buffer = bytearray(2)
        try:
            self.i2c.readfrom_into(self.i2c_address, buffer)
            button1_pressed = buffer[0] == 0  # True if first button is pressed (LOW)
            button2_pressed = buffer[1] == 0  # True if second button is pressed (LOW)
            return button1_pressed, button2_pressed
        except OSError:
            return False, False  # Return False for both buttons if there's an error reading


class Sensors:
    def __init__(self):
        self.i2c = board.I2C()
        self.lightSensor = LightSensor(self.i2c)
        self.movementSensor = MovementSensor(self.i2c)
        self.gpio = GpioManager(self.i2c)
        self.socketio = None
        self.last_emit_time = time.time()
        self.total_lux = 0
        self.total_gforces = [0, 0, 0]  # For x, y, and z
        self.num_samples = 0
        self.motion_triggered = False
        self.button1_triggered = False
        self.button2_triggered = False

    def run(self):
        while True:
            button1_pressed, button2_pressed = self.gpio.read_button_states()
            
            light = self.lightSensor.get_label()
            lux = self.lightSensor.get_lux()
            gforces = self.movementSensor.update_values()
            motion = self.movementSensor.get_movement()

            self.total_lux += lux
            self.total_gforces = [self.total_gforces[i] + gforces[i] for i in range(3)]
            self.num_samples += 1

            if button1_pressed:
                self.button1_triggered = True
            if button2_pressed:
                self.button2_triggered = True


            if motion:
                self.motion_triggered = True
                
            else: 
                self.motion_triggered = False
               
            if not self.socketio:
                print(f"Light: {light}, Lux:{lux}, Movement: {motion}, Button1 Pressed: {button1_pressed}, Button2 Pressed: {button2_pressed}")

            self.movementSensor.update_prev()

            current_time = time.time()
            if current_time - self.last_emit_time >= 0.25:
                average_lux = self.total_lux / self.num_samples
                average_gforces = [value / self.num_samples for value in self.total_gforces]
                
                if self.socketio:
                    self.socketio.emit('sensors_update', {'light': light, 'lux': average_lux, "motion": self.motion_triggered, "gforces": average_gforces, "button1": self.button1_triggered, "button2": self.button2_triggered})

                self.last_emit_time = current_time
                self.total_lux = 0
                self.total_gforces = [0, 0, 0]
                self.num_samples = 0
                self.button1_triggered = False
                self.button2_triggered = False
                self.motion_triggered = False

            time.sleep(1/10)

def connect_to_server():
    while True:
        try:
            sio.connect('http://localhost:8080')
            print("Connected to server!")
            break
        except socketio.exceptions.ConnectionError as e:
            # print(f"Failed to connect to server. Waiting for {5} seconds before retrying.")
            time.sleep(5)

if __name__ == '__main__':
    sio = socketio.Client()
    sensors = Sensors()

    @sio.on('connect')
    def on_connect():
        sensors.socketio = sio
        sio.emit('message', 'Hello from client!')

    @sio.on('state_change')
    def state_change(data):
        print(data)
        if data["awake_state"] == "AWAKE":
            if data["action_state"] == "IDLE":
                sensors.gpio.set_animation_state(3)
            if data["action_state"] == "TALKING":
                sensors.gpio.set_animation_state(4)
            if data["action_state"] == "PROCESSING":
                sensors.gpio.set_animation_state(5)
            if data["action_state"] == "LISTENING":
                sensors.gpio.set_animation_state(3)

        else:
            sensors.gpio.set_animation_state(2)

    sensor_thread = threading.Thread(target=sensors.run)
    sensor_thread.start()

    connect_to_server()

import pi_servo_hat
import time, threading, random

class PiServoHatWrapper:
    def __init__(self, frequency=100):
        self.servo_hat = pi_servo_hat.PiServoHat()
        self.servo_hat.restart()
        self.servo_hat.set_pwm_frequency(frequency)

        self.x_axis = ServoController(self, 0, 10, 170)
        self.y_axis = ServoController(self, 1, 30, 120)
        self.rt_eyelid = ServoController(self, 2, 135, 10) # right top (180, 0)
        self.rb_eyelid = ServoController(self, 4, 10, 160) # right bottom (180, 0)
        self.lt_eyelid = ServoController(self, 3, 10, 130) # left top (180, 0)
        self.lb_eyelid = ServoController(self, 5, 130, 10) # left bottom (180,0)

        self.last_move_time = 0
        self.last_center_x = None
        self.last_center_y = None

        self.blinking_thread = None
        self.state = 'unblinking'

        self.active = True

        self.current_positions = {
            self.x_axis: 0.5,
            self.y_axis: 0.5,
            self.rt_eyelid: 0.5,
            self.lt_eyelid: 0.5,
            self.rb_eyelid: 0.5,
            self.lb_eyelid: 0.5
        }

        self.target_positions = None
        self.blink_start_time = None

        # self.thread = threading.Thread(target=self._run)
        # self.thread.start()

    def _run(self):
        while True:
            start_time = time.time()
            speed = .25

            if self.state == 'blinking':
                speed = .9
                if not self.blink_start_time:
                    self.blink_start_time = start_time

                self.target_positions = [(self.rt_eyelid, 0), (self.rb_eyelid, 0), (self.lt_eyelid, 0),  (self.lb_eyelid, 0)]

                if start_time - self.blink_start_time > 0.1:  # Adjust this duration as needed
                    self.blink_start_time = None  # Reset the blink start time
                    self.state = 'unblinking_after_blink'

            elif self.state == 'unblinking_after_blink':
                speed = .7
                self.target_positions = self.calculate_eyelid_positions(self.y_axis.get_current_position())
                self.state = 'unblinking'
            elif self.state == 'close':
                speed = .9
                if not self.blink_start_time:
                    self.blink_start_time = start_time

                self.target_positions = [(self.rt_eyelid, 0), (self.rb_eyelid, 0), (self.lt_eyelid, 0),   (self.lb_eyelid, 0)]


            if self.target_positions is not None:
                for servo, target_position in self.target_positions:
                    current_position = self.current_positions[servo]
                    new_position = current_position + speed * (target_position - current_position)
                    self.current_positions[servo] = new_position
                    servo.move_to_position(new_position)
                    
            time.sleep(0.01)
            
    def activate(self):
        print("ACTIVATE")
        self.state = "unblinking"
        # self.blinking_thread_stop = False  # Reset the flag
        self.active = True
        self.servo_hat.wake()
        self.start_blinking()

    def deactivate(self):
        print("DEACTIVATE")
        self.state = "close"
        self.active = False
        self.stop_blinking()  # Stop the blinking thread
        self.move_eyes(0.5, 0.5)  # Move eyes to center
        servo_positions = [(self.rt_eyelid, 0), (self.lt_eyelid, 0), (self.rb_eyelid, 0), (self.lb_eyelid, 0)]
        self.target_positions = servo_positions  # Close eyelids

        timer = threading.Timer(5.0, self.servo_hat.sleep)
        timer.start()

    def update_person_position(self, position):
        if self.active:
            if position is not None:
                x, y = position
                # print("x:", x/255, "y:", y/255)
                self.move_eyes(x/255, y/255)

    def start_blinking(self):
        if not self.blinking_thread:
            print("start blinking")
            self.blinking_thread = threading.Thread(target=self.random_blink)
            self.blinking_thread.daemon = True  # Set as a daemon thread so it will close when the main program closes
            self.blinking_thread.start()

    def stop_blinking(self):
        if self.blinking_thread:
            print("stop blinking")
            self.unblink()
            self.blinking_thread_stop = True  # Signal the thread to stop
            self.blinking_thread = None

    def random_blink(self):
        self.blinking_thread_stop = False
        while not self.blinking_thread_stop:
            total_sleep = random.uniform(2, 10)
            sleep_elapsed = 0

            while sleep_elapsed < total_sleep and not self.blinking_thread_stop:
                time.sleep(0.1)  # sleep in small chunks
                sleep_elapsed += 0.1

            if not self.blinking_thread_stop:
                self.blink()
            

    def move_servo_position(self, channel, angle, duration):
        self.servo_hat.move_servo_position(channel, angle, duration)

    def unblink(self):
        servo_positions = self.calculate_eyelid_positions(self.y_axis.get_current_position())
        smooth_move_servos(servo_positions, 5)

    def blink(self):
        self.state = 'blinking'

    def natural_blink(self):
        servo_positions = [(self.rt_eyelid, 0), (self.lt_eyelid, 0), (self.rb_eyelid, 0), (self.lb_eyelid, 0)]
        smooth_move_servos(servo_positions, 5)
        servo_positions = self.calculate_eyelid_positions(self.y_axis.get_current_position())
        smooth_move_servos(servo_positions, 5)

        # Pause for a brief moment to simulate the eyes being closed
        time.sleep(0.1)

        servo_positions = [(self.rt_eyelid, 0), (self.lt_eyelid, 0), (self.rb_eyelid, 0), (self.lb_eyelid, 0)]
        smooth_move_servos(servo_positions, 20)
        servo_positions = self.calculate_eyelid_positions(self.y_axis.get_current_position())
        smooth_move_servos(servo_positions, 20)

    def move_eyes(self, x_position, y_position):
        inverted_x = 1 - x_position
        adjusted_y = min(1, y_position * 1.15)  # Adjust y_position and make sure it's <= 1
        inverted_y = 1 - adjusted_y

        eye_positions = [(self.x_axis, inverted_x), (self.y_axis, inverted_y)]
        eyelid_positions = self.calculate_eyelid_positions(inverted_y)
        servo_positions = eye_positions + eyelid_positions
        self.target_positions = servo_positions

    def calculate_eyelid_positions(self, y_position):
        offset = (y_position - 0.5) * .5
        top_eyelid_position = 0.5 + offset
        bottom_eyelid_position = 0.5 - offset
        return [(self.rt_eyelid, top_eyelid_position), (self.lt_eyelid, top_eyelid_position),
                (self.rb_eyelid, bottom_eyelid_position), (self.lb_eyelid, bottom_eyelid_position)]

class ServoController:
    def __init__(self, servo_hat, channel, min_angle=0, max_angle=180):
        self.channel = channel
        self.min_angle = min_angle
        self.max_angle = max_angle
        self.servo_hat = servo_hat
        self.current_angle = (self.min_angle + self.max_angle) / 2  # Initialize to midpoint of range
        self.previous_smoothed_position = self.get_current_position()  # Initialize with current position
        self.alpha = 0.05  # You can adjust this value for desired smoothness
        # self.move_to_center()

    def get_current_position(self):
        # Assuming the current angle is stored in self.current_angle
        return (self.current_angle - self.min_angle) / (self.max_angle - self.min_angle)

    def move_to_center(self):
        self.move_to_position(0.5)
        time.sleep(.15)

    def move_to_angle(self, angle):
        if angle < min(self.min_angle, self.max_angle):
            angle = min(self.min_angle, self.max_angle)
        elif angle > max(self.min_angle, self.max_angle):
            angle = max(self.min_angle, self.max_angle)

        self.servo_hat.move_servo_position(self.channel, angle, 180)
        self.current_angle = angle  # Store the current angle

    def move_to_position(self, position):
        if position < 0:
            position = 0
        elif position > 1:
            position = 1

        angle_range = self.max_angle - self.min_angle
        angle = self.min_angle + position * angle_range
        self.move_to_angle(angle)

    def smooth_move_to_position(self, target_position, duration=1.0):
        start_time = time.time()
        end_time = start_time + duration

        print("smooth move to position")

        while time.time() < end_time:
            elapsed_time = time.time() - start_time
            t = elapsed_time / duration
            desired_position = self.get_current_position() + t * (target_position - self.get_current_position())

            # Apply the smoothing (EMA) algorithm
            smoothed_position = (desired_position * self.alpha) + (self.previous_smoothed_position * (1 - self.alpha))

            self.move_to_position(smoothed_position)
            self.previous_smoothed_position = smoothed_position  # Update the previous value

            time.sleep(0.01)  # Adjust the sleep time for the desired speed

        # Ensure the final position is reached
        self.move_to_position(target_position)


def smooth_move_servos(servo_positions, steps=100, delay_time=0.01):
    def move_servo(servo, target_position):
        current_position = servo.get_current_position()
        
        for step in range(steps + 1):
            t = step / steps
            eased_t = t**2 * (3 - 2 * t)
            position = current_position + eased_t * (target_position - current_position)
            servo.move_to_position(position)
            time.sleep(delay_time)
        
        servo.move_to_position(target_position)
    
    # threads = [threading.Thread(target=move_servo, args=sp) for sp in servo_positions]
    # for thread in threads:
    #     thread.start()
    # for thread in threads:
    #     thread.join()
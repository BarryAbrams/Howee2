import math, random, time
import threading
import numpy as np


class Eyes:
    def __init__(self):
        self.pos = 128,128
        self.socketio = None
        self.thread = threading.Thread(target=self._run)
        self.thread.start()
        self.emit_pos = 0,0
        self.emit_pos_prev = 1,1

    def _run(self):
        while True:
            amplitude = 50
            xPos = (np.sin(time.time())/2 * amplitude) + amplitude/2
            yPos = (np.sin(time.time()/2)/2 * amplitude) + amplitude/2
            self.pos = xPos + (255/2 - amplitude/2), yPos + (255/2 - amplitude/2)
            self.emit_state()
            time.sleep(0.033)
            

    def look_for_person(self):
        # Implementation
        pass

    def move_eyes(self):
        # Implementation
        pass

    def _clamp(self, value, range):
        return value/255 * range

    def emit_state(self):
        if self.socketio:
            xPos = math.floor(self._clamp(self.pos[0], 8.8))
            yPos = math.floor(self._clamp(self.pos[1], 8.8))
            self.emit_pos = xPos, yPos
            if self.emit_pos != self.emit_pos_prev:
                self.socketio.emit('eyes_change', {'xPos': xPos, "yPos":yPos})
            self.emit_pos_prev = self.emit_pos

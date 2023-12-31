from .base import Knowledge

from threading import Timer

import sys
sys.path.append("..")  # Adds higher directory to python modules path.

from _utils import *

class System(Knowledge):
    def __init__(self, transition_state_callback):
        super().__init__(transition_state_callback)


    def query(self, input):
        if input == "volume_up":
            self._adjust_volume("up")
            return "Volume increased."
        
        elif input == "volume_down":
            self._adjust_volume("down")
            return "Volume decreased."
        
        elif input == "mute":
            self._mute_volume()
            return "Volume muted."
        
        elif input == "unmute":
            self._unmute_volume()
            return "Volume unmuted."

        elif input == "sleep":
            self._sleep()
            return "Go To Sleep."
        
        
        else:
            return f"I'm sorry, I don't recognize the command '{input}'."

    def _adjust_volume(self, direction):
        if direction == "up":
            print_c("Volume +", "red")
            # Logic to increase volume
            pass
        elif direction == "down":
            print_c("Volume -", "red")
            # Logic to decrease volume
            pass
    
    def _mute_volume(self):
        print_c("Muted", "red")
        # Logic to mute volume
        pass

    def _unmute_volume(self):
        print_c("Unmuted", "red")
        # Logic to unmute volume
        pass

    def _sleep(self):
        print_c("Sleep", "red")

        pass
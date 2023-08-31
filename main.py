import eventlet, threading, cProfile
eventlet.monkey_patch()

from _utils import *

from brain import Brain
from gui import GUI

def boot_systems():
    print_c("Check the Tires and Light the Fires...", "magenta")
    # Initialize motors, sensors, flask, database, etc.
    pass

if __name__ == '__main__':
  
    brain = Brain()
    gui = GUI(brain)
    brain.socketio = gui.socketio
    brain.start()
    set_socketio_instance(gui.socketio)
    gui.run()
    
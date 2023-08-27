from _utils import *

from brain import Brain

def boot_systems():
    print_c("Check the Tires and Light the Fires...", "magenta")
    # Initialize motors, sensors, flask, database, etc.
    pass

if __name__ == "__main__":
    boot_systems()
    brain = Brain("terminal")
    brain.start()

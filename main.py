from brain import Brain

def boot_systems():
    # Initialize motors, sensors, flask, database, etc.
    pass

if __name__ == "__main__":
    boot_systems()
    brain = Brain("terminal")
    brain.start()

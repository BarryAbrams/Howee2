from enum import Enum

socketio = None

def set_socketio_instance(sio):
    global socketio
    socketio = sio

class AwakeState(Enum):
    AWAKE = 1
    ASLEEP = 2

    def to_json(self):
        return self.name

class ActionState(Enum):
    TALKING = 1
    PROCESSING = 2
    LISTENING = 3
    IDLE = 4

    def to_json(self):
        return self.name

def print_c(text, color="white"):
    color_codes = {
        "black": "\033[30m",
        "red": "\033[31m",
        "green": "\033[32m",
        "yellow": "\033[33m",
        "blue": "\033[34m",
        "magenta": "\033[35m",
        "cyan": "\033[36m",
        "white": "\033[37m"
    }
    reset_code = "\033[0m"
    
    print(f"{color_codes[color]}{text}{reset_code}")


def input_c(text, color="yellow"):
    color_codes = {
        "black": "\033[30m",
        "red": "\033[31m",
        "green": "\033[32m",
        "yellow": "\033[33m",
        "blue": "\033[34m",
        "magenta": "\033[35m",
        "cyan": "\033[36m",
        "white": "\033[37m"
    }
    reset_code = "\033[0m"
    
    return input(f"\n{color_codes[color]}{text}{reset_code}\n")

def stop_signal():
    socketio.emit('response', {'type':"stop" })


def howee_speak(text):
    if text:
        print_c("HOWEE: " + text, "cyan")
        socketio.emit('response', {'type':"incoming", 'from':"Howee", "message":text})

def you_speak(text):
    if text:
        print_c("YOU: " + text, "green")
        socketio.emit('response', {'type':"outgoing", 'from':"You", "message":text})
        stop_signal()
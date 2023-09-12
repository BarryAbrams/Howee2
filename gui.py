from flask import Flask, jsonify, request, render_template
from flask_socketio import SocketIO
from _utils import *  
import subprocess

class GUI:
    def __init__(self, brain):
        self.app = Flask(__name__)
        self.socketio = SocketIO(self.app)
        self.brain = brain
    
        self.setup_routes()
        print("GUI STARTED")
        self.socketio.emit('on_eye_update', {'awake_state':"asleep"})

    def setup_routes(self):
        @self.app.route('/')
        def index():
            return render_template('index.html')

        @self.socketio.on('sensors_update')
        def handle_sensors_update(data):
            # Relay the data to all connected clients
            self.socketio.emit('sensors_update', data)

        @self.socketio.on('send-input')
        def handle_send_input(data):
            user_input = data['input']
            self.brain.user_input = user_input
            
        @self.socketio.on('request-state')
        def request_state():
            # print("state")
            self.brain.emit_state()
            # self.brain.eyes.emit_state()
            self.brain.mouth.emit_state()
            self.emit_current_volume()

        @self.socketio.on('on_eye_position')
        def on_eye_position(data):
            self.socketio.emit('eye_position', data)

        @self.socketio.on('on_emotion_selected')
        def on_emotion_selected(data):
            self.socketio.emit('emotion_selected', data)

        @self.socketio.on('set-volume')
        def handle_set_volume(data):
            volume_percentage = float(data['volume']) / 100.0
            self.brain.mouth.set_alsa_volume(volume_percentage)
            self.emit_current_volume()

        @self.socketio.on('set-awake-state')
        def handle_set_awake_state(data):
            if data["state"] == "sleep":
                if self.brain.awake_state != AwakeState.ASLEEP:
                    self.brain.transition(AwakeState.ASLEEP, ActionState.LISTENING)
            if data["state"] == "wake":
                if self.brain.awake_state != AwakeState.AWAKE:
                    self.brain.transition(AwakeState.AWAKE, ActionState.LISTENING)
                    self.brain.user_input = "hey howee"


    def emit_current_volume(self):
        self.socketio.emit('system_volume', {'volume': self.brain.mouth.volume * 100})

    def run(self):
        print("GUI RUN")

        self.socketio.run(self.app, host='0.0.0.0', port=8080, debug=False)



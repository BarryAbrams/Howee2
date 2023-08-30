from flask import Flask, jsonify, request, render_template
from flask_socketio import SocketIO
from _utils import *  

class GUI:
    def __init__(self, brain):
        self.app = Flask(__name__)
        self.socketio = SocketIO(self.app)
        self.brain = brain
        self.setup_routes()
        print("GUI STARTED")

    def setup_routes(self):
        @self.app.route('/')
        def index():
            return render_template('index.html')

        @self.socketio.on('send-input')
        def handle_send_input(data):
            user_input = data['input']
            self.brain.user_input = user_input
            
        @self.socketio.on('request-state')
        def request_state():
            # print("state")
            self.brain.emit_state()
            self.brain.eyes.emit_state()
            self.brain.mouth.emit_state()

    def run(self):
        print("GUI RUN")

        self.socketio.run(self.app, host='0.0.0.0', port=8080, debug=False)



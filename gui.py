from flask import Flask, jsonify, request, render_template
from flask_socketio import SocketIO
from _utils import *  

class GUI:
    def __init__(self, brain):
        self.app = Flask(__name__)
        self.socketio = SocketIO(self.app)
        self.brain = brain
        self.setup_routes()

    def setup_routes(self):
        @self.app.route('/')
        def index():
            # Assuming the HTML file is named 'index.html' and is located in a 'templates' directory.
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

        # Add other routes as needed.

    def run(self):

        self.socketio.run(self.app, host='0.0.0.0', port=5000, debug=False)



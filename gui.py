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
            
            # Pass the user input to the Brain instance for processing
            self.brain.user_input = user_input
            self.brain.transition(AwakeState.AWAKE, ActionState.PROCESSING)
            
            # Emit a response back to the client
            self.socketio.emit('response', {'response': 'Received: ' + user_input})

        # Add other routes as needed.

    def run(self):
        self.socketio.run(self.app, debug=True)



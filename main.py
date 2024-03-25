from flask import Flask, render_template, request
from flask import session, redirect
from flask_socketio import join_room, leave_room, send, SocketIO
# The following two imports are used for generating room codes.
import random
from string import ascii_uppercase

app = Flask(__name__)

app.config["SECRET_KEY"] = "ourkey"
# Initialize the socketio server.
socketio = SocketIO(app)

@app.route("/", methods=["POST", "GET"])
def home():
    return render_template("home.html")

if __name__ == "__main__":
    socketio.run(app, debug=True)
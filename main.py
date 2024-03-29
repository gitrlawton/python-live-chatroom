from flask import Flask, render_template, request
from flask import session, redirect, url_for
from flask_socketio import join_room, leave_room, send, SocketIO
# The following two imports are used for generating room codes.
import random
from string import ascii_uppercase

app = Flask(__name__)

app.config["SECRET_KEY"] = "ourkey"
# Initialize the socketio server.
socketio = SocketIO(app, logger=True, engineio_logger=True)

# Dictionary to hold our list of existing rooms.
rooms = {}

def generate_unique_code(length):
    while True:
        code = ""
        # _ signifies we don't care what we call this variable (ie. i, index, etc.)
        for _ in range(length):
            # Choose a random ascii uppercase character and append it to the
            # code string.
            code += random.choice(ascii_uppercase)
        
        # Check if the code we generated is not one that is already in use in
        # our dictionary.
        if code not in rooms:
            break
        # Otherwise, the while loop will continue -- creating an entirely new
        # code.
        
    return code
    
@app.route("/", methods=["POST", "GET"])
def home():
    # Clear the session when user navigates to the homepage.
    session.clear()
    
    if request.method == "POST":
        # Extract the form data.  The .get() method will attempt to grab
        # the value associated with the key in quotes.  If no value for the
        # key is found, it will return None by default.  You can choose to
        # return something else by including what you'd like to return in
        # the case of no value, like False, by specifying it after the key.
        name = request.form.get("name")
        code = request.form.get("code")
        join = request.form.get("join", False)
        create = request.form.get("create", False)
        # If name was not sent with form...
        if not name:
            # Render the home page and pass an error to it.  Also repass the
            # values for name and code back to the template so the user doesn't
            # need to type them again.
            return render_template("home.html", error="Please enter a name.", code=code, name=name)
        # If user tried to join without entering a room code...
        if join != False and not code:
            # Render the home page and pass an error to it.  Also repass the
            # values for name and code back to the template so the user doesn't
            # need to type them again.
            return render_template("home.html", error="Please enter a room code.", code=code, name=name)
        room = code
        # At this point, the user provided a name and entered a room code.
        # Hence, figure out what room they want to join.
        # !room = code!
        # If they want to create a room...
        if create != False:
            # Generate room code of length 4.
            room = generate_unique_code(4)
            # Create a new entry in dictionary of rooms.  The new room is empty
            # and has no messages in it yet.
            rooms[room] = {"members": 0, "messages": []}
        # Otherwise, if the room code they provided to join is not in the
        # dictionary...
        elif code not in rooms:
            return render_template("home.html", error="Room does not exist.", name=name, code=code)
        # Temporary user data that's semi-permanently stored on the server.
        # This way we don't need the user to retype their name or room code 
        # every time they refresh the page.
        session["room"] = room
        session["name"] = name  
        # Redirect user to the page for the chat room they are joining.
        return redirect(url_for("room"))
        
    # This line is only going to happen if the method was not a POST request.
    # Therefore, we don't need to pass any variables back to the template.    
    return render_template("home.html")

@app.route("/room")
def room():
    room = session.get("room")
    # Running some checks to prevent user from accessing the /room url path by
    # bypassing the homepage's join room/create room functionality and typing
    # localhost:5000/room directly into the navigation bar.
    if room is None or session.get("name") is None or room not in rooms:
        # Keep redirecting them to the home page.
        return redirect(url_for("home"))
    # Otherwise, redirect them to the room page. Pass the room code and the list
    # of messages in the room already.
    return render_template("room.html", code=room, messages=rooms[room]["messages"])

# Here on the server, handle the message and retransmit it to everyone in the
# chat room.
@socketio.on("message")
def message(data):
    # Find out the room the user sent the message from.
    room = session.get("room")
    # If user is sending a message from a room that is not valid, do nothing.
    if room not in rooms:
        return
    # Otherwise, the message we want to retransmit will contain the sender's
    # name and their message.
    content = {
        "name": session.get("name"),
        "message": data["data"]
    }
    # Send message we just constructed.
    send(content, to=room)
    # Add the message to the list of messages in the room.
    rooms[room]["messages"].append(content)
    # Console log for debugging.
    print(f"{session.get('name')} said: {data['data']}")

# Decorator using the socketio instance we initialized at the top.
# Function to handle user joining a room.
@socketio.on("connect")
def connect(auth):
    # Look in the session for the user's room and the user's name.
    room = session.get("room")
    name = session.get("name")
    # Check to make sure they have a name and a room to avoid errors.
    # They don't have one or the other, do nothing.
    if not room or not name:
        return
    # If they have a room but its not a valid room number, make them leave it.
    if room not in rooms:
        # Built-in Socketio method.
        leave_room(room)
        return
    
    # At this point, their name and room are valid.
    # Built-in Socketio method.
    join_room(room)
    # Send a json message to everyone in the room that a user joined.
    # Built-in Socketio method.
    send({"name": name, "message": "has entered the room."}, to=room)
    # Increase room user count by 1.
    rooms[room]["members"] += 1

# Function to handle user leaving room.
@socketio.on("disconnect")
def disconnect():
    room = session.get("room")
    name = session.get("name")
    leave_room(room)
    
    if room in rooms:
        # Decrease room members count by 1.
        rooms[room]["members"] -= 1
        # If there are no users left in the room, delete the room.  This way
        # we're not storing empty rooms.
        if rooms[room]["members"] <= 0:
            del rooms[room]
    # Send message to everyone in the room that a user left.        
    send({"name": name, "message": "has left the room."}, to=room)
    
    

if __name__ == "__main__":
    socketio.run(app, debug=True)
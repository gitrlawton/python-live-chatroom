from flask import Flask, render_template, request
from flask import session, redirect, url_for
from flask_socketio import join_room, leave_room, send, SocketIO
# The following two imports are used for generating room codes.
import random
from string import ascii_uppercase

app = Flask(__name__)

app.config["SECRET_KEY"] = "ourkey"
# Initialize the socketio server.
socketio = SocketIO(app)

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
    # Otherwise, redirect them to the room page.
    return render_template("room.html")

if __name__ == "__main__":
    socketio.run(app, debug=True)
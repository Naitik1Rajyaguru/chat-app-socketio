from flask import Flask, render_template, request, session, redirect, url_for
from flask_socketio import join_room, leave_room, send, SocketIO
import random
from string import ascii_uppercase

# data base :
# rooms dic which will have number of people and massage and other stufs, you can accesss member by using chat room name
rooms = {}

# generate random room code
def generate_room_code(length):
    while True:
        code =''
        for _ in range(length):
            code += random.choice(ascii_uppercase)
        if code not in rooms:
            break
    return code



# create app
app = Flask(__name__)
app.config['SECRET_KEY'] = "randomstring"
socketio = SocketIO(app)

#create route
@app.route('/', methods=['POST', 'GET'])
def home():

    # this is kind of session for store temoporary data
    session.clear()
    # print(request.form) :- this are name :- in the form that you have setup :- like get those attributes
    # so we will create this for all
    if request.method == 'POST':
        name = request.form.get("name")
        chatroom = request.form.get("chatroom")
        join = request.form.get("join", False) # :- this will be boolean (click or not click)
        create = request.form.get("create", False)

        # user must have enter name
        if not name:
            return (render_template("home.html", error = "please enter name", name=name, chatroom=chatroom)) # :- this error massage will send to home.html and it will get error variable(this is possible in python html(django html)) and put it there
        if (join != False) and (not chatroom):
            return (render_template("home.html", error = "please enter chat room name", name=name, chatroom=chatroom)) # :- here name chatroom will be pass as variable :- the vaiable which we have define in html
        
        # create room, you dont need to provide room name :- it will just create room with random if :- when you join room you should enter correct room id        
        room = chatroom
        
        if create != False:       
            room = generate_room_code(4)
            rooms[room] = {"members": 0, "massages": []}
        # room name wrong    
        elif chatroom not in rooms:
            return render_template("home.html", error = "room is not exist", name=name, chatroom=chatroom)
        
        session["room"] = room
        session["name"] = name
        
        return redirect(url_for("room"))
    


        
    return render_template("home.html")


@app.route('/room')
def room():

    # you cant directly enter by /room :- you need to have details as above (should have room created and it should be on this session)
    room = session.get("room")
    print(room)
    if (room is None) or (session.get("name") is None) or (room not in rooms):
        print("f")
        return redirect(url_for("home"))

    return render_template("room.html", chatroom = room, messages = rooms[room]['massages'])  # this is for title and massages that we are passing in room.html


# in room we have initilized socket io().
# when that accures we connect to room.
@socketio.on("connect")
def connect(auth):
    room = session.get("room")
    name = session.get("name")

    if (not room) or (not name):
        return
    if room not in rooms:
        leave_room(room)
        return

    join_room(room)
    # this send, join_room, leave_room is method in socket that we imported above
    send({
        "name" : name, 
        "message":"has join the room"}, to=room)
    rooms[room]["members"] += 1
    print(f"{name} join {room}")



@socketio.on("get_message")
def get_message(data):
    room = session.get("room")
    name = session.get("name")
    if room not in rooms:
        return

    content={
        "name": name,
        "message": data["data"]
    }
    send(content, to=room)
    rooms[room]["massages"].append(content)
    print(f"{name} send {data['data']}")


# now when you refresh or go back this will work (cause we are working on session)
@socketio.on("disconnect")
def disconnect():
    room = session.get("room")
    name = session.get("name")
    leave_room(room)

    # now if there is only one person and he goes back or refresh he will be disconnected from room and re route to home page :- cause rooom will be deleted.
    # now if there is more then one person and one of them goes back, only he will be disconnected :- on refreshing page there will be nothing happend
    if room in rooms:
        rooms[room]["members"] -= 1
        if rooms[room]["members"] <=0 :
            print(f"{room} is deleted")
            del rooms[room]
    send({
        "name" : name, 
        "message":"has left the room"}, to=room)
    print(f"{name} left {room}")
    

    


if __name__ == "__main__":
    socketio.run(app, debug=True) # debug :- dont need to refresh every time

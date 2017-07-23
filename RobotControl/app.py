#!/usr/bin/env python

# Robot controller, modified from the example provided in the Flask-SocketIO
# GitHub repo.
# Modified by Evan Simkowitz (esimkowitz@wustl.edu), July 2017

import argparse
from camera_pi import Camera
from flask import Flask, render_template, session, request, Response
from flask_socketio import SocketIO, emit, join_room, leave_room, \
    close_room, rooms, disconnect

# Import the Robot.py file (must be in the same directory as this file!).
try:
    import Robot
    is_robot = True
except ImportError:
    print("No robot available")
    is_robot = False
    pass

# Set the trim offset for each motor (left and right).  This is a value that
# will offset the speed of movement of each motor in order to make them both
# move at the same desired speed.  Because there's no feedback the robot doesn't
# know how fast each motor is spinning and the robot can pull to a side if one
# motor spins faster than the other motor.  To determine the trim values move the
# robot forward slowly (around 100 speed) and watch if it veers to the left or
# right.  If it veers left then the _right_ motor is spinning faster so try
# setting RIGHT_TRIM to a small negative value, like -5, to slow down the right
# motor.  Likewise if it veers right then adjust the _left_ motor trim to a small
# negative value.  Increase or decrease the trim value until the bot moves
# straight forward/backward.
LEFT_TRIM = 0
RIGHT_TRIM = 0


# Create an instance of the robot with the specified trim values.
# Not shown are other optional parameters:
#  - addr: The I2C address of the motor HAT, default is 0x60.
#  - left_id: The ID of the left motor, default is 1.
#  - right_id: The ID of the right motor, default is 2.
try:
    robot = Robot.Robot(left_trim=LEFT_TRIM, right_trim=RIGHT_TRIM)
except:
    if is_robot:
        raise RuntimeError("Unknown error with robot")
    else:
        pass

# Set this variable to "threading", "eventlet" or "gevent" to test the
# different async modes, or leave it set to None for the application to choose
# the best option based on installed packages.

parser = argparse.ArgumentParser(description='Robot controller.')
parser.add_argument('-p', '--public', dest="is_public", action="store_true",
                    help='set flag to make the server public-facing')
args = parser.parse_args()

host = '0.0.0.0' if args.is_public else None

async_mode = None

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode=async_mode)


def gen(camera):
    """Video streaming generator function."""
    while True:
        frame = camera.get_frame()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


@app.route('/')
def index():
    return render_template('index.html', async_mode=socketio.async_mode)


@socketio.on('control_event', namespace='/test')
def test_message(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response',
         {'data': message['data'], 'count': session['receive_count']})
    print("Message recieved: %s" % message['data'])
    if message['data'] == 'Forward':
        try:
            robot.forward(75)
        except:
            if is_robot:
                raise RuntimeError("Unknown error with robot")
            else:
                pass
        print("robot forward")
    elif message['data'] == 'Backward':
        try:
            robot.backward(75)
        except:
            if is_robot:
                raise RuntimeError("Unknown error with robot")
            else:
                pass
        print("robot backward")
    elif message['data'] == 'Left':
        try:
            robot.left(75)
        except:
            if is_robot:
                raise RuntimeError("Unknown error with robot")
            else:
                pass
        print("robot left")
    elif message['data'] == 'Right':
        try:
            robot.right(75)
        except:
            if is_robot:
                raise RuntimeError("Unknown error with robot")
            else:
                pass
        print("robot right")
    elif message['data'] == 'Stop':
        try:
            robot.stop()
        except:
            if is_robot:
                raise RuntimeError("Unknown error with robot")
            else:
                pass
        print("robot stopped")


@app.route('/video_feed')
def video_feed():
    """Video streaming route. Put this in the src attribute of an img tag."""
    return Response(gen(Camera()),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


@socketio.on('join', namespace='/test')
def join(message):
    join_room(message['room'])
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response',
         {'data': 'In rooms: ' + ', '.join(rooms()),
          'count': session['receive_count']})


@socketio.on('leave', namespace='/test')
def leave(message):
    leave_room(message['room'])
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response',
         {'data': 'In rooms: ' + ', '.join(rooms()),
          'count': session['receive_count']})


@socketio.on('disconnect_request', namespace='/test')
def disconnect_request():
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response',
         {'data': 'Disconnected!', 'count': session['receive_count']})
    disconnect()


@socketio.on('connect', namespace='/test')
def test_connect():
    emit('my_response', {'data': 'Connected'})


@socketio.on('disconnect', namespace='/test')
def test_disconnect():
    print('Client disconnected', request.sid)


if __name__ == '__main__':
    socketio.run(app, host, debug=True)

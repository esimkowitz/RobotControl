#!/usr/bin/env python

# Robot controller, modified from the example provided in the Flask-SocketIO
# GitHub repo.
# Modified by Evan Simkowitz (esimkowitz@wustl.edu), July 2017


import argparse
from flask import Flask, render_template, session, request, Response

import sys
import io
import os
import shutil
import picamera
import signal
import urllib

from subprocess import Popen, PIPE, check_output
from string import Template
from struct import Struct
from threading import Thread
from time import sleep, time
from wsgiref.simple_server import make_server
from ws4py.websocket import WebSocket
from ws4py.server.wsgirefserver import WSGIServer, WebSocketWSGIRequestHandler
from ws4py.server.wsgiutils import WebSocketWSGIApplication

# Import the Robot.py file (must be in the same directory as this file!).
try:
    import Robot
    is_robot = True
except ImportError:
    print("No robot available")
    is_robot = False
    pass


###########################################
# CONFIGURATION
WIDTH = 640
HEIGHT = 480
FRAMERATE = 24
HTTP_PORT = 8082
WS_PORT = 8084
COLOR = u'#444'
BGCOLOR = u'#333'
JSMPEG_MAGIC = b'jsmp'
JSMPEG_HEADER = Struct('>4sHH')
###########################################

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

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
app.debug = False
app.threading = True


class StreamingWebSocket(WebSocket):
    def opened(self):
        self.send(JSMPEG_HEADER.pack(JSMPEG_MAGIC, WIDTH, HEIGHT), binary=True)


class BroadcastOutput(object):
    def __init__(self, camera):
        print('Spawning background conversion process')
        self.converter = Popen([
            'avconv',
            '-f', 'rawvideo',
            '-pix_fmt', 'yuv420p',
            '-s', '%dx%d' % camera.resolution,
            '-r', str(float(camera.framerate)),
            '-i', '-',
            '-f', 'mpeg1video',
            '-b', '800k',
            '-r', str(float(camera.framerate)),
            '-'],
            stdin=PIPE, stdout=PIPE, stderr=io.open(os.devnull, 'wb'),
            shell=False, close_fds=True)

    def write(self, b):
        self.converter.stdin.write(b)

    def flush(self):
        print('Waiting for background conversion process to exit')
        self.converter.stdin.close()
        self.converter.wait()


class BroadcastThread(Thread):
    def __init__(self, converter, websocket_server):
        super(BroadcastThread, self).__init__()
        self.converter = converter
        self.websocket_server = websocket_server

    def run(self):
        try:
            while True:
                buf = self.converter.stdout.read(512)
                if buf:
                    self.websocket_server.manager.broadcast(buf, binary=True)
                elif self.converter.poll() is not None:
                    break
        finally:
            self.converter.stdout.close()


class Server():
    def __init__(self):
        # Create a new server instance
        print("Initializing camera")
        self.camera = picamera.PiCamera()
        self.camera.resolution = (WIDTH, HEIGHT)
        self.camera.framerate = FRAMERATE
        # hflip and vflip depends on how you mount the camera
        self.camera.vflip = True
        self.camera.hflip = True
        sleep(1)  # camera warm-up time
        print("Camera ready")

    def __str__(self):
        # Return string representation of server
        ip_addr = check_output(['hostname', '-I']).decode().strip()
        return "Server video stream at http://{}:{}".format(ip_addr, HTTP_PORT)

    def start(self):
        # Start video server streaming
        print('Initializing websockets server on port %d' % WS_PORT)
        self.websocket_server = make_server(
            '', WS_PORT,
            server_class=WSGIServer,
            handler_class=WebSocketWSGIRequestHandler,
            app=WebSocketWSGIApplication(handler_cls=StreamingWebSocket))
        self.websocket_server.initialize_websockets_manager()
        self.websocket_thread = Thread(
            target=self.websocket_server.serve_forever)
        print('Initializing Flask thread')
        self.flask_server = make_server(
            '', 5000,
            app=app)
        self.flask_thread = Thread(
            target=self.flask_server.serve_forever)
        print('Initializing broadcast thread')
        output = BroadcastOutput(self.camera)
        self.broadcast_thread = BroadcastThread(
            output.converter, self.websocket_server)
        print('Starting recording')
        self.camera.start_recording(output, 'yuv')
        print('Starting websockets thread')
        self.websocket_thread.start()
        print('Starting Flask thread')
        self.flask_thread.start()
        print('Starting broadcast thread')
        self.broadcast_thread.start()
        print("Video Stream available...")
        while True:
            self.camera.wait_recording(1)

    def cleanup(self):
        # Stop video server - close browser tab before calling cleanup
        print('Stopping recording')
        self.camera.stop_recording()
        print('Waiting for broadcast thread to finish')
        self.broadcast_thread.join()
        print('Shutting down Flask server')
        self.flask_server.shutdown()
        print('Waiting for Flask thread to finish')
        self.flask_thread.join()
        print('Shutting down websockets server')
        self.websocket_server.shutdown()
        print('Waiting for websockets thread to finish')
        self.websocket_thread.join()


@app.context_processor
def inject_canvas_size():
    return dict(canvas_size=dict(width=WIDTH, height=HEIGHT))


@app.context_processor
def inject_canvas_color():
    return dict(color=COLOR)


@app.context_processor
def inject_broadcast_address():
    return dict(address='%s:%d' % (check_output(['hostname', '-I']).decode().strip(), WS_PORT))


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/control_event', methods=['POST'])
def control_event():
    if request.method == 'POST':
        control = request.form['control']
        if control == 'f':
            try:
                robot.forward(75)
            except:
                if is_robot:
                    raise RuntimeError("Unknown error with robot")
                else:
                    pass
            print("robot forward")
        elif control == 'b':
            try:
                robot.backward(75)
            except:
                if is_robot:
                    raise RuntimeError("Unknown error with robot")
                else:
                    pass
            print("robot backward")
        elif control == 'l':
            try:
                robot.left(75)
            except:
                if is_robot:
                    raise RuntimeError("Unknown error with robot")
                else:
                    pass
            print("robot left")
        elif control == 'r':
            try:
                robot.right(75)
            except:
                if is_robot:
                    raise RuntimeError("Unknown error with robot")
                else:
                    pass
            print("robot right")
        elif control == 's':
            try:
                robot.stop()
            except:
                if is_robot:
                    raise RuntimeError("Unknown error with robot")
                else:
                    pass
            print("robot stop")
    return 'OK'


def main():
    server = Server()

    def endProcess(signum=None, frame=None):
        # Called on process termination.
        if signum is not None:
            SIGNAL_NAMES_DICT = dict((getattr(signal, n), n) for n in dir(
                signal) if n.startswith('SIG') and '_' not in n)
            print("signal {} received by process with PID {}".format(
                SIGNAL_NAMES_DICT[signum], os.getpid()))
        print("\n-- Terminating program --")
        print("Cleaning up Server...")
        server.cleanup()
        robot.stop()
        print("Done.")
        os._exit(0)

    # Assign handler for process exit
    signal.signal(signal.SIGTERM, endProcess)
    signal.signal(signal.SIGINT, endProcess)
    signal.signal(signal.SIGHUP, endProcess)
    signal.signal(signal.SIGQUIT, endProcess)

    server.start()


if __name__ == '__main__':
    main()

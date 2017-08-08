# RobotControl

A simple controller for Raspberry Pi robots powered by the [Adafruit DC & Stepper Motor HAT](https://www.adafruit.com/product/2348).

## Installation

Use the following script to download and install RobotControl:

```bash
cd ~
git clone https://github.com/esimkowitz/RobotControl.git
cd ~/RobotControl
sudo python3 setup.py install
```

## Usage

### Getting started

To run RobotControl, use the following script:

```bash
cd ~/RobotControl/RobotControl
python3 app.py
```

This will start the webserver on port ``5000``.

To use the controller, open a browser and navigate to ``http://<Pi's IP address>:5000``, replacing ``<Pi's IP address>`` with the IP address of your Raspberry Pi.

Please note that I've only tested this with the Pi and the controlling device on the same WiFi network.

### The Controls

The controller displays a low-latency video stream from the Pi's camera.

The controls work on desktops and multi-touch devices. On desktops, the best way to control the robot is using the arrow or WASD keys. On mobile/multi-touch devices, the best way to control the robot is to drag your finger along the screen in the direction you want the robot to move. 

Dragging your finger along the screen will enable a joystick that can be used to control the robot. This works on both touchscreens and by clicking-and-dragging with the mouse, but it's really meant for touchscreens.

### Stopping the program

Stop RobotControl at any time by pressing ``Ctrl-C`` in the terminal window.

## Questions/Concerns

Please open an issue if you run into trouble.

## Acknowledgements

Thanks to yoannmoinet's [nipplejs](https://github.com/yoannmoinet/nipplejs) library for the joystick functionality.

Thanks to waveform80's [pistreaming](https://github.com/waveform80/pistreaming) demo for the low-latency video streaming.

Thanks to phoboslab's [jsmpeg](https://github.com/phoboslab/jsmpeg) library for the Javascript video decoder.
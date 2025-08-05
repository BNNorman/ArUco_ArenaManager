# Testing In progress - do not use just yet

# ArUco_ArenaManager
Python code to manage a pixelbot game arena using ArUco markers

Find out about pixelbots from [CrazyRobMiles](http://hullpixelbot.com/)

# Intro
The arena has a number of robot bases on opposite sides of the arena/field each marked with a unique ArUco marker.

Each pixelbot will also have a unique ArUco marker.

There is a seperate marker to aid for compensation for camera to arena distance, which is used for detecting a ball.

At the start of the AreanaManager.py program the bases and robots are identified and each bot is randomly assigned to a 'team' and base. The pixelbots are then sent MQTT messages to tell them where the home base is and they are expected to find there way there using a 'pythonish' program loaded into the bots.

The ArenaManager.py will transmit current co-ordinates of the pixelbots and the ball. It is upto the pythonish program, in each pixelbot, to get the ball into the opponents 'net' - basically the opponent base line.

Flask is used to stream the camera frames to any browser on the network.

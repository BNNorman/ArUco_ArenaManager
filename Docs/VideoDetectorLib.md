# VideoDetectorLib.py

As the name suggests, this module captures a new frame from the camera and uses the picamera2 library.

It uses the aruco DICT_6x6_250 to match markers found on the arena, robots and any other markers in view.

## grabFrame()
Identifies any 6x6 markers in the field of view and returns the video frame with markers annotated

Must be called frequently to update the markers found

## getFrame()

Just returns the current annotated frame and is intended for Flask streaming.

## getMarkers()

Returns the markers found as a dict

import os

from Code.ArenaManager import aruco_detector

print(os.path)

# import the necessary packages
import json
from imutils.video import VideoStream
from flask import Response
from flask import Flask
from flask import render_template
import threading
import VideoDetectorLib
import cv2
import time

lock=threading.Lock()

videoDetector=None # set from ArenaManager

FRAME_WIDTH=640
FRAME_HEIGHT=480

outputFrame=None

# initialize a flask object
app = Flask(__name__)

@app.route("/")
def index():
    # return the rendered template
    # must be in the 'templates' sub-dir
    return render_template("index.html")

# image processing 
def _getVideoFrame() -> Any:
    """
	_getVideoFrame()
	
    grab the current frame and resize to 640x480

    """
    # imshow doesn't like this as a memoryview
	# haven't tried imageview with video streaming
    videoFrame,_=aruco_detector.getFrame() # ignore ArUco markers

    # scale down maintaining aspect ratio
    # just making a 640 pixel wide image for streaming
    h,w=videoFrame.shape[:2]
    aspect=640/w
    newHeight=int(aspect*h)

    return cv2.resize(videoFrame, (640,newHeight), interpolation=cv2.INTER_LINEAR)


def _generate() -> Any:
    """
    Generate the video stream

    called from video_feed() below

    Also displays the image locally using opencv

    :return: Nothing
    """

    while True:
        videoFrame=_getVideoFrame()
        cv2.imshow("FlaskVideo.py",videoFrame) # comment out later

        if videoFrame is not None:
            # encode the frame in JPEG format
            (flag, encodedImage) = cv2.imencode(".jpg", videoFrame)
     
            # ensure the frame was successfully encoded
            if flag:
                # yield the output frame in the byte format
                yield(b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + bytearray(encodedImage) + b'\r\n')
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            cv2.destroyAllWindows()
            break

@app.route("/video_feed")
def video_feed():
    # return the response generated along with the specific media
    # type (mime type)
    return Response(_generate(),mimetype = "multipart/x-mixed-replace; boundary=frame")

# check to see if this is the main thread of execution
if __name__ == '__main__':

    videoDetector=VideoDetectorLib.arucoDetector()
		
    try:
        while True:
            # start the flask app
            app.run(host="0.0.0.0", port=8000, debug=True,threaded=True, use_reloader=False)

    except Exception as e:
        print(f"FlaskVideo: exception {e}")
        cv2.destroyAllWindows()
 

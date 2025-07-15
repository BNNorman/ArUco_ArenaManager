"""
Manages the start of a pixelbot game which uses ArUco markers to identify objects
in the arena used by pixelbots.

1 pixel to mm scaling is achieved by identifying a specific marker which has a known size (see config.py)
2 the arena should have no objects other than pixelbot base markers to allow the pixelbot home base markers to be found quickly
3 pixelbots and other items may then be added and identified
4 the pixelbots are then commanded to go to their base markers and face the opposing team

The arena manager then sits in a loop updating the marker positions and broadcasting them

The game logic is programmed into the pixelbots using the Pythonish interpreter which runs on the bots.
"""
# used to emit coordinates via MQTT

from config import settings

from VideoDetectorLib import arucoDetector # my handler
from MqttManager import MQTT

import sys
import cv2
import MiscLib
import time
import json

from PixelbotControl import Control

pixelbotCtrl=Control()

aruco_detector=arucoDetector()

if settings.STREAMING:
	from FlaskVideo import app as flaskApp

pixelbots={} # list of pixelbots (class instances)

class pixelbot:
	"""properties and methods for each detected pixelbot"""
	def __init__(self,botId,cx,cy,angle,team,homeX,homeY):
		self.id=botId
		self.cx=cx
		self.cy=cy
		self.angle=angle
		self.team=team
		self.homeX=homeX
		self.homeY=homeY
		self.teamColour="red" if team==0 else "blue"
		self.mqtt=MQTT()
	
	def broadcastPositionInfo(self)->None:
		"""broadcastPositionInfo
		
		create a JSON string containing this bot's position
		and send it via mqtt
		
		"""
		j={}
		j["id"]=self.id
		j["cx"]=self.cx
		j["cy"]=self.cy
		j["angle"]=self.angle
		j["team"]=self.team
		# broadcast it
		self.mqtt.publish(settings.MQTT_LOCATION_TOPIC,json.dumps(j))

	def run(selfself):
		pass

	def stop(selfself):
		pass

def get_pixelbots()->None:
	"""build pixelbot teams
	
	Alternately adds each pixelbot found to either team0 or team1
	"""
	global pixelbots # dict of bots
	
	_,markers=aruco_detector.grabFrame() # ignore video frame
	
	team=1
	playerIdx=0 # index into TEAMx_BASES
	
	for botId in markers.keys():
		if botId not in settings.PIXELBOT_ID_RANGE:
			continue
		else:
			homeBaseId=settings.TEAM1_BASES[playerIdx] if team==1 else settings.TEAM0_BASES[playerIdx]
			cx,cy,angle=markers[botId]
			homeX,homeY,_=markers[homeBaseId]
			
			# add bot to dict colour is set by the pixelbot class
			# based on team number
			pixelbots[botId]=pixelbot(botId,cx,cy,angle,team,homeX,homeY)

			teamColour=settings.TEAM1_COLOUR if team==1 else settings.TEAM2_COLOUR
			# light up the pixels to identify the teams
			pixelbotCtrl.setPixels(botId,teamColour)

			# toggle the team
			team=0 if team==1 else 1
			
			# bump the team player index
			if team==1 and playerIdx==0:
				playerIdx+=1
			
def send_bots_home():
	"""
	
	Tells each bot where it's home base is. The bots are expected to make their way
	to their home bases.
	
	Monitors the position of each bot till it gets within the home base and when
	at home tells the bot to face it's opponent.
	"""
	# first tell each bot where it's base is
	for bot in pixelbots:
		pixelbot.broadcastPositionInfo()

	# check if all bots are homes
	homed=0
	while homed<(2*settings.NUM_TEAM_BASES):
		homed=0 # restart counting
		_,markers=aruco_detector.grabFrame()
		updatePixelbots()
		for botId in pixelbots.keys():
			botX,botY,_=markers[botId]
			homeX=pixelbots[botId].homeX
			homeY=pixelbots[botId].homeY
			tolerance=5 # pixels
			if MiscLib.isHome(botX,botY,homeX,homeY,tolerance):
				homed+=1
				# turn the bot to face its opponent
				botAngle=pixelbots[botId].angle
				# bot bases at y>(arena height) should face up
				# otherwise down
				if pixelbots[botId].homeY>(settings.VIDEO_HEIGHT/2):
					# point North
					pixelbotCtrl.turn(botId,-botAngle)
				else:
					# point south
					pixelbotCtrl.turn(botId,180-botAngle)
				# stop and wait till all bots are homed
				pixelbotCtrl.stop(botId)
				
	# the bots should now be on their home bases
	# and facing the correct way and ready to start the game
	time.sleep(5)
	for botId in pixelbots.keys():
		pixelbot[botId].run()
		
def updatePixelbots()->None:
	"""updatePixelbots
	
	updates the current coordinate info of the bots and broadcasts
	the info to the actual pixelbots
	"""
	_,markers=aruco_detector.grabFrame() # ignore video frame
		
	for botId in pixelbots.keys():
		try:
			cx,cy,angle=markers[botId]
			pixelbots[botId].cx=cx
			pixelbots[botId].cy=cy
			pixelbots[botId].angle=angle
			pixelbots[botId].broadcastPositionInfo()
		except:
			pass
	
# identify pixelbots and team bases	
get_pixelbots()

# send commands to each bot to go to their home base
# returns when all done
send_bots_home()

# the game may commence according to the pythonish
# programs they have.


running=True

while running:
	
	updatePixelbots() # broadcasts current position
	
	# check states
	
	if not settings.STREAMING:
		cv2.imshow("Arena",aruco_detector.getFrame())

		if cv2.waitKey(1) & 0xFF==ord("q"):
			running=False

	
	
		
		
cv2.destroyAllWindows()

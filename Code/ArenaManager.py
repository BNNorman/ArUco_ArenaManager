# used to emit coordinates via MQTT

from settings import ARENA_ARCU_MARKERS, ARENA_ARCU_CORNERS, NUM_PLAYERS_PER_TEAM, VIDEO_HEIGHT, MQTT_TOPIC
STREAMING=False

if STREAMING:
	from FlaskVideo import app as flaskApp

from VideoDetectorLib import ARuCo # my handler

import sys
import cv2
import MiscLib

from PixelbotControl import Control

pixelbotCtrl=Control()

aruco_detector=ARuCo()

bots={}

class pixelbot:
	def __init__(self,botId,cx,cy,angle,team,homeX,homeY):
		self.id=botId
		self.cx=cx
		self.cy=cy
		self.angle=angle
		self.team=team
		self.homeX=homeX
		self.homeY=homeY
		self.teamColour="red" if team==0 else "blue"
	
	def broadcastPositionInfo(self):
		j={}
		j["id"]=self.id
		j["cx"]=self.cx
		j["cy"]=self.cy
		j["angle"]=self.angle
		j["team"]=self.team
		# broadcast it
		mqtt.publish(LOCATION_TOPIC,json.dumps(j))
	
def getPixelbots():
	# build pixelbot teams
	
	global pixelbots # dict of bots
	
	markers=aruco_detector.getMarkers() # return dict [id]=cx,cy,angle)
	
	team=1
	playerIdx=0 # index into TEAMx_BASES
	
	for botId in markers.keys():
		if botId not in PIXELBOT_ID_RANGE:
			continue
		else:
			homeBaseId=TEAM1_BASES[playerIdx] if team==1 else TEAM0_BASES[playerIdx]
			cx,cy,angle=markers[botId]
			homeX,homeY,_=markers[homeBaseId]
			
			# add bot to dict colour is set by the pixelbot class
			# based on team number
			pixelbots[botId]=pixelbot(botId,cx,cy,angle,team,homeX,homeY)
			
			# light up the pixels to identify the teams
			pixelbotCtrl.setPixels(botId,colour)

			# toggle the team
			team=0 if team==1 else 1
			
			# bump the team player index
			if team==1 and player==0:
				playerIdx+=1
			
def send_bots_home():
	# first tell each bot where it's base is
	for bot in pixelBots:
		pixelbot.publishTargetPosition(pixelbots[bot].homeX,pixelbots[bot].homeY)

	# check if all bots are homes
	Homed=0
	while homed<(2*NUM_TEAM_BASES):
		homed=0 # restart counting
		markers=aruco_detector.getMarkers() # refresh dict
		for botId in pixelbots.keys():
			botX,botY,_=markers[botId]
			homeX=pixelbots[botId].homeX
			homeY=pixelbots[botId].homeY
			tolerance=5 # pixels
			if MiscLib.isHome(botX,botY,baseX,baseY,tolerance)
				homed+=1
	# turn bots to face each other
	for botId in pixelbots.keys():
		botAngle=pixelbots[botId].angle
		# bot bases at y>(arena height) should face up
		# otherwise down
		if pixelbots[botId].homeY>(VIDEO_HEIGHT/2):
			# point North
			pixelbotCtrl.turn(botId,-botAngle)
		else:
			# point south
			pixelbotCtrl.turn(botId,180-botAngle)
		
	# the bots should be on their home bases
	# and facing the correct way
		
def updatePixelbots():
	markers=aruco_detector.getMarkers() # refresh dict
	for botId in pixelbots.keys():
		cx,cy,angle=markers[botId]
		pixelbots[botId].cx=cx
		pixelbots[botId].cy=cy
		pixelbots[botId].angle=angle
		
		
	
					
get_pixelBots() 	# locate bots, assign to teams and set home pos
send_bots_home() 	# returns when all bots are on their bases and facing North or South

# the game may commence according to the pythonish
# programs they have.


while running:
	updatePixelbots()
	
	# check states
	
	if not STREAMING:	
		cv2.imageShow("Arena",aruco_detector.getFrame())

		if cv2.waitKey(1) & 0xFF==ord("q"):
			running=False
		
	# broadcast current bot positions
	for botId in pixelbots.keys():
		pixelbots[botId].broadcastPositionInfo()
	
	
		
		
cv2.destroyAllWindows()

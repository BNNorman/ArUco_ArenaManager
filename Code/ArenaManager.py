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

from config import settings

from VideoDetectorLib import arucoDetector # my handler

import sys
import cv2
import MiscLib
import time
import json


detector=arucoDetector()

if settings.STREAMING:
	from FlaskVideo import app as flaskApp

pixelbots={} #  id-> pixelbot class instances
homeBases={}
ball=None : tuple of cx,cy positions

def off_get_pixelbots()->None:
	"""build pixelbot teams
	
	Alternately adds each pixelbot found to either team0 or team1
	"""
	global pixelbots # dict of bots
	
	print("Finding pixel")
	
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


def assignPixelbotsToTeams()->None:
	"""build pixelbot teams
	
	called after team bases and pixelbos have been found

	"""
	global pixelbots , teamBases

	team=1

	for botId,baseId in zip(pixelbots.keys(),homeBases.keys()):

		homeX,homeY,_=teamBases[baseId]
		
		# add bot to dict colour is set by the pixelbot class
		# based on team number
		pixelbots[botId]=setHomePos(homeX,homeY)

		teamColour=settings.TEAM1_COLOUR if team==1 else settings.TEAM2_COLOUR
		# light up the pixels to identify the teams
		pixelbots[botId].setTeamColour(teamColour) # also lights them up

		# toggle the team
		team=0 if team==1 else 1
				
def checkPixelbotIsHome(botId, tolerance=10):
	cx,cy,angle,team,homeX,homeY=pixelbots[botId].getProps()
	
	if MiscLib.isHome(cx,cy,homeX,homeY,tolerance):
		# turn the bot to face its opponents
		botAngle=pixelbots[botId].angle
		# bot bases at y>(arena height) should face up
		# otherwise down
		if pixelbots[botId].homeY>(settings.VIDEO_HEIGHT/2):
			# point North
			pixelbots[botId].turn(-botAngle)
		else:
			# point south
			pixelbots[botId.turn(botId,180-botAngle)
		# stop and wait till all bots are homed
		pixelbots[botId].stop()
		
def off_send_bots_home():
	"""
	Tells each bot where it's home base is. The bots are expected to make their way
	to their home bases.
	
	Monitors the position of each bot till it gets within the home base and when
	at home tells the bot to face it's opponent.
	"""
	print("Sending bots home")

	# check if all bots are homed
	print("Waiting for all bots to home")
	homed=0
	while homed<(2*settings.NUM_TEAM_BASES):
		homed=0 # restart counting
		detector.update()
		
		bots=detector.getPixelbots() # a dict cx,cy,angle
		for botId in bots:
			botX,botY,_=bots[botId]
			homeX,homeY=pixelbots[botId].getHomePos()

			if MiscLib.isHome(botX,botY,homeX,homeY):
				homed+=1
				# turn the bot to face its opponent
				curAngle=pixelbots[botId].getAngle()
				# bot bases at y>(arena height) should face up
				# otherwise down
				if homeY>(settings.VIDEO_HEIGHT/2):
					# point North
					pixelbots[botId].turn(botId,-curAngle)
				else:
					# point south
					pixelbots[botId].turn(botId,180-curAngle)
				# stop and wait till all bots are homed
				pixelbotCtrl.stop(botId)
				
	# the bots should now be on their home bases
	# and facing the correct way and ready to start the game
	time.sleep(5)
	for botId in pixelbots.keys():
		pixelbots[botId].run()
		
def updatePixelbots()->None:
	"""updatePixelbots
	
	updates the current coordinate info of the bots and broadcasts
	the info to the actual pixelbots
	"""
	markers=detector.getPixelbots() # get current pos info
	for botId in pixelbots.keys():
		cx,cy,angle=markers[botId]
		pixelbots[botId].setPos(cx,cy)
		pixelbots[botId].setAngle(angle)
		pixelbots[botId].tellPixelbot()

# the game may commence according to the pythonish
# programs they have.

print("Scanning for home bases") 
while True:
	# grab a new video frame and analyse it
	detector.update()
	homeBases=detector.getHomeBases()
	if len(homeBases.keys())==settings.NUM_TEAM_BASES:
		print("Found all home bases")
		break
		
print("Scanning for pixelbots")
while True:
	# grab a new video frame and analyse it
	detector.update()
	pixelbots=detector.getPixelbots() # a dict
	if len(pixelbots.keys()==settings.NUM_TEAM_BASES: # one bot per home base
		print("Found all pixel bots")
		break

assignPixelbotsToTeams()


print("Spot the ball")
while True:
	# grab a new video frame and analyse it
	detector.update()
	ballX,ballY=detector.getBall()
	if ballX is not None:
		break

print("Allocating pixelbots to teams and sending them home")

for botId,baseId in zip(pixelbots.keys(),homeBases.keys):
	baseX,baseY=homeBases[baseId]
	

print("Please removed base and calibration markers")

running=True

print("Game loop starting")

while running:
	detector.update()
	
	# broadcast current positions
	updatePixelbots() 		
	updateBallPosition()
	
	# check states
	
	if not settings.STREAMING:
		cv2.imshow("Arena",aruco_detector.getFrame())

		if cv2.waitKey(1) & 0xFF==ord("q"):
			running=False

	
	
		
		
cv2.destroyAllWindows()

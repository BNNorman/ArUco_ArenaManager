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
import itertools
import pixelbotClass

# game loop stages
FINDING_BASES=1
FINDING_BOTS=2
HOMING_BOTS=3
WAITING_FOR_BALL=4
PLAYING_GAME=5
STOPPED=6
FACE_OPPONENTS=7

STAGE=FINDING_BASES


detector=arucoDetector()

# just for feedback and to get the camera running
for c in range(2):
	detector.update()
	cv2.imshow("ARENA",detector.getFrame())
	cv2.waitKey(1)

if settings.STREAMING:
	from FlaskVideo import app as flaskApp
else:
	print("Not using Flask",flush=True)

lastArenaScale=detector.getScale() # used to detec camera movement

pixelbots={} #  id-> pixelbot class instances
team0HomeBases={} #  id-> cx,cy
team1HomeBases={}
arenaBounderies=[0,0,settings.VIDEO_WIDTH,settings.VIDEO_HEIGHT] # re-calculated in game loop

ballPos=(None,None) # tuple of cx,cy positions


def botBusy(botId,setBusy=False):
	"""
	busy=None means just read the status otherwise set it
	
	Has a built in timeout of 10s in case bot callback is missing
	
	"""
	if setBusy:
		# set the bot status to busy and add a timeout
		pixelbots[botId].busy=True
		pixelbots[botId].lastCmd=time.time()
		return True
	else:
		# check if still busy and add a timeout of 10s
		if pixelbots[botId].busy:
			if time.time()-pixelbots[botId].lastCmd>10:
				print(f"Busy timeout for {botId}")
				pixelbots[botId].busy=False
				return False
			# still busy
			return True
	
	
	
	
def updatePixelbots()->None:
	"""updatePixelbots
	
	updates the current coordinate info of the bot instances
	This does not send anything to the pixelbot itself therefore
	doesn't care if the hardware is busy.
	
	This info is used to calculate motion distances and angles
	"""
	for botId in list(pixelbots.keys()):
		cx,cy,heading=detector.getBotInfo(botId)
		if cx is not None:
			print(f"Update bot {botId} cx {cx} cy {cy} heading {heading}",flush=True)
			pixelbots[botId].setPos(cx,cy)
			pixelbots[botId].setHeading(heading)

	
def faceTheOpponents():

	for botId in list(pixelbots.keys()):
		
		if not botBusy(botId):
				
			homeX,homeY=pixelbots[botId].getHomePos()
			
			# bots on the left must turn to face east (90)
			# bots on the right must face west (180)
			halfWay=settings.VIDEO_WIDTH/2
			Vars={
				"angle":0,
				"dist":0 
			}
			newCourse=180 if homeX<halfWay else 90

			print(f"Turn to face opponents newCourse {newCourse} bot heading {pixelbots[botId].heading}",flush=True)
			# we only want a turn
			Vars["angle"]=MiscLib.courseChange(pixelbots[botId].heading,newCourse)
			
			botBusy(botId,True)
			pixelbots[botId].updateVariables(Vars)	
		
def createPixelbots() ->None:
	"""
	create new pixelbot instances and send them home
	"""
	global pixelbots
		
	foundBots=detector.getPixelbots() # a dict id=>(cx,cy,angle)
	homeBases=detector.getHomeBases()
	
	for botId in list(foundBots.keys()):
		# is this a new pixelbot?
		if not botId in list(pixelbots.keys()): 
			try:
				cx,cy,heading=foundBots[botId]
				if cx is not None:
					#print(f"creating bot {botId} cx {cx} cy {cy} heading {heading}",flush=True)
					pairedWith=settings.PAIRINGS[botId]
					# all home bases must be found first
					homeX,homeY=homeBases[pairedWith]

					pixelbots[botId]=pixelbotClass.pixelbot(botId,cx,cy,heading,homeX,homeY)
				else:
					print(f"cannot create bot {botId}",flush=True)
			except:
				# another bot may be covering its base
				print("Cannot locate homeBase",flush=True)

def chaseTheBall():
	"""
	calculate angles and distances to move to get to the ball
	"""
	
	for botId in list(pixelbots.keys()):
		
		if not botBusy(botId):

			Vars={
				"angle":0,
				"dist":0
			}
			cx,cy,heading=detector.getBotInfo(botId)
			if cx is None:
				continue
				
			ballX,ballY=ballPos
			
			course,distPX=MiscLib.getHeadingAndRange(cx,cy,ballX,ballY)
			
			angle=MiscLib.getCourseChange(course,heading) # already int
			dist=round(distPX/detector.getScale())
			
			if dist+angle==0: #nothing to do
				continue
			
			Vars["angle"]=angle
			Vars["dist"]=dist
			
			# the bot program should turn and move
			botBusy(botId,True)
			pixelbots[botId].updateVariables(Vars)

def sendHome(botId):
	"""
	calculate angle and distance to move
	"""
	
	if not botBusy(botId):
		
		Vars={
			"angle":0,
			"dist":0
		}
		
		# updated by the loop
		cx=pixelbots[botId].cx
		cy=pixelbots[botId].cy
				
		if cx is None: # might happen if bot has left the arena
			return
			
		homeX=pixelbots[botId].homeX
		homeY=pixelbots[botId].homeY
		course,distPX=MiscLib.getHeadingAndRange(cx,cy,homeX,homeY)
		Vars["angle"]=MiscLib.getCourseChange(course,pixelbots[botId].heading)
		Vars["dist"]=int(distPX/detector.getScale())
		
		print(f"Arena send home botId {botId} angle {Vars['angle']} dist {Vars['dist']}", flush=True)
		# the bot program should turn and move
		
		botBusy(botId,True)
		pixelbots[botId].updateVariables(Vars)
	
def allBotsHomed():
	"""
	Check if all bots are homed. Required before game can commence
	"""
	baseSideLenPX=settings.HOMEBASE_SIDELEN_MM*detector.getScale()
	
	botCount=len(list(pixelbots.keys()))
	homeCount=0
	for botId in list(pixelbots.keys()):
		if not pixelbots[botId].isHome(baseSideLenPX):
			sendHome(botId)
		else:
			homeCount+=1
	if homeCount==botCount:
		return True
	return False

def spotTheBall()->bool:
	"""
	try to locate a ball
	"""
	global ballPos
	ballX,ballY=detector.getBall()
	if ballX is not None:
		ballPos=(ballX,ballY)
	
def calcArenaBoundaries(homeBases):
	"""
	return a rectangle defining the height and width of
	the arena using position of bases in pixels
	using TEAM0_BOTS[0] and TEAM1_BOTS[0] markers
	
	settings.BOUNDARY_MARGIN us used to expand the area
	encompassed by the home markers
	
	"""
	global arenaBoundaries
	
	# all team0 bases are almost on same X and max Y pos
	# likewise for team1
    
	try:
		# find the minX,minY,maxX,maxY for the bases
		minX,minY,maxX,maxY=settings.VIDEO_WIDTH,settings.VIDEO_HEIGHT,0,0
		for baseId in list(homeBases.keys()):
			cx,cy=homeBases[baseId]
			
			minX=cx if cx<minX else minX
			minY=cy if cy<minY else minY
			maxX=cx if cx>maxX else maxX
			maxY=cy if cy>maxY else maxY
		
		arenaBoundaries=MiscLib.expandRect(minX,minY,maxX,maxY,settings.BOUNDARY_MARGIN)
	
	except Exception as e:
		print(f"CalcBoundaries exception {e}",flush=True)
	
def getTeamBases():
	"""
	splits homeBases into team  bases
	required to calculate arenaBoundaries because the arena image
	might not fill the video frame
	"""
	global team0HomeBases,team1HomeBases
	
	# do this in every looop incase camera position changes
		
	homeBases=detector.getHomeBases()
	
	for baseId in list(homeBases.keys()):
		if baseId in settings.TEAM0_BASES:
			team0HomeBases[baseId]=homeBases[baseId]
		else:
			team0HomeBases[baseId]=homeBases[baseId]
			
	calcArenaBoundaries(homeBases) # gets arena rect
	
	return len(homeBases.keys())
			
#########################################
#
#  Main Arena Loop
#
########################################


FINDING_BASES=1
FINDING_BOTS=2
HOMING_BOTS=3
WAITING_FOR_BALL=4
PLAYING_GAME=5
STOPPED=6
FACE_OPPONENTS=7

STAGE=FINDING_BASES

print("Game loop starting.",flush=True)

print("Finding bases",flush=True)

while STAGE!=STOPPED:
	detector.update()
	spotTheBall() # updates ball pos
	
	if STAGE==FINDING_BASES:
		numBases=getTeamBases()
		if numBases==len(settings.TEAM0_BASES+settings.TEAM1_BASES):
			print("Finding bots",flush=True)
			STAGE=FINDING_BOTS

	elif STAGE==FINDING_BOTS:
		createPixelbots() # only creates new bots
		botsFound=len(list(pixelbots.keys()))	
		if botsFound==settings.NUM_BOTS:
			print("Homing bots",flush=True)
			STAGE=HOMING_BOTS
			
	elif STAGE==HOMING_BOTS:
		updatePixelbots()
		for botId in list(pixelbots.keys()):
			sendHome(botId)
			
		if allBotsHomed():
			# as soon as the ball appears it's game on
			print("Turn to face opponents",flush=True)
			STAGE=FACE_OPPONENTS
			
	elif STAGE==FACE_OPPONENTS:
		updatePixelbots()
		faceTheOpponents()
		STAGE=WAITING_FOR_BALL
			
	elif STAGE==WAITING_FOR_BALL:
		ballX,ballY=ballPos
		if ballX is None:
			pass
		else:
			print("Got a ball. Playing game",flush=True)
			STAGE=PLAYING_GAME
		
		
	elif STAGE==PLAYING_GAME:
		updatePixelbots()
		chaseTheBall()
		
		ballX,ballY=ballPos
		
		if ballX is None:
			# ball has left the arena
			print("Waiting for new ball",flush=True)
			STAGE=WAITING_FOR_BALL

	
	if not settings.STREAMING:
		cv2.imshow("ARENA",detector.getFrame())

	key=cv2.waitKey(1) & 0xFF
	
	if key==ord("q"): # quit
		STAGE=STOPPED
	
		
cv2.destroyAllWindows()
sys.stdout=oldStdOut

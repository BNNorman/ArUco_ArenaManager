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
import logging
import pixelbotClass

logger = logging.getLogger(__name__)

# start a fresh log for each run
logging.basicConfig(filename='ArenaManager.log', filemode="w",level=logging.INFO)
logger.info('Started')


detector=arucoDetector()

# just for feedback and to get the camera running
for c in range(2):
	detector.update()
	cv2.imshow("ARENA",detector.getFrame())
	cv2.waitKey(1)

if settings.STREAMING:
	from FlaskVideo import app as flaskApp
else:
	logger.info("Not using Flask")


pixelbots={} #  id-> pixelbot class instances
homeBases={}
ballPos=(None,None) # tuple of cx,cy positions


def assignPixelbotsToBases()->None:
	"""build pixelbot teams
	
	called after team bases and pixelbos have been found

	"""
	global pixelbots , teamBases

	team=1

	for botId,baseId in itertools.zip_longest(pixelbots.keys(),homeBases.keys()):
		if botId is None:
			logger.info("Not all bases have bots")
			return
			
		if baseId is None:
			logger.info("Not enough bases. Too many bots")
			return 

		homeX,homeY,_=homeBases[baseId]
		
		# add bot to dict colour is set by the pixelbot class
		# based on team number
		pixelbots[botId].setHomePos(homeX,homeY)

		teamColour=settings.TEAM1_COLOUR if team==1 else settings.TEAM0_COLOUR
		# light up the pixels to identify the teams
		pixelbots[botId].setTeamColour(teamColour) # also lights them up

		# toggle the team
		team=0 if team==1 else 1
				
		
def send_bots_home()->None:
	"""
	Tells each bot where it's home base is. The bots are expected to make their way
	to their home bases.
	
	Monitors the position of each bot till it gets within the home base and when
	at home tells the bot to face it's opponent.
	"""
	logger.info("Sending bots home")
	
	# each bot runs separately
	for id in list(pixelbots.keys()):
		pixelbots[id].sendHome() # non blocking

	# wait till all known bots are homed
	homed=0
	while homed<len(pixelbots.keys()):
		homed=0
		for id in list(pixelbots.keys()):
			if pixelbots[id].isHome():
				homed+=1

	# now turn to face opponents
	
	for id in list(pixelbots.keys()):
		if pixelbots[id].homeX>(setting.VIDEO_WIDTH*.75):
			# face left
			pixelbots[id].turn(180-pixelbots[id].angle)
		else:
			pixelbots[id].turn(pixelbots[id].angle)
			
			
	time.sleep(5)
	
	# let them run their builtin game program
	
	for botId in list(pixelbots.keys()):
		pixelbots[botId].run()
		
def updatePixelbots()->None:
	"""updatePixelbots
	
	updates the current coordinate info of the bots and broadcasts
	the info to the actual pixelbots
	"""
	markers=detector.getPixelbots() # get current pos info
	for botId in list(pixelbots.keys()):
		try:
			cx,cy,angle=markers[botId]
			pixelbots[botId].setPos(cx,cy)
			pixelbots[botId].setAngle(angle)
			pixelbots[botId].tellPixelbot() # upload data to the bot
		except:
			pass
###########################################################
#
# scan for home bases, pixelbots and scale marker
# assign bots to bases then send them home
# when homed, turn to face the opponents and
# start the builtin game scripts
#

def getHomeBases()->int:
	global homeBases
	logger.info("Scanning for home bases") 
	detector.update()
	homeBases=detector.getHomeBases() # dict [markerId]=(cx,cy)
	return len(homeBases.keys())
	
		
def getPixelbots(timeout=60) ->None:
	global pixelbots
	logger.info("Scanning for pixelbots")
	detector.update()
	start=time.time()
	numBots=0
	
	while numBots==0:
		if time.time()-start>timeout:
			msg="Timeout waiting for pixelbots"
			logger.info(msg)
			raise(msg)
			
		foundBots=detector.getPixelbots() # a dict id=>(cx,cy,angle)
		
		numBots=len(foundBots.keys())
	
		if numBots>0:
			for botId in list(foundBots.keys()):
				#the team,homeX and homeY will be set by assignPixelbotsToTeams()
				cx,cy,angle=foundBots[botId]
				logger.info(f"Creating bot {botId} {cx} {cy} {angle}")
				pixelbots[botId]=pixelbotClass.pixelbot(botId,cx,cy,angle)
		else:
			detector.update()

def spotTheBall(timeout=60)->bool:
	global ballPos
	logger.info("Scanning for the ball")
	start=time.time()
	scanning=True
	while scanning:
		if time.time()-start>timeout:
			msg="Timeout scanning for ball"
			logger.info(msg)
			raise(msg)
		detector.update()
		ballX,ballY=detector.getBall()
		if ballX is not None:
			ballPos=(ballX,ballY)
			scanning=False

#########################################
#
# logic
#
# find home bases - if none abort
# find pixelbots - raises timeout
# assign bots to bases (randomly)
# send bots home
# wait till bots are home
# spot the ball - with timeout
# wait?
# tell bots to run
#

########################################

if getHomeBases()==0:
	logger.info("No home bases found")
	raise "no home bases - cannot continue"

getPixelbots(120) # timeout default is 60s

assignPixelbotsToBases()

spotTheBall(120) # timeout default is 60s

running=True

logger.info("Game loop starting press Q to quit")

while running:
	detector.update()
	
	# broadcast current positions
	updatePixelbots() 		
	ballPos=detector.getBall()
	
	# check states
	
	if not settings.STREAMING:
		cv2.imshow("ARENA",detector.getFrame())

		if cv2.waitKey(1) & 0xFF==ord("q"):
			running=False
	
		
cv2.destroyAllWindows()

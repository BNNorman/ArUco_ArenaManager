
# interface to HULLOS-Z

from config import settings
import math
import MiscLib
import logging

DEBUG=False

from MqttManager import MQTT # used to emit coordinates via MQTT

logger=logging.getLogger(__name__)

class pixelbot:
	
	"""things shared by all instances"""
	
	mqtt=MQTT()
	
	def __init__(self,botId,cx,cy,angle,team=0,homeX=0,homeY=0):
		"""properties and methods for each detected pixelbot"""
		logger.info(f"Created pixlbot {botId} at {cx},{cy} angle {angle}")
		self.myId=botId
		self.cx=cx
		self.cy=cy
		self.angle=angle
		self.team=team
		self.homeX=homeX
		self.homeY=homeY
		self.teamColour="red" if team==0 else "blue"


	def _getClbAddress(self):
		try:
			name,addr=settings.allKnownBots[self.myId]
			return addr
		except:
			logger.error(f"Error finding botId in allKnownBots {self.myId} type {type(self.myId)}")
			return None
		
	def _sendToRobot(self,cmd:str)->None:
		""" sendToRobot
	
		
		if DEBUG is True just print what would be sent
		"""
		addr=self._getClbAddress()
		
		if addr is not None:
			topic=settings.MQTT_COMMAND_TOPIC+f"{addr}"
			topic=f"'{topic}'"
			if DEBUG:
				logger.debug(f"Topic {topic} cmd {cmd}")
			else:
				logger.info(f"Publish to topic {topic} cmd {cmd}")
				self.mqtt.publishPayload(topic,f"'***{cmd}'")

	def _sendCmdList(cmdList):
		for cmd in cmdList:
			self._sendToRobot(cmd)
	
	def tellPixelbot(self):
		"""
		sends all positional info to the pixelbot
		"""
		cmdlist=[f"VSbotX={self.cx}", f"VSbotY={self.cy}",f"VSbotAngle={self.angle}"]
		self.sendCmdList(cmdList)
		
	def sendBallPos(self,ballX,ballY):
		cmdList=[f"VSballX={ballX}",f"VSballY={ballY}"]


	def setTeamColour(self,colourName:str)->None:
		self.teamColour=colourName
		# light up the bot
		self.setPixels(colourName)
	
	def setPos(self,cx,cy):
		self.cx=cx
		self.cy=cy
		
	def getPos(self):
		return (self.cx,self.cy)
		
	def setHomePos(self,cx,cy):
		self.homeX,self.homeY=cx,cy
		
	def getHomePos(self):
		return (self.homeX,self.homeY)
		
	def setAngle(self,angle):
		self.angle=angle
		
	def getAngle(self):
		return self.angle

	def props(self) -> tuple:
		"""props()
		used to return all the required properties
		"""
		return (self.cx,self.cy,self.angle,self.team,self.homeX,self.homeY)

	def run(self):
		"""run()
		Tells the bot to start it's pythonish program
		"""
		self._sendToRobot("RR")

	def stop(self):
		"""stop()
		Tells the pixelbot to stop executing its program
		"""
		self._sendToRobot("RH")
		
	def sendHome(self):
		"""sendHome()
		
		NOTE TO SELF
		COULD COMPUTE THE ANGLE, TURN THE BOT AND MOVE IT
		"""
		cmdList=[]
		cmdList.append("RH")
		cmdList.append(f"VShomeX={self.homeX}")
		cmdList.append(f"VShomeY={self.homeY}")
		
		# turn the robot to face homeX,homeY
		destAngle=MiscLib.angle(self.homeX,self.homeY,self.x,self.y)
		turn=destAngle-self.angle
		cmdList.append(f"MR{turn}")
		
		dist=MiscLib.distance(self.homeX,self.homeY,self.x,self.y)
		cmdList.append(f"MF{dist}") # as fast as possible
		
		self.sendCmdList(cmdList)
		
		
	def isHome(self,tolerance=10):
		# now wait for it to get there
		if MiscLib.isHome(self.x,self.y,self.homeX,self.homeY):
			return True
		return False
		
		
	def turn(self,angle:int,inTime:int=None):
		""" turn()

		Sends a command to a pixelbot asking it to turn through an angle

		angle:int	number of degrees to turn anti-clockwise, -ve values are clockwise
		inTime:int	number of seconds in which to turn
		"""
		cmd=f"MR{angle}"
		if inTime:
			cmd=f"MR{angle},{intime}"
			
		self._sendToRobot(cmd)
				
	def move(self,distance:int,inTime:int=None)->None:
		""" move()
		build a command to tell the pixelbot to move

		distance:int 	the distance (mm) to move, -ve values mean backwards
		inTime:int 		the number of seconds for the move, None means as fast as possible
		"""
		cmd=f"MF{distance}"
		if inTime:
			cmd=f"MF{distance},{inTime}"
		
		self._sendToRobot(cmd)
		
	def setPixels(self,colourName:str):
		"""setPixels
		sets the colour of the pixelbot pixels

		colourName:str	like "red","blue" etc or R B etc

		"""
		self._sendToRobot(f"PN{colourName}")

if __name__ == "__main__":
	logging.basicConfig(filename='pixelbotClass.log', filemode="w",level=logging.INFO)
	logger.info('Started')
	
	B=pixelbot(20,10,10,34,0,0,0)
	
	print(B._getClbAddress())
	
	B.setPixels("R")
	
	print("Done")
	
	

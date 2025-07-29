
# interface to HULLOS-Z

from config import settings

from PixelbotControl import Control

Ctrl=Control()

from MqttManager import MQTT # used to emit coordinates via MQTT


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

	def _getClbAddress(self,botId):
		name,addr=settings.pixelBots[botID]
		return addr
		
	def _sendToRobot(self,cmd:str)->None:
		""" sendToRobot
		
		serialises and sends pixelbot commands to an MQTT broker as JSON strings
		
		if DEBUG is True just print what would be sent
		"""
		addr=getClbAddress(botId)
		topic=settings.BASE_COMMAND_TOPIC+"/{addr}"
		if DEBUG:
			print(f"Topic {topic} cmd {cmd}")
		else:
			mqtt.publish(topic,f"***{cmd}")
	
	
	def tellPixelbot(self):
		"""
		sends all positional info to the pixelbot
		"""
		cmd=f"tell {self.cx} {self.cy} {self.angle}"
		self._sendToRobot(self.id,cmd)
		
	def sendBallPos(self,ballX,ballY):
		cmd=f"ball {ballX} {BallY}"
		self._sendToRobot(self.id,cmd)

	def setTeamColour(self,colourName):
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
		return self.homeX,self.homeY)
		
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
		self._sendToRobot(self.id,"run")

	def stop(self):
		"""stop()
		Tells the pixelbot to stop executing its program
		"""
		self._sendToRobot(self.id,"stop")
		
	def sendHome(self):
		"""sendHome()
		
		NOTE TO SELF
		COULD COMPUTE THE ANGLE, TURN THE BOT AND MOVE IT
		"""
		
		cmd=f"home {self.homeX} {self.homeY}"
		self._sendToRobot(self.id,self.homeX,self.homeY)
		
		
	def turn(self,angle:int,inTime:int=None):
		""" turn()

		Sends a command to a pixelbot asking it to turn through an angle

		bitId:int 	is the aruco marker id on the pixelbot
		angle:int	number of degrees to turn anti-clockwise, -ve values are clockwise
		inTime:int	number of seconds in which to turn
		"""
		cmd=f"turn {angle}"
		if inTime:
			cmd=f"turn {angle} {intime}"
			
		self._sendToRobot(self.id,cmd)
				
	def move(self,distance:int,inTime:int=None)->None:
		""" move()
		build a command to tell the pixelbot to move

		botID:int 		is the aruco marker id on the pixelbot
		distance:int 	the distance (mm) to move, -ve values mean backwards
		inTime:int 		the number of seconds for the move, None means as fast as possible
		"""
		cmd=f"move {distance}"
		if inTime:
			cmd=f"move {distance} {inTime}"
		
		self._sendToRobot(self.id,cmd)
		
	def setPixels(self,colourName:str):
		"""setPixels
		sets the colour of the pixelbot pixels

		botId:int 		is the aruco marker id on the pixelbot
		colourName:str	like "red","blue" etc

		"""
		self._sendToRobot(self.id,f"p {colourName}")

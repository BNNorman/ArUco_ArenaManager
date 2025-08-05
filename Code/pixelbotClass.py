
# interface to HULLOS-Z

import paho.mqtt.client as paho

from config import settings
import math
import MiscLib
import logging
import time

DEBUG=False

from mqttSecrets import MQTT_BROKER,MQTT_USER,MQTT_PASS, MQTT_CONNECT_TIMEOUT,MQTT_KEEP_ALIVE,MQTT_COMMAND_TOPIC

logger=logging.getLogger(__name__)

class pixelbot:
	
	"""things shared by all instances"""
	

	
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
		self.mqttc=paho.Client()
		self.mqttc.connected_flag=False
	
		self._connectToBroker()
		
	def __del__(self):
		if self.mqttc.connected_flag:
			self.mqttc.loop_stop()
			
	def _on_connect(self,mqttc, obj, flags, rc):
		if rc==0:
			self.mqttc.connected_flag=True
			logger.info(f"on_connect() callback: ok")
		else:
			logger.info(f"on_connect() callback: error rc={rc}")
			
	
	def _publishPayload(self,topic,payload):
		'''
		meant to be called by user
		:param topic:
		:param payload:
		:return:
		'''

		logger.info(f"publishPayload: topic {topic} payload {payload}")
		
		self.mqttc.publish(topic,payload)
		self.mqttc.loop(timeout=1.0, max_packets=1)
				
		try:
			if not self.mqttc.connected_flag:
				self._connectToBroker()
				
			(res,qos)=self.mqttc.publish(topic,payload,qos=0) # default Qos=1
			logger.info(f"publish returned res {res} qos {qos}")
			
		except Exception as e:
			logger.warn(f"publish failed exception: {e}")       

	def _connectToBroker(self):
		"""
		waits till on_connect callback confirms connection
		"""

		if self.mqttc.connected_flag:
			# don't try again
			logger.info("attempt to connect to mqtt but already connected")
			return

		logger.info("connectToBroker(): Trying to connect to the MQTT broker")

		# on_message calls may be redirected
		self.mqttc.on_connect = self._on_connect


		# use authentication?
		if MQTT_USER is not None:
			logger.info("connectToBroker(): using MQTT authentication")
			self.mqttc.username_pw_set(username=MQTT_USER, password=MQTT_PASS)
		else:
			logger.info("main(): not using MQTT autentication")

		# terminate if the connection takes too long
		# on_connect sets a global flag brokerConnected
		startConnect = time.time()
		self.mqttc.loop_start()	# runs in the background, reconnects if needed
		self.mqttc.connect(MQTT_BROKER,keepalive=MQTT_KEEP_ALIVE)
		self.mqttc.loop_start()
		while not self.mqttc.connected_flag:
			# "connected" callback may take some time
			if (time.time() - startConnect) > MQTT_CONNECT_TIMEOUT:
				logger.error(f"connectToBroker(): broker on_connect time out {MQTT_CONNECT_TIMEOUT}s")
				return False

		logger.info(f"connectToBroker(): Connected to MQTT broker after {time.time()-startConnect} s")
		self.mqttc.publish("lb/command/CLB-E66164084320A62E","connected")
		return True

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
		logger.info(f"sendToRobot({cmd})")
		
		addr=self._getClbAddress()
		
		if addr is not None:
			topic=f"'{MQTT_COMMAND_TOPIC}{addr}'"
			if DEBUG:
				logger.debug(f"Topic {topic} cmd {cmd}")
			else:
				logger.info(f"Publish to topic {topic} cmd {cmd}")
				self._publishPayload(topic,f"'***{cmd}'")
		else:
			logger.warn(f"bot address not found")
			
	def _sendCmdList(self,cmdList):
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
		logger.info(f"Set pixels {colourName}")
		self._sendToRobot(f"PN{colourName}")

if __name__ == "__main__":
	logging.basicConfig(filename='pixelbotClass.log', filemode="w",level=logging.INFO)
	logger.info('Started')
	
	B=pixelbot(20,10,10,34,0,0,0)
	
	if not B.mqttc.connected_flag:
		print("Not connected to MQTT")
	
	print("Addr:",B._getClbAddress())
	
	B.setPixels("R")
	
	B._sendToRobot("PNG")
	
	print("Done")
	
	

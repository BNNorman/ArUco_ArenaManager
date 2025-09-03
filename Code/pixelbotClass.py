
# interface to HULLOS-Z

import paho.mqtt.client as paho

from config import settings
import math
import MiscLib
import time

DEBUG=False
DEFAULT_PROGRAM_LIST=["active.txt"]


from mqttSecrets import MQTT_BROKER,MQTT_USER,MQTT_PASS, MQTT_CONNECT_TIMEOUT,MQTT_KEEP_ALIVE,MQTT_COMMAND_TOPIC, MQTT_DATA_TOPIC



class pixelbot:
	
	"""things shared by all instances"""

	
	def __init__(self,botId,cx:int,cy:int,heading:int,homeX:int=0,homeY:int=0):
		"""properties and methods for each detected pixelbot"""

		self.myId=botId
		try:
			self.myName,self.addr=settings.allKnownBots[self.myId]
		except:
			raise(f"botId {self.myId} not found in settings.allKnownBots")
		
		self.cx=cx
		self.cy=cy
		self.heading=heading
		self.homeX=homeX
		self.homeY=homeY
		
		self.teamColour="red" if homeX<(settings.VIDEO_WIDTH/2) else "blue"
		self.mqttc=paho.Client()
		self.mqttc.connected_flag=False
		self.publishCallbackPending=False
		self.connectedToBroker=False
		self._connectToBroker("__init__") # debugging where call came from

		# set when variables are sent, cleared by bot data 
		# topic on_message callback
		self.busy=False
		
	def __del__(self):
		pass
		if self.mqttc.connected_flag:
			self.mqttc.loop_stop()
			
	def _on_connect(self,client, obj, flags, rc):
		if rc==0:
			client.connected_flag=True
			print(f"subscribing to topic {MQTT_DATA_TOPIC+self.addr}",flush=True)
			client.subscribe(MQTT_DATA_TOPIC+self.addr)

	
	def _on_message(self,client, userdata, message):
		# when the bot has finished doing its thing
		# we are subscribed to the data topic for this
		#print(f"Got message {message.payload} from arena",flush=True)
		if message.payload==b'1':
			#print("Got job done")
			self.busy=False
			
		#print(f"on message for botId {self.myId} topic {message.topic} payload {message.payload}",flush=True)
		
		
	def _on_disconnect(self,client, userdata, rc):
		client.connected_flag=False
	
	def _on_publish(self,client, userdata, mid):
		self.publishPending=False

		
	def _publishPayload(self,topic,payload):
		'''
		use by sendToRobot and sendHome
		
		:param topic:
		:param payload:
		:return:
		'''
		
		if topic is None or payload is None:
			return
	
		self.publishPending=True
				

		if not self.mqttc.connected_flag:
			self._connectToBroker()
		self.mqttc.publish(topic,payload,qos=2)
			
   

	def _connectToBroker(self,info):
		"""
		waits till on_connect callback confirms connection
		"""
		
		if self.connectedToBroker:
			return

		if self.mqttc.connected_flag:
			# don't try again
			return

		# on_message calls may be redirected
		
		self.mqttc.on_message = self._on_message
		self.mqttc.on_connect = self._on_connect
		self.mqttc.on_publish = self._on_publish
		self.mqttc.on_disconnect = self._on_disconnect

		# use authentication?
		if MQTT_USER is not None:
			self.mqttc.username_pw_set(username=MQTT_USER, password=MQTT_PASS)


		# terminate if the connection takes too long
		# on_connect sets a global flag brokerConnected
		startConnect = time.time()
		self.mqttc.loop_start()
		self.mqttc.connect(MQTT_BROKER,keepalive=MQTT_KEEP_ALIVE)
		while not self.mqttc.connected_flag:
			# "connected" callback may take some time
			if (time.time() - startConnect) > MQTT_CONNECT_TIMEOUT:
				print(f"MQTT connect timeout",flush=True)
				return False

        # pending uploader fix
		#self.uploadPrograms(DEFAULT_PROGRAM_LIST)
		return True

	def _sendHullOScmd(self,cmd:str)->None:
		self._sendToRobot("***"+cmd)

	def _sendHullOScmdList(self,cmdList: list)->None:
		for cmd in cmdList:
			self._sendHullOScmd(cmd)
	
	def _sendPythonishCmd(self,cmd):
		self._sendToRobot("**"+cmd)
		
	def _sendPythonishcmdList(self,cmdList: list)->None:
		for cmd in cmdList:
			self._sendPythonishCmd(cmd)		
		
	def _sendToRobot(self,cmd:str)->None:
		""" sendToRobot
	
		if DEBUG is True just print what would be sent
		"""
	
		topic=f"{MQTT_COMMAND_TOPIC}{self.addr}"
		if DEBUG:
			print(f"_sendToRobot: Topic {topic} cmd {cmd}",flush=True)
		else:
			self._publishPayload(topic,f"{cmd}")
			
	def _sendCmdList(self,cmdList):
		for cmd in cmdList:
			self._sendToRobot(cmd)
	
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
		
	def setHeading(self,heading)->None:
		self.heading=heading
		
	def getHeading(self):
		return self.heading

	def props(self) -> tuple:
		"""props()
		used to return all the required properties
		"""
		return (self.cx,self.cy,self.heading,self.team,self.homeX,self.homeY)

	def run(self):
		"""run()
		Tells the bot to start it's pythonish program
		"""
		self._sendHullOScmd("RS")

	def stop(self):
		"""stop()
		Tells the pixelbot to stop executing its program
		"""
		self._sendHullOScmd("RH")

	def loadAndRun(self,filename:str)->None:
		"""
		send a load command
		"""
		cmd=f'load "{filename}"'
		self._sendPythonishCmd(cmd)
			
				
				
	def OFF_uploadPrograms(self,progs=None)->None:
		"""
		upload a group of pythonish programs
		"""
		if progs is None:
			return
			
		for filename in progs:
			with open("programs/"+filename,"r") as f:
				progTxt=f.readlines()
			
			self._uploadPythonishProgram(progTxt,filename)

	def uploadPrograms(self,progs=None)->None:
		"""
		upload a group of pythonish programs
		"""
		if progs is None:
			return
			
		for filename in progs:
			print(f"Uploading {filename}")
			with open(f"programs/{filename}","r") as f:
				progTxt=f.read()
				# each file must have a begin and an end
				self._uploadPythonishProgram(progTxt,filename)


	def _beginUpload(self,filename=None):
		if filename is None:
			# prog becomes current
			self._sendHullOScmd("RM") 
		else:
			self._sendHullOScmd(f'RM{filename}')
	
	def _endUpload(self):
		self._sendHullOScmd("RX")
		
	def _uploadPythonishProgram(self,progTxt,filename=None):
		"""
		upload one program or None
		"""
		
		self.stop() # halt the running program

		self._beginUpload(filename)
			
		self._sendPythonishCmd(progTxt)
		
		self._endUpload()
		
		if filename is None:
			self.run() # immediately run the program ( default active.txt)
		else:
			self.loadAndRun(filename) # run the program
			
	def OFF_uploadPythonishProgram(self,cmdList,filename=None):
		"""
		upload one program or None
		"""
		
		if filename is None:
			print("Filename missing",flush=True)
			return
			
		self.stop() # halt the running program

		self._beginDownload(filename)
			
		self._sendPythonishcmdList(cmdList)
		
		self._endDownload()
		
		if filename is None:
			self.run() # immediately run the program
		else:
			self.loadAndRun(filename) # run the program
			
	def updateVariables(self,variables:dict)->None:
		"""
		the variables must already exist in the running program
		
		only dist(ance) and angle are required. The bot will turn and move as
		as asked.
		
		Arena Manager checks if bot has completed previous moves (not busy)
		
		"""
			
		for var in list(variables.keys()):
			HullOs=f"VS{var}={variables[var]}"
			self._sendHullOScmd(HullOs)

		
	def isHome(self,baseSideLenPX:int)->bool:
		
		tolerance=round(baseSideLenPX/2)
		
		distToHome=round(MiscLib.getHypotenuse(self.cx,self.cy,self.homeX,self.homeY))
	
		if distToHome<=tolerance:
			return True
		return False
		
				
		
	def setPixels(self,colourName:str)->None:
		"""setPixels
		sets the colour of the pixelbot pixels

		colourName:str	like "red","blue" etc or R B etc

		"""
		self._sendHullOScmd(f"PN{colourName}")


		
	
if __name__=="__main__":
	
	# botId,cx:int,cy:int,heading:int,homeX:int=0,homeY:int=0):
	
	# using goldilocks for debugging
	print(f"creating goldilocks",flush=True)
	B=pixelbot(20,0,0,0,100,100)
	
	Vars={"dist":50, "angle":45}
	
	def status(msg):
		if B.busy:
			print(f"{msg} is busy")
		else:
			print(f"{msg} is NOT busy")
			
	
	status("BEFORE")
	B.updateVariables(Vars)
	status("AFTER")
	
	
	
	
	print(f"Press ctrl-c to exit",flush=True)
		
	try:
		while True:
			print(f"loop  busy {B.busy}")
			time.sleep(1)
	except Exception as e:
		print(f"Exception {e}")
	
	

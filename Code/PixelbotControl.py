# PixelbotControl
#
# used to convert simple arg list commands into JSON and send it to
# MQTT server



import math
import json
from MqttManager import MQTT

mqtt=MQTT() # connects to broker


class Control:
	
	def __init__(self):
		pass
		
	def sendToRobot(self,cmd)->None:
		mqtt.publish(json.dumps(cmd)
		
	def move(self,botId,distance,inTime=None)->None:
		cmd={"process":"motors","command":"move"}
		cmd["to"]=botId
		cmd["distance"]=distance
		if inTime is not None:
			cmd["inTime"]=inTime
		self.sendToRobot(cmd)

	def turn(self,botId,angle,inTime=None):
		cmd={"process":"motors","command":"turn"}
		cmd["to"]=botId
		cmd["angle"]=angle
		if inTime is not None:
			cmd["inTime"]=inTime
		self.sendToRobot(cmd)
		
	def stop(self,botId):
		cmd={"process":"motors","command":"stop"}
		cmd["to"]=botId
		self.sendToRobot(cmd)
		

	def setPixels(self,botId,colourName):
		cmd={"process":"pixels","command":"setnamedcolour"}
		cmd["to"]=botId,
		cmd["colourname"]=colourName
		self.sendToRobot(cmd)
		
	def publishPosition(self,botId,cx,cy,heading):
		cmd={"process":"pixels","command":"setPosition"}
		cmd["to"]=botId
		cmd["cx"]=cx
		cmd["cy"]=cy
		cmd["heading"]=heading
		self.sendToRobot(cmd)
		
	def publishTargetPosition(self,botId,cx,cy,heading):
		# pixelbots must head to the X/Y coordinates given
		# collision avoidance is down to the bot
		cmd={"process":"pixels","command":"setPosition"}
		cmd["to"]=botId
		cmd["cx"]=cx
		cmd["cy"]=cy
		cmd["heading"]=heading
		self.sendToRobot(cmd)		

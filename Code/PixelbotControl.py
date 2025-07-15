""" PixelbotControl

used to convert simple arg list pixelbot commands into JSON and send it to MQTT server

"""
DEBUG=True

import json

if not DEBUG:
	from MqttManager import MQTT

	mqtt=MQTT() # connects to broker


class Control:
	""" Control

	An API to send control commands to a pixelbot via MQTT
	"""
	
	def __init__(self):
		pass
		
	def sendToRobot(self,cmd:dict[str,any])->None:
		""" sendToRobot
		
		serialises and sends pixelbot commands to an MQTT broker as JSON strings
		
		if DEBUG is True just print what would be sent
		"""
		if not DEBUG:
			mqtt.publish(json.dumps(cmd))
		else:
			print(f"MQTT Publish {json.dumps(cmd)}")
			
	def move(self,botId:int,distance:int,inTime:int=None)->None:
		""" move
		build a command to tell the pixelbot to move

		botID:int 		is the aruco marker id on the pixelbot
		distance:int 	the distance (mm) to move, -ve values mean backwards
		inTime:int 		the number of seconds for the move, None means as fast as possible
		"""
		cmd={"process":"motors","command":"move"}
		cmd["to"]=botId
		cmd["distance"]=distance
		if inTime is not None:
			cmd["inTime"]=10*inTime # pixelbot uses 0.1s intervals
		self.sendToRobot(cmd)

	def turn(self,botId:int,angle:int,inTime:int=None):
		""" turn

		Sends a command to a pixelbot asking it to turn through an angle

		bitId:int 	is the aruco marker id on the pixelbot
		angle:int	number of degrees to turn anti-clockwise, -ve values are clockwise
		inTime:int	number of seconds in which to turn
		"""
		cmd={"process":"motors","command":"turn"}
		cmd["to"]=botId
		cmd["angle"]=angle
		if inTime is not None:
			cmd["inTime"]=10*inTime
		self.sendToRobot(cmd)
		
	def stop(self,botId:int):
		"""stop
		Tells the pixelbot to stop executing its program

		botId:int 	is the aruco marker id on the pixelbot
		"""
		cmd={"process":"motors","command":"stop"}
		cmd["to"]=botId
		self.sendToRobot(cmd)
		

	def setPixels(self,botId:int,colourName:str):
		"""setPixels
		sets the colour of the pixelbot pixels

		botId:int 		is the aruco marker id on the pixelbot
		colourName:str	like "red","blue" etc

		"""
		cmd={"process":"pixels","command":"setnamedcolour"}
		cmd["to"]=botId,
		cmd["colourname"]=colourName # might need to lowercase this
		self.sendToRobot(cmd)
		
	def publishPosition(self,botId:int,cx:int,cy:int,heading:int):
		""" publishPosition

		Used to send the current position and heading of a pixelbot

		botId:int 		is the aruco marker id on the pixelbot
		cx:int			X centre of the bot in mm
		cy:int			Y centre of the bot in mm
		heading:int		heading in degrees from North
		"""
		cmd={"process":"move","command":"setPosition"}
		cmd["to"]=botId
		cmd["cx"]=cx
		cmd["cy"]=cy
		cmd["heading"]=heading
		self.sendToRobot(cmd)
		
	def publishTargetPosition(self,botId:int,cx:int,cy:int,heading:int):
		""" publishTargetPosition

		Tells the botId where to go next. The pixelbot is expected to
		turn till it is on the required heading then move. The pixelbot program
		should handle collision avoidance

		botId:int		id of the pixelbot that should follow this command
		cx:int			x position to go to
		cy:int			y position to go to
		heading:int		heading for the move

		"""

		cmd={"process":"move","command":"setPosition"}
		cmd["to"]=botId
		cmd["target"]=True # flag to indicate cx & cy are target locations
		cmd["cx"]=cx
		cmd["cy"]=cy
		cmd["heading"]=heading
		self.sendToRobot(cmd)		


if __name__=="__main__":
	ctrl=Control()
	
	ctrl.publishTargetPosition((1,10,20,0))
	

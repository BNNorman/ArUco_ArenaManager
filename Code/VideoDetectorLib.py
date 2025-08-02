# picamera2 only available on a pi
from picamera2 import Picamera2,Preview
import cv2
import threading # for locking
import numpy as np
import time
import traceback
import sys
import imutils
import itertools # for zipping
import MiscLib

from config import settings


MARKER_DICT=cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)

class arucoDetector:
	"""arucoDetector
	
	Initialises the camera , aruco dict and grabs the first frame
	"""
	def __init__(self,width:int=settings.VIDEO_WIDTH,height:int=settings.VIDEO_HEIGHT,)->None:

		# pixel/mm ratio will be updated if marker with settings.CALIBRATION_MARKER is found
		# it is recommended that the marker is always present in case the camera position changes
		self.scale_px_per_mm=settings.INITIAL_SCALE_FACTOR 
		
		self.cam=Picamera2()

		camera_config=self.cam.create_still_configuration(main={"size": (width,height),'format':"RGB888"})
		self.cam.configure(camera_config)
		
		#self.cam.set_controls({"ExposureTime": 0, "AnalogueGain": 0}) # autogain & exposure
		
		self.cam.start()


		
		self.parameters = cv2.aruco.DetectorParameters()

		self.markers={}

		time.sleep(2) # wait for camera to warm up
		self.lock=threading.Lock()
		
		# just to mitigate against start up race conditions
		self.frame=self.cam.capture_array()
		self.gray=self.frame.copy()
		self.threshold=self.frame.copy()
		self.edges=None
		
		self.ballPos=(0,0)		
			
			
	def __del__(self):
		""" terminate the camera feed
		"""
		self.cam.stop()
		

	def _grabFrame(self) ->(any,dict):
		"""grabFrame()
		
		must be called frequently from update() method

		Identifies any aruco markers it can then
		draws the detected markers on the frame
		
		if marker ID = setting.CALIBRATION_MARKER computes the pixel to mm ratio.
		for all other markers computes the centre and angle of rotation.
		
		returns videoFrame:any,markers:dict
		
		"""
		with self.lock:
			self.frame=self.cam.capture_array()

			# convert to grey scale
			self.gray=cv2.cvtColor(self.frame,cv2.COLOR_BGR2GRAY)
			
			# make black & white to enhance aruco detection
			
			# these complain about image format
			#_, self.threshold = cv2.threshold(self.frame, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
			#self.threshold = cv2.adaptiveThreshold(self.frame, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 11, 2)
 
			_, self.threshold = cv2.threshold(self.gray, settings.BW_THRESHOLD, 255, cv2.THRESH_BINARY)

			# scann for any markers and draw them 
			self.markers={}
			corners, ids, _ = cv2.aruco.detectMarkers(self.threshold,MARKER_DICT)
			if ids is not None:
				cv2.aruco.drawDetectedMarkers(self.frame, corners,ids)
				for aruco_id,corners in zip(ids, corners):
					self.markers[aruco_id[0]]=corners
					
		
	def _doCalibration(self):
		"""
		looks for a calibration marker then computes the
		pixel to mm ratio.

		"""

		try:
			corners=self.markers[settings.CALIBRATION_MARKER]

			perimPX = cv2.arcLength(corners, True) 			 # pixels
			self.scale_px_per_mm=perimPX/settings.CALIBRATION_PERIM_MM # pixels per mm
			#print("Scale_px_per_mm",self.scale_px_per_mm)
		except:
			# marker not present
			pass
		
	def _findTheBall(self,radiusTolerance=settings.BALL_TOLERANCE):

		scaledBallRadiusPx=settings.BALL_DIA_MM*self.scale_px_per_mm/2	# scale may change if camera moves
		minRadiusPx,maxRadiusPx=MiscLib.min_max(scaledBallRadiusPx,radiusTolerance)

		#print(f"minRadiusPx {minRadiusPx} maxRadiusPx {maxRadiusPx} scaled {scaledBallRadiusPx} scale {self.scale_px_per_mm}")
		
		self.edges=cv2.Canny(self.gray,30,200)
		
		contours, hierarchy = cv2.findContours(self.edges,cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

		for i,contour in enumerate(contours):
			if i==0:
				continue
			
			#cv2.drawContours(self.frame, [contour], -1, (0, 255, 0), 3) # -1 means filled
			
			# more approx vertices means more likely to be a circle
			# hexagon has 6
			approx=cv2.approxPolyDP(contour,0.01*cv2.arcLength(contour,True),True)
			
			if len(approx)>10: # bigger than a nonogon
				(x,y,w,h)=cv2.boundingRect(contour)
				aspect=w/h

				# the aspect ratio of a circle is 1.0 exactly viewed square on
				if aspect>=0.9 and aspect<=1.1: 
					(x,y),radius = cv2.minEnclosingCircle(contour)
					
					#print("FOUND RADIUS",radius)

					# ball has a certain size - or range thereof
					if radius>minRadiusPx and radius<maxRadiusPx:
						#print("Possible ball candidate ball radius ",radius)
						#cv2.drawContours(self.frame, [contour], -1, (0, 255, 0), 3) # -1 means filled

						self.ballPos=(int(x),int(y))

						cv2.circle(self.frame,self.ballPos,int(radius),(255,0,0),2)

									
				
	def _drawCentreOnFrame(self,cx,cy,dia=5):
		""" drawCentreOnFrame

		Used to add a small circle at the centre of the detected marker.
		"""
		cv2.circle(self.frame,(cx,cy),dia,(255,255,0),-1) # use -1 to fill

	def _getMarkerInfo(self,corners):
		""" _getMarkerInfo

		calc cx,cy and rotation angle
		"""
		if corners is None:
			return False,None,None,None
		
		m=cv2.moments(corners)
		cx=int(m['m10']/m['m00'])	
		cy=int(m['m01']/m['m00'])	
		
		# find the degree of rotation
		rotRect=cv2.minAreaRect(corners)
		angle=rotRect[-1]
		
		return True,cx,cy,angle
	
		
	def update(self):
		"""
		simply calls all the methods required to monitor the arena
		"""
		self._grabFrame()
		self._doCalibration()
		self._findTheBall()
		
	def getHomeBases(self) ->dict:
		""" getHomeBases

		return: dict(baseId:(cx,cy))

		"""
		bases={}
		for home_id in settings.TEAM1_BASES+TEAM0_BASES:
			try:
				corners=self.markers[home_id]
				res,cx,cy,angle=self._getMarkerInfo(corners)

				bases[id]=(cx,cy,angle)
			except:
				pass
		return bases
		
		
	def getPixelbots(self) ->dict:
		"""
		return: dict(botId:(cx,cy,heading))
		cx: position (mm) (int)
		cy: position (mm) (int)
		heading: degrees (int)
		"""
		bots={}
		for bot_id in settings.PIXELBOTS:
			try:
				corners=self.markers[bot_id]
				res,cx,cy,angle=self._getMarkerInfo(corners)
				bots[id]=(cx,cy,angle)
			except:
				pass
				
		return bots
	
		
	def getBall(self)->tuple:
		"""
		returns cx,cy of the ball
		"""
		return self.ballPos()

	def getScale(self):
		"""getScale()
		
		return pixels per mm scale
		Assumes the calibration marker has been found. Otherwise
		the default value is returned.
		"""
		return self.scale_px_per_mm
	
	def getFrame(self):
		""" getFrame()

		returns the last frame including any annotations
		grabFrame() takes longer so not suited to fast frame rates.
		since robots don't move quickly Flask can use the last frame grabbed
		to achieve higher frame rates
		"""
		with self.lock:
			return self.frame
				
if __name__ == "__main__":
	A=arucoDetector()
	
	pixel_to_mm_ratio=None
	
	try:
		
		while True:
			# all these are done by A.update() but I'm doing it here for
			# debugging
			A.update()


			# to access the data
			#homeBases=A.getHomeBases()
			#pixelbots=A.getPixelbots()
			#ball=A.getBall()
			
			print("MAX GRAY",np.max(A.gray),"MIN GRAY",np.min(A.gray))	
					
			#cv2.imshow("THRESHOLD",A.threshold)
			#cv2.imshow("GRAY",A.gray)
			#cv2.imshow("EDGES",A.edges)
			cv2.imshow("FRAME",A.frame)
			cv2.waitKey(1)
		
	except :
		exc_type, exc_val, exc_tb = sys.exc_info()
		traceback.print_exception(exc_type, exc_val, exc_tb)

	
	
	# camera is stopped when A is deleted
	cv2.destroyAllWindows()
	
	
	
	
	
		

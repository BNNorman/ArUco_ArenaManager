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
import math
import os

USE_GRAY=True

# stop most libcamera logging
os.environ["LIBCAMERA_LOG_LEVELS"]="3" # allow ERROR and FATAL only

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

		self.cam.start()
		self.markers={}

		time.sleep(2) # wait for camera to warm up
		self.lock=threading.Lock()
		
		# just to mitigate against start up race conditions
		self.frame=self.cam.capture_array()
		self.gray=self.frame.copy()
		
		self.threshold=self.frame.copy()
		self.edges=None
		self.blurred=None
		self.mask=None
		
		self.ballPos=(0,0)		
			
		#logging.info("VideoDetectorLib started")
		
			
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
			# could use a callback - this blocks till a frame is captured
			self.frame=self.cam.capture_array()

			# convert to grey scale
			self.gray=cv2.cvtColor(self.frame,cv2.COLOR_BGR2GRAY)
			
			# enhance black/white for marker detection
			if not USE_GRAY:
				_, self.threshold = cv2.threshold(self.gray, settings.BW_THRESHOLD, 255, cv2.THRESH_BINARY)

			# scan for any markers and draw them 
			self.markers={}
			if USE_GRAY:
				corners, ids, _ = cv2.aruco.detectMarkers(self.gray,MARKER_DICT) 
			else:
				corners, ids, _ = cv2.aruco.detectMarkers(self.threshold,MARKER_DICT)
				
			if ids is not None:
				cv2.aruco.drawDetectedMarkers(self.frame, corners,ids)
				for aruco_id,corners in zip(ids, corners):
					self.markers[aruco_id[0]]=corners
					
	def _doCalibration(self):
		"""
		looks for a calibration marker then computes the
		pixel to mm ratio.
		
		The marker may be obscured so only do this if the
		marker is detected.
		
		This is done repeatedly in case the camera position changes

		"""
		
		if settings.CALIBRATION_MARKER in list(self.markers):
			corners=self.markers[settings.CALIBRATION_MARKER][0]
			x1,y1=corners[0] # top left
			x2,y2=corners[1] # top right

			sideLen=MiscLib.getHypotenuse(x1,y1,x2,y2)

			newScale=round(sideLen/settings.CALIBRATION_SIZE_MM,1) # pixels per mm
			# reduce log repetition
			if self.scale_px_per_mm!=newScale:
				self.scale_px_per_mm=newScale

	
	def _checkBall(self,contours,scaledBallRadiusPx,minRadiusPx,maxRadiusPx):
		for i,contour in enumerate(contours):
			if i==0:
				continue
			
			# more approx vertices means more likely to be a circle
			# hexagon has 6
			approx=cv2.approxPolyDP(contour,0.01*cv2.arcLength(contour,True),True)
			
			if len(approx)>10: # bigger than a nonogon
				(x,y,w,h)=cv2.boundingRect(contour)
				aspect=w/h

				# the aspect ratio of a circle is 1.0 exactly viewed square on
				if aspect>=0.9 and aspect<=1.1: 
					(x,y),radius = cv2.minEnclosingCircle(contour)
					

					# ball has a certain size - or range thereof
					if radius>minRadiusPx and radius<maxRadiusPx:
						logging.info(f"minRadiusPx {minRadiusPx} maxRadiusPx {maxRadiusPx} scaled {scaledBallRadiusPx} scale {self.scale_px_per_mm} FOUND RADIUS {radius}")

						logging.info(f"Possible ball candidate ball radius {radius}")
						#cv2.drawContours(self.frame, [contour], -1, (0, 255, 0), 3) # -1 means filled

						self.ballPos=(int(x),int(y))

						cv2.circle(self.frame,self.ballPos,int(radius),(0,255,0),2)


	def _findTheBall(self,radiusTolerance=settings.BALL_TOLERANCE):
		"""
		using HoughCircles
		"""
		global ballPos
		
		blurred=cv2.medianBlur(self.gray,5)
		scaledBallRadiusPx=settings.BALL_DIA_MM*self.scale_px_per_mm/2	# scale may change if camera moves
		minRadiusPx,maxRadiusPx=MiscLib.min_max(scaledBallRadiusPx,radiusTolerance)
		
		rows=blurred.shape[0]
		circles = cv2.HoughCircles(blurred, cv2.HOUGH_GRADIENT, 1, rows / 8,param1=100, param2=30,minRadius=int(minRadiusPx), maxRadius=int(maxRadiusPx))
			

		if circles is not None:
			circles = np.uint16(np.around(circles))
			for i in circles[0, :]:
				ballPos = (i[0], i[1])
				# circle center
				cv2.circle(self.frame, ballPos, 1, (0, 100, 100), 3)
				# circle outline
				radius = i[2]
				#print(f"radius {radius} min {minRadiusPx} max {maxRadiusPx}")
				cv2.circle(self.frame, ballPos, radius, (255, 0, 255), 3)
				
				
	def _drawCentreOnFrame(self,cx,cy,dia=5):
		""" drawCentreOnFrame

		Used to add a small circle at the centre of the detected marker.
		"""
		cv2.circle(self.frame,(cx,cy),dia,(255,255,0),-1) # use -1 to fill

	def getBotInfo(self,botId):
		"""
		caller facing access
		"""
		try:
			# cx,cy.heading
			r,cx,cy,hdg=self._getMarkerInfo(botId)
			if r:
				return cx,cy,hdg
			else:
				print(f"Unable to get info for botId {botId}",flush=True)
				return None,None,None
		except:
			return None,None,None
		
	def _getMarkerInfo(self,markerId):
		""" _getMarkerInfo

		calc cx,cy and heading
		
		return res,cx,cy,heading
		"""
		
		try:
			corners=self.markers[markerId]
		
			if corners is None:
				return False,None,None,None
		except:
			return False,None,None,None
				
		try:
			m=cv2.moments(corners)
			cx=int(m['m10']/m['m00'])	
			cy=int(m['m01']/m['m00'])	
			
			TLX,TLY=corners[0][0] # use top left corner
			
			#print(f"getMarkerInfo {markerId} CX {cx} CY {cy} TLX {TLX} TLY {TLY} ")

			heading,_=MiscLib.getHeadingAndRange(cx,cy,TLX,TLY) # I dont use returned radius
			
			# all integer values already
			return True,cx,cy,heading
			
		except Exception as e:
			print(f"getMarkerInfo EXCEPTION {e}")
			
		
	def update(self):
		"""
		simply calls all the methods required to monitor the arena
		"""
		self._grabFrame()
		self._doCalibration()
		self._findTheBall()
		
	def getHomeBases(self)->dict:
		""" getTeamBases

		return: dict(baseId:(cx,cy))

		"""
		bases={}
		
		
		for home_id in settings.TEAM0_BASES + settings.TEAM1_BASES:
			try:
				# we don't need heading
				res,cx,cy,_=self._getMarkerInfo(home_id)
				if res:
					bases[home_id]=(cx,cy)
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
		for botId in settings.TEAM0_BOTS + settings.TEAM1_BOTS:
			try:
				res,cx,cy,heading=self._getMarkerInfo(botId)
				if res:
					bots[botId]=(cx,cy,heading)					
			except:
				# bot not found
				pass
				
		return bots
	
		
	def getBall(self)->tuple:
		"""
		returns cx,cy of the ball
		"""
		return self.ballPos

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
	
		
	print("Starting video detector",flush=True)
	
	A=arucoDetector()
	
	pixel_to_mm_ratio=None
	
	try:
		
		while True:
			# all these are done by A.update() but I'm doing it here for
			# debugging

			A.update()

			# to access the data
			homeBases=A.getHomeBases()
			pixelbots=A.getPixelbots()
			
			try:		
				cx,cy=homeBases[43]
				#print(f"{43} cx {cx} cy {cy} scale {A.getScale()}",flush=True)
			except Exception as e:
				print(f"Exception {e} keys={list(homeBases.keys())}",flush=True)
			
			try:		
				cx,cy,heading=pixelbots[20]
				#print(f"bot 20 cx {cx} cy {cy} heading {heading}",flush=True)
			except:
				print("bot not found ")
				
			#ball=A.getBall()
			
					
			#cv2.imshow("BLURRED",A.blurred)
			#cv2.imshow("THRESHOLD",A.threshold)
			#cv2.imshow("GRAY",A.gray)
			#cv2.imshow("EDGES",A.edges)
			#cv2.imshow("MASK",A.mask)
			cv2.imshow("FRAME",A.frame)
			cv2.waitKey(1)
		
	except Exception as e:
		print("__main__ EXCEPTION {e}")
		exc_type, exc_val, exc_tb = sys.exc_info()
		traceback.print_exception(exc_type, exc_val, exc_tb)

	
	
	# camera is stopped when A is deleted
	cv2.destroyAllWindows()


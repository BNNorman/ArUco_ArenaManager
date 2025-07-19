# picamera2 only available on a pi
from picamera2 import Picamera2,Preview
import cv2
import threading
import numpy as np
import time
import traceback
import sys

from config import settings

class arucoDetector:
	"""arucoDetector
	
	Initialises the camera , aruco dict and grabs the first frame
	"""
	def __init__(self,width:int=settings.VIDEO_WIDTH,height:int=settings.VIDEO_HEIGHT,calibrationId:int=settings.CALIBRATION_MARKER,calibrationSize:int=settings.CALIBRATION_SIZE)->None:

		self.calibrationId=calibrationId
		self.calibrationSize=calibrationSize
		
		self.scale:float=0 # pixel/mm ratio will be updated if calibrationId is found
		
		self.cam=Picamera2()

		camera_config=self.cam.create_still_configuration(main={"size": (width,height),'format':"RGB888"})
		self.cam.configure(camera_config)
		self.cam.start()

		self.aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_6X6_250)
		self.parameters = cv2.aruco.DetectorParameters()

		self.corners={} # raw corners
		self.markers={} # cx,cy,angle

		time.sleep(2) # wait for camera to warm up
		self.lock=threading.Lock()
		self.frame=self.cam.capture_array()
		
	def __del__(self):
		""" terminate the camera feed
		"""
		self.cam.stop()

	def grabFrame(self) ->(any,dict):
		"""grabFrame()
		

		must be called frequently

		Identifies any aruco markers it can then
		draws the detected markers on the frame
		
		if marker ID = self.calibrationId computes the pixel to mm ratio.
		for all other markers computes the centre and angle of rotation.
		
		returns videoFrame:any,markers:dict
		
		"""
		with self.lock:
			self.frame=self.cam.capture_array()

			# convert to grey scale
			gray=cv2.cvtColor(self.frame,cv2.COLOR_BGR2GRAY)
			# make black & white to enhance detection
			_, threshold = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)

			#cv2.imshow("thresh",threshold)

			# Detect the markers
			corners, ids, _ = cv2.aruco.detectMarkers(threshold,self.aruco_dict)

			if ids is not None:
				# adds an outline and red corner
				# remove on release
				cv2.aruco.drawDetectedMarkers(self.frame, corners,ids)

				# if we plan to keep last known position then
				# dont wipe this dict.
				# this might help if detection is flaky
				self.markers={}

				# marry up the ids and corners
				for id, corners in zip(ids, corners):
					id=int(id)
					if id==self.calibrationId:
						# just calc scale
						self.scale=self._getScale(corners)
					else:
						res,cx,cy,angle=self._getMarkerInfo(corners)
						if res:
							self._drawCentreOnFrame(cx,cy)
							#print(f"ID type {type(id)}")
							#print(f"id {id} cx {cx} cy {cy} angle {angle}")
							self.markers[id]=(cx,cy,angle)

			return self.frame,self.markers
	
		
	def _getScale(self,corners)->float:
		"""_getScale()

		called if a marker of the designated calibrationId is found
		
		corners:tuple corners to use
		return:->float  the pixel to mm ratio
		"""
		perimeter = cv2.arcLength(corners, True)
		return perimeter/(4*self.calibrationSize)

	def getScale(self):
		"""getScale()
		
		return pixels per mm scale
		"""
		return self.scale
		
	def _drawCentreOnFrame(self,cx,cy,dia=5):
		""" drawCentreOnFrame

		Used to add a small circle at the centre of the marker.
		"""
		cv2.circle(self.frame,(cx,cy),dia,(255,255,0),-1) # use -1 to fill
		
	def getFrame(self):
		""" getFrame()

		returns the last frame including any annotations
		grabFrame() takes longer so not suited to fast frame rates.
		since robots don't move quickly Flask can use the last frame grabbed
		to achieve higher frame rates
		"""
		with self.lock:
			return self.frame
	
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
		
	def getMarkers(self) ->dict:
		""" getMarkers

		return: dict[botId,(cx,cy,angle)]
		
		Faster than getFrame(), intended to be used when markers don't change quickly
		"""
		with self.lock:
			return self.markers
		
if __name__ == "__main__":
	A=arucoDetector(calibrationId=settings.CALIBRATION_MARKER,calibrationSize=settings.CALIBRATION_SIZE)
	
	pixel_to_mm_ratio=None
	
	try:
		while True:
			frame,markers=A.grabFrame()

			cv2.imshow("frame",frame)
							
			if pixel_to_mm_ratio is None:
				pixel_to_mm_ratio=A.getScale()
				#print(F"scale {pixel_to_mm_ratio}")
			
			for id in markers:
				print(F"id {id} cx,cy,angle={markers[id]}")
			

			cv2.waitKey(1)
		
	except :
		exc_type, exc_val, exc_tb = sys.exc_info()
		traceback.print_exception(exc_type, exc_val, exc_tb)

	
	
	# camera is stopped when A is deleted
	cv2.destroyAllWindows()
	
	
	
	
	
		

from picamera2 import Picamera2,Preview
import cv2
import numpy as np
import time
import traceback
import sys
from settings import VIDEO_WIDTH,VIDEO_HEIGHT,CALIBRATION_MARKER,CALIBRATION_SIZE

class ARuCo:
	
	def __init__(self,width=VIDEO_WIDTH,height=VIDEO_HEIGHT,calibrationId=CALIBRATION_MARKER,calibrationSize=CALIBRATION_SIZE):

		self.calibrationId=calibrationId
		self.calibrationSize=calibrationSize
		
		self.scale=None # will be updated if calibrationId is found
		
		self.cam=Picamera2()

		camera_config=self.cam.create_still_configuration(main={"size": (width,height),'format':"RGB888"})
		self.cam.configure(camera_config)
		self.cam.start()

		self.aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_6X6_250)
		self.parameters = cv2.aruco.DetectorParameters()

		self.corners={} # raw corners
		self.markers={} # cx,cy,angle

		time.sleep(2) # wait for camera to warm up
		self.frame=self.cam.capture_array()
		
	def __del__(self):
		self.cam.stop()

	def grabFrame(self):
		"""
		grabFrame just grabs a frame from the camera
		must be called from caller's loop
		
		draws the detected markers on the frame
		
		if marker ID = self.calibrationId computes the pixel to mm ratio
		for all other markers computes the centre and angle of rotation
		
		"""
		self.frame=self.cam.capture_array()

		
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
			# dont wipe these dicts
			self.markers={}
			
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
			
		return self.frame
	
		
	def _getScale(self,corners):
		# called if a marker of the designated calibrationId is found
		# return  the pixel to mm ratio
		perimeter = cv2.arcLength(corners, True)
		return perimeter/(4*self.calibrationSize)

	def getScale(self):
		"""
		scale is pixels per mm
		"""
		return self.scale
		
	def _drawCentreOnFrame(self,cx,cy,dia=5):
		cv2.circle(self.frame,(cx,cy),dia,(255,255,0),-1) # use -1 to fill
		
	def getFrame(self):
		"""
		may be required by Flask to stream the arena
		
		use a memory view to prevent copying the frame
		"""
		return self.Frame
	
	def _getMarkerInfo(self,corners):
		"""
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
		
	def getMarkers(self):
		"""
		returns a dict whose key is marker ID and values ae cx,cy,rotation angle
		"""
		return self.markers
		
if __name__ == "__main__":
	A=ARuCo(calibrationId=200,calibrationSize=52) # Id and mm side of square
	
	pixel_to_mm_ratio=None
	
	try:
		while True:
			frame=A.grabFrame()
			#if frame:
				
			cv2.imshow("frame",frame)
				
			markers=A.getMarkers()
			
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
	
	
	
	
	
		

# MiscLib.py
#
# miscellaneous methods
import logging
import math

def min_max(val:any,tolerance:float=.1)->tuple:
	"""
	min_max return the min and max of a value +- tolerance
	"""
	return (val-val*tolerance,val+val*tolerance)
	
def getHypotenuse(x0:int,y0:int,x1:int,y1:int)->int:
	"""
	calculate the distance between two points using pythagoras
	
	for a bot this is the radius of a circle centred on x0/y0 with x1,y1 on its circumference
	
	for a course this is the length of the course (distance to travel)
	
	measurements are in screen pixels which will be converted to mm by the arena manager
	
	"""
	xdiff=abs(x1-x0)
	ydiff=abs(y1-y0)
	return abs(math.sqrt(xdiff**2+ydiff**2))

	
def getHeadingAndRange(cx:int,cy:int,X0:int,Y0:int)->tuple:
	"""
	for a bot cx,cy are the centre and X0,Y0 are the top left corner.
	
	for a course cx,cy are the start coords (centred of bot) and X0,Y0 are the
	destination co-ordinates
	
	heading are always measure clockwise from North (0)
	
	"""
	radius=getHypotenuse(cx,cy,X0,Y0)

	try:
		ratio=abs(X0-cx)/radius # Sine=O/H

		radians=math.asin(ratio)
		
		# this is angle to the vertical
		angle= math.degrees(radians)
		
		# quadrants
		# 0 1
		# 2 3
		if X0>=cx and Y0>=cy:
			Q=3
			heading=180-angle
		elif X0>=cx and Y0<=cy:
			Q=1
			heading=angle
		elif X0<=cx and Y0>=cy:
			Q=2
			heading=180+angle
		else:
			Q=0
			heading=360-angle
		
		#print(f"getHeading quadrant {Q} heading {heading} angle : {angle}",flush=True)
		return round(heading),round(radius)
		
	except ValueError:
		print(f"getHeading ValueError EXCEPTION cx {cx} cy {cy} X0 {X0} Y0 {Y0} ratio {ratio} radius {radius}",flush=True)


	
def getCourseChange(course:int,heading:int)->int:
	"""
	returns the turn angle from heading to course
	"""
	turn=course-heading # valid upto 180 degrees
	if turn>180:
		turn=-(360-course+heading)
	return turn
	
	
def expandRect(TLX,TLY,BRX,BRY,Margin):
	"""
	expand the rect by Margin
	"""
	
	if TLX<BRX:
		TLX-=Margin
		TLY-=Margin
		BRX+=Margin
		BRY+=Margin
	else:
		TLX+=Margin
		TLY+=Margin
		BRX-=Margin
		BRY-=Margin
	
	return TLX,TLY,BRX,BRY
	
	
	

# MiscLib.py
#
# miscellaneous methods
import math

def distance(self,x1,y1,x2,y2)->int:
	# distance between two points
	# calc hypotenuse
	ydiff=abs(y1-y2)
	xdiff=abs(x1-x2)
	
	return int(math.sqrt(xdiff*xdiff+ydiff*ydiff))
		
def angle(self,x1,y1,x2,y2) -> int:
	# returns the heading between two points
	# might need adjusting so that North is zero
		
	# using Tan=o/a
	ang=math.degrees(math.tan((y2-y1)/(x2-x1)))
		
	return int(ang)
		
def heading(self,angle):
	# angles normally have zero on the east compass point
	# but headings use North
	return abs(angle-90)
		
def isHome(botX,botY,baseX,baseY, tolerance=5):
	# determine if bot pos is within the base
	baseTLX=baseX-tolerance
	baseTLY=baseY-tolerance
	baseBRX=baseX+tolerance
	baseBRY=baseY+tolerance
	
	if baseTLX<=botX<=baseBRX and baseTLY<=botY<=baseBRY:
		return True
	return False
	
	
	
	
	
	
	
	

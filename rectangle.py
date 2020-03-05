import itertools


class Rectangle:

	def __init__(self, x1, y1, x2, y2):
		if x1>x2 or y1>y2:
			raise ValueError("Coordinates are invalid")
		self.x1, self.y1, self.x2, self.y2 = x1, y1, x2, y2
        
	def Contains(self, x, y):
		if x>=self.x1 and x<=self.x2 and y>=self.y1 and y<=self.y2:
			return True
		
		return False

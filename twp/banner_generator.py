# -*- coding: utf-8 -*-
#########################################################################################
##    TWP v0.1.0 - Teeworlds Web Panel
##    Copyright (C) 2015  Alexandre Díaz
##
##    This program is free software: you can redistribute it and/or modify
##    it under the terms of the GNU Affero General Public License as
##    published by the Free Software Foundation, either version 3 of the
##    License.
##
##    This program is distributed in the hope that it will be useful,
##    but WITHOUT ANY WARRANTY; without even the implied warranty of
##    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
##    GNU Affero General Public License for more details.
##
##    You should have received a copy of the GNU Affero General Public License
##    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#########################################################################################
from __future__ import (
    division
)
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
from io import BytesIO


class BannerGenerator(object):
	# Gradient code by Jens Breit: https://djangosnippets.org/snippets/787/
	def channel(self, i, c, size, startFill, stopFill):
	    """calculate the value of a single color channel for a single pixel"""
	    return startFill[c] + int((i * 1.0 / size) * (stopFill[c] - startFill[c]))
	
	def color(self, i, size, startFill, stopFill):
	    """calculate the RGB value of a single pixel"""
	    return tuple([self.channel(i, c, size, startFill, stopFill) for c in range(3)])
	
	def gradient(self, size, startFill, stopFill, runTopBottom = False):
	    """Draw a rounded rectangle"""
	    width, height = size
	    rectangle = self.image
	
	    if runTopBottom:
	      si = height
	    else:
	      si = width
	
	    gradient = [ self.color(i, si, startFill, stopFill) for i in xrange(si) ]
	
	    if runTopBottom:
	        modGrad = []
	        for i in xrange(height):
	           modGrad += [gradient[i]] * width
	        self.image.putdata(modGrad)
	    else:
	        self.image.putdata(gradient*height)
	
	
	def __init__(self, size, title):
		self.size = size
		self.title = title
		self.fontTitle = ImageFont.load("pilfonts/timR12.pil")
		self.fontText = ImageFont.load("pilfonts/timR08.pil")
		self.textColor = (34, 33, 60, 255)
		self.gradStartColor = (214, 213, 213)
		self.gradStopColor = (166, 165, 165)
		self.image = None
		
	def generate(self, format="png"):
		# Create RGBA Image
		memory_img = BytesIO()
		self.image = Image.new('RGBA', self.size, (0, 0, 0, 0))
		draw = ImageDraw.Draw(self.image)
		
		# Border
		self.gradient(self.image.size, self.gradStartColor, self.gradStopColor, True)
		draw.rectangle((1, 1, self.image.size[0], self.image.size[1]), outline=(255, 255, 255))
		draw.rectangle((0, 0, self.image.size[0]-1, self.image.size[1]-1), outline=(120, 120, 120))
		#wh = self.font.getsize("G E E X L A B")
		# Title
		draw.text((11, 4), self.title, fill=(0, 0, 0, 128), font=self.fontTitle)
		draw.text((10, 3), self.title, fill=self.textColor, font=self.fontTitle)
		# Detail
		draw.text((15, 25), "Players: 0/9 - Map: dm1 - Game Type: DM - Public: Yes - Visible: No", 
				fill=(0, 0, 0), font=self.fontText)
		
		# Save Image
		del draw
		self.image.save(memory_img, format=format)
		memory_img.seek(0)
		return memory_img
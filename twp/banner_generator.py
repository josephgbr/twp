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


class BannerGenerator(object):
	READ = 1
	WRITE = 2
	EXCEPTION = 4
	
	def __init__(self, width, height, title):
		self.width = width
		self.height = height
		self.title = title
		self.font = ImageFont.load("pilfonts/timR24.pil")
		
	def save(self):
		im = Image.new('RGBA', (800, 150), (0, 0, 0, 255)) # Create a blank image
		draw = ImageDraw.Draw(im)
		draw.line((0, 0) + im.size, fill=(255, 255, 255))
		draw.line((0, im.size[1], im.size[0], 0), fill=(255, 255, 255))
		wh = self.font.getsize("G E E X L A B")
		draw.text((im.size[0]/2 - wh[0]/2, im.size[1]/2 + 20), "G E E X L A B",
				fill=(255, 255, 0), font=self.font)
		draw.text((im.size[0]/2 - wh[0]/2, im.size[1]/2 - 60), "G E E X L A B",       
				fill=(255, 255, 0), font=self.font)
		del draw  
		im.save('/tmp/twp_banner.png')
		return True
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
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from flask.ext.babel import _


class BannerGenerator(object):
	# Gradient code by Jens Breit: https://djangosnippets.org/snippets/787/
	def _channel(self, i, c, size, startFill, stopFill):
	    """calculate the value of a single color channel for a single pixel"""
	    return startFill[c] + int((i * 1.0 / size) * (stopFill[c] - startFill[c]))
	
	def _color(self, i, size, startFill, stopFill):
	    """calculate the RGB value of a single pixel"""
	    return tuple([self._channel(i, c, size, startFill, stopFill) for c in range(3)])
	
	def _gradient(self, startFill, stopFill, runTopBottom = False):
	    """Draw a rounded rectangle"""
	    width, height = self._image.size
	    si = height if runTopBottom else width
	
	    gradient = [ self._color(i, si, startFill, stopFill) for i in xrange(si) ]
	
	    if runTopBottom:
	        modGrad = []
	        for i in xrange(height):
	           modGrad += [gradient[i]] * width
	        self._image.putdata(modGrad)
	    else:
	        self._image.putdata(gradient*height)
	##
	
	def __init__(self, size, server, netinfo):
		self.size = size
		self.titleColor = (34, 33, 60)
		self.detailColor = (0, 0, 0)
		self.addressColor = (1, 65, 103)
		self.gradStartColor = (214, 213, 213)
		self.gradEndColor = (166, 165, 165)
		
		self._server = server
		self._netinfo = netinfo
		self._fontLarge = ImageFont.load("pilfonts/timR12.pil")
		self._fontLargeBold = ImageFont.load("pilfonts/timB12.pil")
		self._fontSmall = ImageFont.load("pilfonts/timR08.pil")
		self._image = None
		
	def generate(self, ip, format="png"):
		is_online = True if self._netinfo.gametype else False
		
		# Create RGBA Image
		self._image = Image.new('RGBA', self.size, (0, 0, 0, 0))
		draw = ImageDraw.Draw(self._image)
		
		# Border
		self._gradient(self.gradStartColor, self.gradEndColor, True)
		draw.rectangle((1, 1, self._image.size[0], self._image.size[1]), outline=(255, 255, 255))
		draw.rectangle((0, 0, self._image.size[0]-1, self._image.size[1]-1), outline=(120, 120, 120))
		#wh = self.font.getsize("text")
		# Title
		name = self._netinfo.name if is_online else self._server['name']
		draw.text((11, 4), name, fill=(0, 0, 0, 128), font=self._fontLarge)
		draw.text((10, 3), name, fill=self.titleColor, font=self._fontLarge)
		# Detail
		if is_online:
			gametype = self._netinfo.gametype if self._netinfo.gametype else self._server['gametype']
			map = self._netinfo.map if is_online else ". . ."
			players = '%d/%d' % (self._netinfo.players,self._netinfo.max_players) if is_online else ". . ."
			is_visible = _('Yes') if self._server['register'] else _('No')
			is_public = _('No') if self._server['password'] else _('Yes')
			draw.text((15, 25), "%s: %s - %s: %s - %s: %s - %s: %s - %s: %s" 
								% (_('Players'), players,
                                   _('Map'), map, 
                                   _('Game Type'), gametype.upper(), 
                                   _('Public'), is_public, 
                                   _('Visible'), is_visible), 
					fill=(0, 0, 0), font=self._fontSmall)
		else:
			draw.text((15, 25), _('SERVER OFFLINE'), fill=(240, 10, 5), font=self._fontSmall)			
		# Address
		addr = '%s:%s' % (ip, self._server['port'])
		wh = self._fontLargeBold.getsize(addr)
		draw.text((self._image.size[0]-wh[0]-10, self._image.size[1]/2-wh[1]/2), addr, 
				fill=self.addressColor, font=self._fontLargeBold)
		
		del draw
		
		# Save Image To Memory
		memory_img = BytesIO()
		self._image.save(memory_img, format=format)
		memory_img.seek(0)
		return memory_img
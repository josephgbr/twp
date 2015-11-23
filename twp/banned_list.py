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

class BannedList(object):
	def __init__(self):
		self.banlist = []
	
	def add(self, address, time):
		if address in addresslist:
			raise Exception('Address already banned')
		self.banlist.append(BanLine(address, time))
	
	def find(self, address=None):
		output = BannedList()
		if address: address = re.compile(address, re.IGNORECASE)
		for line in self.banlist:
			if address == None or address.search(line.address):
				output.add(line)
		return output
	
	def refresh(self):
		for line in self.banlist:
			if line.end >= time.time():
				self.banlist.remove(line)
	
	def sort(self, cmp=None, key=None, reverse=False):
		self.banlist = sorted(self.banlist, cmp, key, reverse)
	
	def reverse(self):
		self.banlist.reverse()
	
	def clear(self):
		del self.banlist[:]
	
	def __iter__(self):
		return iter(self.banlist)
	
	def __repr__(self):
		return str(self.banlist)


class BanLine(object):
	def __init__(self, address, time):
		self.address = address
		sefl.end = time.time() + time
	
	def __repr__(self):
		return "<Ban ip='{0}' end='{1}'>".format(self.address,self.end)
	
	def __contains__(self, item):
		return True if self.address is item else False
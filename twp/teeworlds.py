#!/usr/bin/python

#  A library to get the serverlist & information for Teeworlds servers
#  Copyright (C) 2011  m!nus <m1nus@online.de>
#
#  This software is provided 'as-is', without any express or implied
#  warranty.  In no event will the authors be held liable for any damages
#  arising from the use of this software.
#  
#  Permission is granted to anyone to use this software for any purpose,
#  including commercial applications, and to alter it and redistribute it
#  freely, subject to the following restrictions:
#  
#  1. The origin of this software must not be misrepresented; you must not
#     claim that you wrote the original software. If you use this software
#     in a product, an acknowledgment in the product documentation would be
#     appreciated but is not required.
#  2. Altered source versions must be plainly marked as such, and must not be
#     misrepresented as being the original software.
#  3. This notice may not be removed or altered from any source distribution.


from __future__ import print_function
import sys
import socket
import time
from random import randint
from struct import unpack
import select
import Queue as queue
import re

# UTF-8 is required as default encoding
reload(sys)
sys.setdefaultencoding('utf8')


def log(level, str):
	if level is 'debug': return
	print("[{0: <5}] {1}".format(level, str), file=sys.stderr)


def is_ipv6(address):
	if isinstance(address, tuple): address = address[0]
	return True if ':' in address else False


class MultiSocket(object):
	READ = 1
	WRITE = 2
	EXCEPTION = 4
	
	def __init__(self, timeout=None, interval=0):
		self.sockets = {}
		self.queue_out = queue.Queue()
		self.timeout = timeout
		self.interval = interval
		self.sockets[socket.AF_INET] = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.SOL_UDP)
		self.has_ipv6 = socket.has_ipv6
		if self.has_ipv6:
			self.sockets[socket.AF_INET6] = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM, socket.SOL_UDP)
	
	def select(self, type=None, timeout=None):
		timeout = self.timeout if timeout == None else timeout
		list_r = self.sockets.values() if (type&self.READ or type==None) else []
		list_w = self.sockets.values() if type&self.WRITE else []
		list_x = self.sockets.values() if type&self.EXCEPTION else []
		ret = select.select(list_r, list_w, list_x, timeout)
		if ret == ([], [], []):
			raise socket.timeout('select timed out')
		else:
			return ret
	
	def sendto(self, data, address):
		if is_ipv6(address):
			if not self.has_ipv6: return 0
			return self.sockets[socket.AF_INET6].sendto(data, address)
		else:
			return self.sockets[socket.AF_INET].sendto(data, address)
	
	def sendto_q(self, data, address, callback=None):
		self.queue_out.put((data, address, callback))
	
	def recvfrom(self, len):
		try:
			s = self.sockets.values()
			(r, w, x) = select.select(s, [], [], self.timeout)
			if not r and not w and not x:
				raise socket.timeout('select timed out')
			for sock in r:
				return sock.recvfrom(len)
		except socket.error as e:
			# Errno 10054 happens when we get ICMP port unreachable, we don't care about that
			if e.errno != 10054:
				raise
		# in case if error 10054 just retry
		# TODO: might reach maximum recursion
		return self.recvfrom(len)
	
	def process_queue(self, amount):
		for _ in range(amount):
			if not self.queue_out.empty():
				(data, address, callback) = self.queue_out.get()
				if self.sendto(data, address) == len(data):
					if hasattr(callback, '__call__'): callback(time.time())
				else:
					log('warning', 'failed to send whole packet, requeuing')
					self.queue_out.put((data, address, callback))


class Handler(object):
	def match(self, **kwargs):
		for name, value in kwargs.iteritems():
			if hasattr(self, name) and getattr(self, name) != value:
				return False
		return True
	
	def call(self, address, data):
		pass


class HandlerStorage(object):
	def __init__(self):
		self.handlers = []
	
	def add(self, handler):
		if isinstance(handler, list):
			self.handlers += handler
		else:
			self.handlers.append(handler)
	
	def remove(self, handler):
		if isinstance(handler, list):
			for item in handler:
				self.handlers.remove(item)
		else:
			self.handlers.remove(handler)
	
	def find(self, **kwargs):
		return [handler for handler in self.handlers if handler.match(**kwargs)]
	
	def clear(self):
		del self.handlers[:]
	
	def __repr__(self):
		return str(self.handlers)


class MasterServer(Handler):
	_packet_count_request = 10*b'\xff' + b'cou2'
	_packet_count_response = 10*b'\xff' + b'siz2'
	_packet_list_request = 10*b'\xff' + b'req2'
	_packet_list_response = 10*b'\xff' + b'lis2'
	_serveraddr_size = 18
	
	def __init__(self, parent, address, name='none given'):
		self._parent = parent
		self._address = address
		self.address = ("[{host}]:{port}" if is_ipv6(address) else "{host}:{port}") \
					.format(host=address[0], port=address[1])
		#self.data = self._packet_list_response
		self.name = name
		self.latency = -1
		self.serverlist = ServerList()
		self.server_count = -1
	
	def request(self):
		self.request_time = time.time()
		self._parent.socket.sendto_q(10 * b'\xff' + b'req2', self._address, self.request_callback)
		self.server_count = 0
	
	def request_callback(self, request_time):
		self.request_time = request_time
	
	def add_from_serverlist(self, data):
		if len(data) % self._serveraddr_size != 0:
			raise Exception("Address packet's size not multiple of the server " + \
					"address struct's size: {datalen}%{addrsize}={modulo} data={data}" \
					.format(datalen=len(data), addrsize=self._serveraddr_size, \
							modulo=(len(data)%self._serveraddr_size), \
							data=' '.join([ "{0:2x}".format(ord(x)) for x in data ])))
		for i in xrange(0, len(data), self._serveraddr_size):
			if data[0:12] == b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xff": # ::ffff:... == IPv4
				serverAddress = (socket.inet_ntoa(data[i+12:i+16]), unpack("!H", data[i+16:i+18])[0])
			else:
				# TODO: workaround for windows as inet_ntop doesn't exist there
				if sys.platform == "win32":
					log('warning', "Can't make IPv6 address on windows from binary: {0!r}".format(data[i:i+16]))
					continue
				serverAddress = (socket.inet_ntop(socket.AF_INET6, data[i:i+16]), unpack("!H", data[i+16:i+18])[0])
			server = Server(self._parent, serverAddress, master=self)
			server.request()
			self._parent.serverlist.add(server)
			self.serverlist.add(server)
	
	def call(self, address, data):
		count_header_len = len(self._packet_count_response)
		if data[0:count_header_len] == self._packet_count_response:
			self.latency = time.time() - self.request_time
			self.server_count += unpack('!H', data[count_header_len:count_header_len+2])[0]
		self.add_from_serverlist(data[len(self._packet_list_response):])
	
	def match(self, **kwargs):
		if not kwargs.has_key("address") or kwargs["address"] != self._address:
			return False
		if not kwargs.has_key("data") or kwargs["data"][0:len(self._packet_list_response)] != self._packet_list_response:
			return False
		return True
	
	def __repr__(self):
		return "<MasterServer name='{name}' address='{address}' servers='{servers}'>" \
			.format(name=self.name, address=self.address, servers=self.server_count)


class Server(Handler):
	_packet_request = 10*b'\xff' + b'gie3'
	_packet_response = 10*b'\xff' + b'inf3'
	
	def __init__(self, parent, address, master=None):
		self._address = address
		self.address = ("[{host}]:{port}" if is_ipv6(address) else "{host}:{port}") \
					.format(host=address[0], port=address[1])
		self._parent = parent
		self.master = master
		self.data = None
		self.reset()
	
	def reset(self):
		self.latency = -1
		self.playerlist = PlayerList()
		self.version = None
		self.name = self.address
		self.map = None
		self.gametype = None
		self.password = None
		self.players = -1
		self.max_players = -1
		self.clients = -1
		self.max_clients = -1
	
	def request(self):
		#log('debug', "Server-ping to " + self.address)
		self.token = chr(randint(1,255))
		self.data = self._packet_response + str(ord(self.token)) + b'\x00'
		self.request_time = time.time()
		self._parent.socket.sendto_q(self._packet_request + self.token, self._address, self.request_callback)
		self._parent.add_handler(self)
	
	def request_callback(self, request_time):
		self.request_time = request_time
	
	def call(self, address, data):
		#log('debug', "Server-callback hit from " + address)
		self.parse(data[len(self.data):])
	
	def parse(self, data):
		self.latency = time.time() - self.request_time
		data = iter(data.split(b'\x00'))
		try:
			self.version = data.next().decode('utf8')
			self.name = data.next().decode('utf8')
			self.map = data.next().decode('utf8')
			self.gametype = data.next().decode('utf8')
			self.password = (data.next()=='1')
			self.players = int(data.next())
			self.max_players = int(data.next())
			self.clients = int(data.next())
			self.max_clients = int(data.next())
			for _ in range(self.clients):
				player = Player()
				player.name=data.next().encode('utf8').strip().decode('utf8')
				player.clan=data.next().encode('utf8').strip().decode('utf8')
				player.country = int(data.next())
				player.score = int(data.next())
				player.playing = (data.next()=='1')
				player.server = self
				self.playerlist.add(player)
		except StopIteration:
			self.reset()
			log('warning', 'unexpected end of data for server ' + str(self))
		for player in self.playerlist:
			self._parent.playerlist.add(player)
	
	def match(self, **kwargs):
		if not kwargs.has_key("address") or kwargs["address"] != self._address:
			return False
		if not kwargs.has_key("data") or kwargs["data"][0:len(self.data)] != self.data:
			return False
		return True
	
	def __repr__(self):
		return "<Server name='{name}' address='{address}'>" \
			.format(name=self.name, address=self.address)


class Player(object):
	def __init__(self):
		self.name = ''
		self.clan = ''
		self.country = None
		self.score = None
		self.server = None
		self.playing = False
	
	def __repr__(self):
		return "<Player name='{name}'>".format(name=self.name)


class ServerList(object):
	def __init__(self):
		self.servers = []
	
	def add(self, server):
		if not isinstance(server, Server):
			raise Exception('Trying to add non-Server object')
		self.servers.append(server)
	
	def find(self, name=None, gametype=None, maxping=None, address=None):
		output = ServerList()
		if name: name = re.compile(name, re.IGNORECASE)
		if gametype: gametype = re.compile(gametype, re.IGNORECASE)
		if address: address = re.compile('%s:[0-9]{1,5}' % address, re.IGNORECASE)
		for server in self.servers:
			if (server.latency != -1) and \
				(name == None or  name.search(server.name)) and \
				(maxping == None or server.latency <= maxping) and \
				(gametype == None or gametype.search(server.gametype)) and \
				(address == None or address.search(server.address)):
				output.add(server)
		return output
	
	def sort(self, cmp=None, key=None, reverse=False):
		self.servers = sorted(self.servers, cmp, key, reverse)
	
	def reverse(self):
		self.players.reverse()
	
	def __iter__(self):
		return iter(self.servers)
	
	def __repr__(self):
		return str(self.servers)


class PlayerList(object):
	def __init__(self):
		self.players = []
	
	def add(self, player):
		if not isinstance(player, Player):
			raise Exception('Trying to add non-Player-object')
		self.players.append(player)
	
	def find(self, name=None, clan=None, country=None, playing=None, server=None):
		output = PlayerList()
		if name: name = re.compile(name, re.IGNORECASE)
		if clan: clan = re.compile(clan, re.IGNORECASE)
		for player in self.players:
			if (name == None or name.search(player.name)) and \
				(clan == None or clan.search(player.clan)) and \
				(country == None or player.country == country) and \
				(server == None or player.server == server) and \
				(playing == None or player.playing == playing):
				output.add(player)
		return output
	
	def sort(self, cmp=None, key=None, reverse=False):
		self.players = sorted(self.players, cmp, key, reverse)
	
	def reverse(self):
		self.players.reverse()
	
	def clear(self):
		del self.players[:]
	
	def __iter__(self):
		return iter(self.players)
	
	def __repr__(self):
		return str(self.players)


class Teeworlds(object):
	def __init__(self, timeout=5):
		#self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		#self.socket.setblocking(0)
		#self._socket.settimeout(2)
		self.timeout = timeout
		self.handlers = HandlerStorage()
		self.serverlist = ServerList()
		self.playerlist = PlayerList()
		self.masterlist = []
		self.socket = MultiSocket(timeout=0.001)
	
	def query_masters(self):
		masters = ["master{0}.teeworlds.com".format(i) for i in range(2, 4+1)]
		for mastername in masters:
			# resolves host and picks the first address
			try:
				info = socket.getaddrinfo(mastername, 8300, 0, socket.SOCK_DGRAM)
			except socket.gaierror as e:
				log('warning', 'getaddrinfo failed: ' + str(e))
				continue
			else:
				master_addr = info[0][4]
				log('debug', "requesting " + mastername + " " + str(master_addr))
				master = MasterServer(self, master_addr, mastername.partition(".")[0])
				master.request()
				self.add_handler(master)
				self.masterlist.append(master)
	
	def run_loop(self):
		last_recv = time.time()
		last_send = 0
		while True:
			try:
				#(data, address) = self.socket.recvfrom(1492)
				#log('debug', "received data from socket: byteslen=" + str(len(data)) + " bytes=" + ' '.join([ "{0:2x}".format(ord(x)) for x in data[0:20] ]))
				#for handler in self.handlers.find(data=data, address=address):
				#	log('debug', "calling handler " + repr(handler) + "with address=" + str(address))
				#	handler.call(address, data)
				#self.socket.process_queue()
				(r, w, x) = self.socket.select(MultiSocket.READ | MultiSocket.WRITE)
				cur_time = time.time()
				if w and cur_time > last_send + 0.005:
					last_send = cur_time
					self.socket.process_queue(1)
				if not r:
					if cur_time > last_recv + self.timeout:
						break
					time.sleep(0.001)
				else:
					last_recv = cur_time
					for sock in r:
						try:
							(data, address) = sock.recvfrom(1492)
							log('debug', "received data from socket: byteslen=" + str(len(data)) + " bytes=" + ' '.join([ "{0:2x}".format(ord(x)) for x in data[0:20] ]))
							for handler in self.handlers.find(data=data, address=address):
								log('debug', "calling handler " + repr(handler) + " with address=" + str(address))
								handler.call(address, data)
						except socket.error as e:
							# Errno 10054 happens when we get ICMP port unreachable, we don't care about that
							if e.errno != 10054:
								raise
			except socket.timeout:
				break
	
	def add_handler(self, handler):
		# improve this
		if not isinstance(handler, Handler):
			raise Exception('Expecting instance of class Handler')
		self.handlers.add(handler)

		
## TWP MODIF
class TWServerRequest(object):
    def __init__(self, timeout=5):
        self.timeout = timeout
        self.handlers = HandlerStorage()
        self.playerlist = PlayerList()
        self.server = None
        self.socket = MultiSocket(timeout=timeout)
    
    def query_port(self, ip, port):
        self.handlers.clear()
        self.playerlist.clear()

        self.server = Server(self, (ip, port), master=self)
        self.server.request()
    
    def run_loop(self):
        last_recv = time.time()
        last_send = 0
        while True:
            try:
                (r, w, x) = self.socket.select(MultiSocket.READ | MultiSocket.WRITE)
                cur_time = time.time()
                if w and cur_time > last_send + 0.005:
                    last_send = cur_time
                    self.socket.process_queue(1)
                if not r:
                    if cur_time > last_recv + self.timeout:
                        break
                    time.sleep(0.001)
                else:
                    last_recv = cur_time
                    for sock in r:
                        try:
                            (data, address) = sock.recvfrom(1492)
                            log('debug', "received data from socket: byteslen=" + str(len(data)) + " bytes=" + ' '.join([ "{0:2x}".format(ord(x)) for x in data[0:20] ]))
                            for handler in self.handlers.find(data=data, address=address):
                                log('debug', "calling handler " + repr(handler) + " with address=" + str(address))
                                handler.call(address, data)
                        except socket.error as e:
                            # Errno 10054 happens when we get ICMP port unreachable, we don't care about that
                            if e.errno != 10054:
                                raise
            except socket.timeout:
                break
    
    def add_handler(self, handler):
        # improve this
        if not isinstance(handler, Handler):
            raise Exception('Expecting instance of class Handler')
        self.handlers.add(handler)
## END: TWP MODIF


if __name__ == "__main__":
	tw = Teeworlds(timeout=2)
	tw.query_masters()
	tw.run_loop()
	servers = tw.serverlist.find(name="^C", gametype="CTF", maxping=0.1)
	servers.sort(key=lambda s: s.latency)
	for server in servers:
			print("{server: <64} [{gametype: ^16}] on {master}: {clients: >2}/{max_clients: >2} - {latency: >4.0f} ms" \
			.format(server=server.name, gametype=server.gametype, master=server.master.name, clients=server.clients, \
					max_clients=server.max_clients, latency=server.latency*1000))

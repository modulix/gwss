#!/usr/bin/env python
from __future__ import print_function
import sys
import os
import time
from datetime import datetime, timedelta
from threading import Thread

import gevent
import json
from WebSocketService import WebSocketService



class WebSocketServer(Thread):
	"""
	This server is used to control all WebSocketServices
	found in ./services/ directory
	Also a list of all current websocked is also checked to
	send "ping" it no activity is detceted in last 42 sec.
	"""
	def __init__(self, logger):
		super(WebSocketServer, self).__init__()
		self.logger = logger
		self.logger.debug("gwss:WebSocketServer init...")
		self.clients = []
		self.services = []
		self.listen = True
		self.daemon = True
		self.track = {}
		#sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "services"))
	def run(self):
		self.logger.debug("gwss:WebSocketServer run...")
		# This server start a service thread for each .py file found in ./services subdirectory
		self.logger.debug("gwss:WebSocketServer starting all ./services :")
		svc_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "services")
		for file_name in os.listdir(svc_dir):
			(fln, fle) = os.path.splitext(file_name)
			if os.path.isfile(os.path.join(svc_dir, file_name)) and fle == ".py" and fln != "__init__":
				self.logger.debug("gwss:service :%s" % file_name)
				service = WebSocketService(self, fln, self.track)
				self.services.append(service)
		for service in self.services:
			service.start()
		# Pooling all clients to send ping message to "inactive" clients
		while self.listen:
			curtime = datetime.now()
			delta = timedelta(seconds=42)
			for client in self.clients:
				if (curtime - self.track[id(client)]["last"]) > delta: 
					self.ping(client)
			# More client, less sleeping... (from 10s to 0.1s)
			# 1->10s, 100->1s, 1000+ -> 0.1s
			if len(self.clients):
				time2sleep = max(0.1, min(10, (100 / len(self.clients))))
			else:
				time2sleep = 10
			gevent.sleep(time2sleep)
			#self.logger.debug("g", end="")
	def ping(self, client):
		self.logger.debug("gwss:ping(%s) %s" % (id(client), client.ip))
		sysdate = datetime.now()
		msg = "ping %s" % sysdate.strftime("%x %X")
		client.send(msg)
		self.track[id(client)]["last"] = sysdate
	def send_all(self, msg):
		if (len(self.clients)):
			self.logger.debug("gwss:send_all %s" % msg)
			for client in self.clients:
				client.send(msg)
				self.track[id(client)]["last"] = datetime.now()
	def add_client(self, client):
		self.logger.debug("gwss:add_client %s" % id(client))
		if client not in self.clients:
			self.clients.append(client)
			self.track[id(client)] = {"last":datetime.now(), "ip": client.ip}
			# Return unique id to this client
			msg = '{"service": "gwss", "action": "subscribe", "data": {"id":"gwss_id", "value":"%s"}}' % id(client)
			client.send(msg)
		for service in self.services:
			service.events.append({"client" : client, "event": "add_client"})
	def del_client(self, client):
		self.logger.debug("gwss:del_client %s" % id(client))
		if client in self.clients:
			self.clients.remove(client)
			del self.track[id(client)]
		for service in self.services:
			if client in service.clients:
				service.del_client(client)
				service.events.append({"client" : client, "event": "del_client"})
	def stop(self):
		self.logger.debug("gwss:stop %s" % self)
		for service in services:
			service.stop()
			service.join()
		self.listen = False
	def __del__(self):
		self.logger.debug("gwss:WebSocketServer dead")


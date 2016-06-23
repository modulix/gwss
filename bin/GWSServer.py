#!/usr/bin/env python
from __future__ import print_function
import sys
import os
import time
from datetime import datetime, timedelta
from threading import Thread

import gevent
import json
from GWSService import GWSService

class GWSServer(Thread):
	"""
	This server is used to control all services
	found in ./services/ directory
	Also a list of all current websocked is also checked to
	send "ping" it no activity is detceted in last 42 sec.
	"""
	def __init__(self, logger):
		super(GWSServer, self).__init__()
		logger.debug("GWSServer init...")
		self.logger = logger
		self.clients = []
		self.services = []
		self.listen = True
		self.daemon = True
		self.track = {}
		#sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "services"))
	def sighup(self):
		self.logger.debug("GWSServer receive SIGHUP signal...(%s)" % self.config)
		#for service in self.services:
		#	self.logger.debug("Service stopping : %s" % service.name)
		#	service.stop()
		#	service.join()
		##reload_services_conf()
		#for service in self.services:
		#	service.start()

	def run(self):
		self.logger.debug("GWSServer run...")
		# This server start a service thread for each .py file found in ./services subdirectory
		self.logger.debug("GWSServer starting all services in %s :" % self.config.services_dir)
		svc_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "services")
		for file_name in os.listdir(svc_dir):
			(fln, fle) = os.path.splitext(file_name)
			if os.path.isfile(os.path.join(svc_dir, file_name)) and fle == ".py" and fln != "__init__":
				self.logger.debug("Service loading : %s" % file_name)
				service = GWSService(self, fln, self.track)
				self.services.append(service)
		self.logger.debug("GWSServer:Trying to run all %d services" % len(self.services))
		for service in self.services:
			self.logger.debug("Service running : %s" % service.name)
			service.start()
		self.logger.debug("GWSServer ready")
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
		self.logger.debug("GWSServer exiting...")
	def ping(self, client):
		self.logger.debug("GWSServer send ping(%s) %s" % (id(client), client.ip))
		sysdate = datetime.now()
		msg = "ping %s" % sysdate.strftime("%x %X")
		client.send(msg)
		self.track[id(client)]["last"] = sysdate
	def send_all(self, msg):
		self.logger.debug("GWSServer:send_all %s" % msg)
		for client in self.clients:
			client.send(msg)
			self.track[id(client)]["last"] = datetime.now()
	def add_client(self, client):
		self.logger.debug("GWSServer:add_client %s" % id(client))
		self.clients.append(client)
		self.track[id(client)] = {"last":datetime.now(), "ip": client.ip}
		# Return unique id to this client
		msg = '{"service": "gwss", "action": "subscribe", "data": {"id":"gwss_id", "value":"%s"}}' % id(client)
		self.logger.debug("GWSServer:ID:%s" % id(client))
		client.send(msg)
	def del_client(self, client):
		self.logger.debug("GWSServer:del_client %s" % id(client))
		self.clients.remove(client)
		# Time for services to process del_client event (some of them use track data)
		gevent.sleep(1)
		del self.track[id(client)]
	def stop(self):
		self.logger.debug("GWSServer:stop %s" % self)
		for service in services:
			service.stop()
			service.join()
			self.listen = False
	def __del__(self):
		self.logger.debug("GWSServer dead")


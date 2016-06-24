#!/usr/bin/env python
from __future__ import print_function
import sys
import os
import time
from datetime import datetime, timedelta
from threading import Thread
from multiprocessing import Pipe
import importlib 
import traceback
from multiprocessing import Queue

import gevent

class GWSServer(Thread):
	"""
	This server is used to control all services
	found in ./services/ directory
	"""
	def __init__(self, logger):
		super(GWSServer, self).__init__()
		logger.debug("GWSServer init...")
		self.logger = logger
		self.clients = {}
		self.services = {}
		self.send_queue = Queue()
		self.listen = True
		self.daemon = True
		#sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "services"))
	def sighup(self):
		self.logger.debug("GWSServer receive SIGHUP signal...(%s)" % self.config)

	def run(self):
		self.logger.debug("GWSServer run...")
		# This server start a service thread for each .py file found in ./services subdirectory
		self.logger.debug("GWSServer starting all services in %s :" % self.config.services_dir)
		svc_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "services")
		for file_name in os.listdir(svc_dir):
			(fln, fle) = os.path.splitext(file_name)
			if os.path.isfile(os.path.join(svc_dir, file_name)) and fle == ".py" and fln != "__init__":
				self.logger.debug("Service loading : %s" % file_name)
		# Get service configuration from ./service/service.py file
				try :
					module = importlib.import_module("services."+fln)
					self.logger.debug("Service init start : %s" % fln)
					service = getattr(module, fln)(self.send_queue)
					self.logger.debug("Service init end : %s" % fln)
					self.services[fln] = service
				except Exception as e:
					self.logger.info("Failed to load service %s" % fln)
					self.logger.debug(traceback.format_exc())
		self.logger.debug("GWSServer ready")
		# Polling all clients to send ping message
		while True:
			client_id,data = self.send_queue.get()
			self.clients[client_id].send(data)
		self.logger.debug("GWSServer exiting...")
	def add_client(self, client):
		self.logger.debug("GWSServer:add_client %s" % id(client))
		self.clients[id(client)] = client
		# Return unique id to this client
		msg = '{"service": "gwss", "action": "subscribe", "data": {"gwss_id":"%s"}}' % id(client)
		self.logger.debug("GWSServer:ID:%s" % id(client))
		client.send(msg)
	def del_client(self, id_client):
		self.logger.debug("GWSServer:del_client %s" % id_client)
		del self.clients[id_client]
		gevent.sleep(1)
	def stop(self):
		self.logger.debug("GWSServer:stop %s" % self)
		for service in services:
			service.stop()
			self.listen = False
	def __del__(self):
		self.logger.debug("GWSServer dead")


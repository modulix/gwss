#!/usr/bin/env python
import sys
import json
import os
import time
import importlib 
from Groups import Groups
from datetime import datetime
from threading import Thread
if sys.version_info.major == 2:
    from Queue import Queue
elif sys.version_info.major == 3:
    from queue import Queue


# Used if service need to send messages at regular intervals
# self.queue.put({"client" : "", "action": "timer", "data": {"id": "UTC", "value": "now"}})

class GWSService(Thread):
	"""
	This thread is in charge to send responses
	to subscribed clients from threaded worker(s)
	"""
	def __init__(self, gwss, name, track):
		super(GWSService, self).__init__()
		gwss.logger.debug("GWSService(%s):init:begin" % name)
		self.name = name
		self.gwss = gwss
		self.track = track
		self.groups = Groups()
		self.workers = []
		self.usages = []
		self.daemon = True
		self.listen = True
		self.queue = Queue()

		# Get service configuration from ./service/service.py file
		self.gwss.logger.debug("GWSService(%s):init:import" % self.name)
		self.module = importlib.import_module("services."+self.name)
		self.gwss.logger.debug("GWSService(%s):init:exec" % self.name)
		self.interface = getattr(self.module, self.name)(self)
		self.gwss.logger.debug("GWSService(%s):init:end" % self.name)

	# Adding new event in the queue
	def add_event(self, event):
		self.gwss.logger.debug("GWSService(%s):add_event:%s" % (self.name, event))
		self.work(event["client"], event["action"], event["data"])

	"""
	Do the asked job through action written in ./services/xxxx.py file
	(xxxx is the service name)
	"""
	def work(self, client, action, data):
		#self.gwss.logger.debug("%s:worker:%s" % (self.service.name, self.action))
		
		if action == "subscribe":
			self.add_client(client)
			return
		elif action == "unsubscribe":
			self.del_client(client)
			return
		try:	
			function = getattr(self.interface, "action_" + action)
		except:
			self.gwss.logger.debug("GWSService(%s):error:unhandled action %s" % (self.name,action))
			client.send ("%s:%s:error:unhandled action" % (self.name,action))
			return
		try:
			function(client, data)
			self.gwss.logger.debug("GWSService(%s):action_complete:%s" % (self.name,action))
		except Exception as e:
			self.gwss.logger.debug("GWSService(%s):error:%s" % (self.name,str(e)))
                        self.send_client(client,"error","runtime error")
	def add_client(self, client):
		"""Adding a new client to this service"""
		self.gwss.logger.debug("GWSService(%s):add_client(%s)"% (self.name, id(client)))
		self.groups.add([client])

	def del_client(self, client):
		"""Removes a client from this service"""
		self.gwss.logger.debug("GWSService(%s):del_client %s" % (self.name, id(client)))
		self.groups.remove([client])

	def send_client(self, client, action, data):
		"""Sends a message by WebSocket to one client"""
		client.send(json.dumps({"action": action, "data":data}))
		try:
			self.track[id(client)]["last"] = datetime.now()
		except:
			self.gwss.logger.debug("GWSService(%s):send_client:not found in %s" % (self.name, self.track))

	# Add a client to a group
	def add_group_client(self, group, client):
		self.groups.tag([client], group)

	# Remove a client from a group
	def del_group_client(self, group, client):
		self.groups.untag([client], group)

	# Send a message by WebSocket to a group of clients
	def send_group(self, group, action, data):
		grp = self.groups.select(group)
		for client in grp:
			self.send_client(client, action, data)

	# Set running flag to stop running
	def stop(self):
		self.gwss.logger.debug("GWSService(%s):stop" % self.name)
		self.listen = False

	#def __del__(self):
		#self.gwss.logger.debug("GWSService(%s) dead" % self.name)


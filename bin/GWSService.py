#!/usr/bin/env python
import sys
import json
import os
import time
from datetime import datetime
from threading import Thread
from Queue import Queue
from GWSSWorker import GWSSWorker

# Used if service need to send messages at regular intervals
class GWSServiceTimer(Thread):
	def __init__(self, heartbeat, queue):
		super(GWSServiceTimer, self).__init__()
		self.daemon = True
		self.queue = queue
		self.heartbeat = heartbeat
	def run(self):
		# Derive is around 0.002 (should be tuned)
		time.sleep(self.heartbeat-0.002)
		self.queue.put({"client" : "", "action": "timer", "data": {"id": "UTC", "value": "now"}})

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
		self.clients = []
		self.groups = []
		self.workers = []
		self.heartbeat = 0
		self.usages = []
		self.daemon = True
		self.listen = True
		self.queue = Queue()
		# Get service configuration from ./service/service.py file
		self.gwss.logger.debug("GWSService(%s):init:import" % self.name)
		exec("from services import %s" % self.name)
		self.gwss.logger.debug("GWSService(%s):init:exec" % self.name)
		exec("%s.%s(self, gwss)" % (self.name, self.name))
		self.gwss.logger.debug("GWSService(%s):init:end" % self.name)

	# Adding new event in the queue
	def add_event(self, event):
		self.gwss.logger.debug("GWSService(%s):add_event:%s" % (self.name, event))
		self.queue.put(event)

	# Start service work
	def run(self):
		self.gwss.logger.debug("GWSService(%s):run" % self.name)
		if self.heartbeat:
			self.gwss.logger.debug("GWSService(%s):starting timer %d" % (self.name, self.heartbeat))
			self.timer = GWSServiceTimer(self.heartbeat, self.queue)
			self.timer.start()
		while self.listen:
			evt = self.queue.get()
			#self.gwss.logger.debug("GWSService(%s):%s..." % (self.name, evt))
			if evt["action"] == "timer":
				self.timer = GWSServiceTimer(self.heartbeat, self.queue)
				self.timer.start()
			self.worker = GWSSWorker(self.gwss, self, evt["client"], evt["action"], evt["data"])
			self.worker.start()
			#self.worker.join()
		self.gwss.logger.debug("GWSService(%s) stopping..." % self.name)

	# Adding a new client to this service
	def add_client(self, client):
		self.gwss.logger.debug("GWSService(%s):add_client(%s)"% (self.name, id(client)))
		self.clients.append(client)
		self.add_event({"client" : client, "action": "add_svc_client", "data": {"id": id(client), "value": self.name}})
		# for each new client shall we launch a worker ?!
		"""
			if "sync" in self.usages:
				self.gwss.logger.debug("GWSService(%s):sync (1 -> 1)" % self.name)
				self.worker = GWSService(self.gwss, self, client, "add_client")
				#self.add_event({"client" : client, "action": "client_start"})
				self.worker.start()
				self.worker.join()
			if "thread" in self.usages:
				# Default usage, "thread"
				self.gwss.logger.debug("GWSService(%s):thread (1 -> 1)" % self.name)
				self.worker = GWSSWorker(self.gwss, self, client, "add_client")
				self.worker.start()
		"""

	# Removing a client from this service
	def del_client(self, client):
		self.gwss.logger.debug("GWSService(%s):del_client %s" % (self.name, id(client)))
		if client in self.clients:
			self.clients.remove(client)
			self.add_event({"client" : client, "action": "del_svc_client", "data": {"id": id(client), "value": self.name}})

	# Receive a new message on the WebSocket
	def receive(self, action, client, data):
		self.gwss.logger.debug("GWSService(%s):%s:%s:%s" % (self.name, action, id(client),data))
		# Using the "action" function of ./services/service.py
		exec("from services import %s" % self.name)
		exec("%s.action(self.gwss, self, action, client, data)" % self.name)
		self.gwss.logger.debug("GWSService(%s):action:%s:end" % (self.name, id(client)))

	# Send a message by WebSocket to one client
	def send_client(self, client, msg):
		client.send(msg)
		try:
			self.track[id(client)]["last"] = datetime.now()
		except:
			self.gwss.logger.debug("GWSService(%s):send_client:not found in %s" % (self.name, self.track))

	# Send a message by WebSocket to all clients
	def send_all(self, msg):
		#self.gwss.logger.debug("GWSService(%s):send_all:%.255s" % (self.name, msg))
		for client in self.clients:
			self.send_client(client, msg)

	# Create a new group
	def add_group(self, group, client):
		self.groups.append({"name": group, "owner": client, "clients": [ id(client) ]})
		#self.add_event({"client" : client, "action": "add_group", "data": {"id": group, "value": group}})

	# Remove a group (need to be owner)
	def del_group(self, group, client):
		for grp in self.groups:
			if grp["name"] == group and grp["owner"] == id(client):
				del grp
				#self.add_event({"client" : client, "action": "del_group", "data": {"id": group, "value": group}})

	# Add a client to a group
	def add_group_client(self, group, client):
		for grp in self.groups:
			if grp["name"] == group:
				grp["clients"].append(id(client))
				self.add_event({"client" : client, "action": "add_group_client", "data": {"id": group, "value": group}})

	# Remove a client from a group
	def del_group_client(self, group, client):
		for grp in self.groups:
			if grp["name"] == group:
				if (id(client) in grp["clients"]):
					grp["clients"].remove(id(client))
					self.add_event({"client" : client, "action": "del_group_client", "data": {"id": group, "value": group}})

	# Send a message by WebSocket to a group of clients
	def send_group(self, group, msg):
		for grp in groups:
			if grp == group.name:
				for client in self.clients:
					self.send_client(client, msg)

	# Set running flag to stop running
	def stop(self):
		self.gwss.logger.debug("GWSService(%s):stop" % self.name)
		self.listen = False

	#def __del__(self):
		#self.gwss.logger.debug("GWSService(%s) dead" % self.name)


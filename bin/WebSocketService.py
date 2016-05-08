#!/usr/bin/env python
from __future__ import print_function
import sys
import json
import os
import time
from threading import Thread
import gevent
from datetime import datetime
from WebSocketWorker import WebSocketWorker

class WebSocketService(Thread):
	"""
	This thread is in charge to send responses
	to subscribed clients from threaded worker(s)
	"""
	def __init__(self, gwss, name, track):
		print("WebSocketService(%s) init..." % name)
		super(WebSocketService, self).__init__()
		self.name = name
		self.gwss = gwss
		self.track = track
		self.clients = []
		self.groups = []
		self.listen = True
		self.daemon = True
		self.workers = []
		self.events = []
		self.heartbeat = 0
		self.usages = []
		# Service configuration
		exec("from services import %s" % self.name)
		exec("%s.%s(self, self.gwss)" % (self.name, self.name))

	# Used by service needing to send messages at regular intervals
	def timer(self):
		# This
		gevent.sleep(self.heartbeat)
		self.events.append({"client" : self.clients, "event": "timer"})

	# Start service working
	def run(self):
		print("WebSocketService %s run..." % self.name)
		if self.heartbeat:
			gevent.spawn(self.timer)
		while self.listen:
			for evt in self.events:
				self.worker = WebSocketWorker(self.gwss, self, evt["client"], evt["event"])
				self.worker.start()
				#self.worker.join()
				if evt["event"] == "timer":
					gevent.spawn(self.timer)
				self.events.remove(evt)
			gevent.sleep(0.01)

	def add_client(self, client):
		print("%s:add_client(%s)"% (self.name, id(client)))
		if client not in self.clients:
			self.clients.append(client)
			self.events.append({"client" : client, "event": "client_start"})
			# for each new client shall we launch a worker ?!
			if "sync" in self.usages:
				print("%s:sync (1 -> 1)" % self.name)
				self.worker = WebSocketWorker(self.gwss, self, client, "add_client")
				self.worker.start()
				self.worker.join()
			if "thread" in self.usages:
				# Default usage, "thread"
				print("%s:thread (1 -> 1)" % self.name)
				self.worker = WebSocketWorker(self.gwss, self, client, "add_client")
				self.worker.start()
				# 
	def del_client(self, client):
		print("%s:del_client %s" % (self.name, id(client)))
		if client in self.clients:
			self.clients.remove(client)
	def send_client(self, client, msg):
		if client in self.clients:
			client.send(msg)
			self.track[id(client)]["last"] = datetime.now()
		else:
			print("%s:send_client(%s,%s) not found..." % (self.name, id(client), msg))
	def receive(self, client, msg):
		print("%s:message:%s(%s)" % (self.name, id(client),msg))
		service = action = data = ""
		message = json.loads(msg)
		service = message["service"]
		action = message["action"]
		data = message["data"]
		print("service=%s action=%s data=%s" % (service, action, data))
		if action == "unsubscribe":
			self.events.append({"client" : client, "event": "del_svc_client"})
			self.del_client(client)
		if action == "subscribe":
			self.add_client(client)
			self.events.append({"client" : client, "event": "add_svc_client"})
		# Using the "receive" function of ./services/service.py
		exec("from services import %s" % service)
		exec("%s.receive(self.gwss, self, action, client, data)" % service)
	def send_all(self, msg):
		if len(self.clients):
			#print("%s:send_all %s" % (self.name, msg))
			for client in self.clients:
				self.send_client(client, msg)
	def stop(self):
		print("%s:stop" % self.name)
		self.listen = False
	#def __del__(self):
		#print("%s:WebSocketService dead" % self.name)


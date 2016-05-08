#!/usr/bin/env python
from __future__ import print_function
from threading import Thread

class WebSocketWorker(Thread):
	"""
	This thread is in going to do the asked job
	thru code written in run def of ./services/xxxx.py file
	(xxxx is the service name)
	"""
	def __init__(self, gwss, service, client, event):
		super(WebSocketWorker, self).__init__()
		self.daemon = True
		self.gwss = gwss
		self.service = service
		self.client = client
		self.event = event
	def run(self):
		exec("from services import %s" % self.service.name)
		exec("%s.event(self.gwss, self.service, self.client, self.event)" % (self.service.name))
		#print("w", end="")
	#def __del__(self):
		#print("WebSocketWorker dead")

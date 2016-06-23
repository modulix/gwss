#!/usr/bin/env python
from __future__ import print_function
import sys
import os
import time
import json
from datetime import datetime
#from threading import Thread

#class GWSSHandler(Thread):
class GWSSHandler():
	def __init__(self, gwss, environ, ws):
		#gwss.logger.debug("GWSSHandler(%s):init" % id(self))
		#super(GWSSHandler, self).__init__()
		self.gwss = gwss
		self.ws = ws
		self.environ = environ
		self.ip = ""
		self.listen = True
		self.ip = ""
		try:
			self.ip = self.environ["HTTP_X_REAL_IP"]
		except:
			pass
			#sys.exc_clear()
		if not self.ip:
			try:
				self.ip = self.environ["REMOTE_ADDR"]
			except:
				self.ip = "127.0.0.1"
				pass
				#sys.exc_clear()
		self.gwss.logger.debug("GWSSHandler(%s):init:%s" % (id(self), self.ip))
	def send(self,msg):
		try:
			self.ws.send(msg)
		except:
			self.listen = False
			pass
	def run(self):
		self.gwss.logger.debug("GWSSHandler(%s) running..." % id(self))
		self.gwss.add_client(self)
		while self.listen:
			try:
				message = self.ws.receive()
			except:
				message = None
				self.listen = False
				pass
				#sys.exc_clear()
			if message is None:
				self.gwss.logger.debug("GWSSHandler:Socket closed {}".format(datetime.now().strftime("%H:%M:%S %f")))
				self.listen = False
			else:
				self.gwss.logger.debug("GWSSHandler(%s):receive:%s" % (id(self),message))
				try:
					msg = json.loads(message)
					msg["client"] = self
				except:
					self.gwss.logger.debug("GWSSHandler(%s):error not valid JSON msg:%s" % (id(self),message))
					sys.exc_clear()
				for svc in self.gwss.services:
					if msg["service"] == svc.name:
						svc.add_event(msg)
		self.gwss.logger.debug("GWSSHandler(%s) stopping..." % id(self))
		self.gwss.del_client(self)
	def __del__(self):
		self.gwss.logger.debug("GWSSHandler(%d) dead" % id(self))

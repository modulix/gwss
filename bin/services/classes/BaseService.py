#!/usr/bin/env python
import json
from Groups import Groups

class BaseService(object):
	"""
	Daemon mode.
	Spins a separate process at start, and listen to a queue to treat incomming actions.
	Should be prefered when performance isn't an issue
	"""
	def __init__(self, name, send_queue):
		#logger.debug("GWSService(%s):init:begin" % name)
		self.name = name
		self.send_queue = send_queue
		#Groups of clients (used for all client pushes)
	def add_event(self, event):
		#self.logger.debug("GWSService(%s):add_event:%s" % (self.name, event))
		client, action, data = event["client"], event["action"], event["data"]
		if action == "subscribe":
			self.add_client(client)
			return
		elif action == "unsubscribe":
			self.del_client(client)
			return
		try:
			self.exec_action (client, action, data)
			#self.logger.debug("GWSService(%s):action_complete:%s" % (self.name,action))
		except Exception as e:
			pass
			#self.logger.debug("GWSService(%s):error:%s" % (self.name,str(e)))
	def send_client(self, client, action, data):
		"""Sends a message by WebSocket to one client"""
		self.send_queue.put((client,json.dumps({"service":self.name, "action": action, "data":data})))



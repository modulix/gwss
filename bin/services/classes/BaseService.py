#!/usr/bin/env python
import traceback
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
	def add_event(self, action, data):
		#self.logger.debug("GWSService(%s):add_event:%s" % (self.name, event))
		try:
			self.exec_action (action, data)
			#self.logger.debug("GWSService(%s):action_complete:%s" % (self.name,action))
		except Exception as e:
			print traceback.format_exc()
			#self.logger.debug("GWSService(%s):error:%s" % (self.name,str(e)))
	def send_action(self, service, action, **kwargs):
		"""Sends a message to the message broker"""
		self.send_queue.put({"service":service, "action": action, "data":kwargs})
	def action_subscribe (self, **kwargs):
		pass
	def action_unsubscribe (self, **kwargs):
		pass



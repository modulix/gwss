#!/usr/bin/env python
import json
from BaseService import BaseService
from multiprocessing import Process, Pipe
import traceback

class DaemonService(BaseService):
	"""
	In charge to receive messages and send responses to subscribed clients
	"""
	def __init__(self, name):
		super(DaemonService, self).__init__(name)
		self.proc = Process(target=self.main)
		self.parent_end, self.child_end = Pipe()
		self.listen_fileno = self.parent_end.fileno()
		self.proc.start()
		
	def listen (self, timeout=None):
		if not self.child_end.poll(timeout):
			return
		action, data = self.child_end.recv()
		try:
			function = getattr(self, "action_" + action)
			#self.logger.debug("GWSService(%s):error:unhandled action %s" % (self.name,action))
			function(**data)
		except Exception as e:
			print traceback.format_exc()
	def add_event(self, action, data):
		self.parent_end.send((action, data,))
		#self.logger.debug("%s:worker:%s" % (self.service.name, self.action))
	def send_action(self, service, action, **kwargs):
		self.child_end.send((service, action, kwargs))
	def recv_action(self):
		return self.parent_end.recv()


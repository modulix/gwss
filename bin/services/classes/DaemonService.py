#!/usr/bin/env python
import json
from Groups import Groups
from BaseService import BaseService
from multiprocessing import Process, Pipe

class DaemonService(BaseService):
	"""
	In charge to receive messages and send responses to subscribed clients
	"""
	def __init__(self, name, send_queue):
		super(DaemonService, self).__init__(name, send_queue)
		self.proc = Process(target=self.listen)
		self.recv_proc, self.send_proc = Pipe(False)
		self.proc.start()
		
	def listen (self):
		while True:
			client, action, data = self.recv_proc.recv()
			try:
				function = getattr(self, "action_" + action)
			except Exception as e:
				#self.logger.debug("GWSService(%s):error:unhandled action %s" % (self.name,action))
				return
			function(client, data)
	def exec_action(self, client, action, data):
		self.send_proc.send((client, action, data,))
		#self.logger.debug("%s:worker:%s" % (self.service.name, self.action))


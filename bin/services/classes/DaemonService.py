#!/usr/bin/env python
import json
from BaseService import BaseService
from multiprocessing import Process, Pipe
import traceback

class DaemonService(BaseService):
	"""
	In charge to receive messages and send responses to subscribed clients
	"""
	def __init__(self, name, send_queue):
		super(DaemonService, self).__init__(name, send_queue)
		self.proc = Process(target=self.main)
		self.recv_proc, self.send_proc = Pipe(False)
		self.proc.start()
		
	def listen (self, timeout=None):
		if not self.recv_proc.poll(timeout):
			return
		action, data = self.recv_proc.recv()
		try:
			function = getattr(self, "action_" + action)
			#self.logger.debug("GWSService(%s):error:unhandled action %s" % (self.name,action))
			function(**data)
		except Exception as e:
			print traceback.format_exc()
	def exec_action(self, action, data):
		self.send_proc.send((action, data,))
		#self.logger.debug("%s:worker:%s" % (self.service.name, self.action))


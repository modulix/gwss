#!/usr/bin/env python
import json
from Groups import Groups
from BaseService import BaseService

class SimpleService(BaseService):
	"""
	No daemon mode.
	This service's actions are expected to be non-blocking,
	otherwise the server will stall during them. 
	"""
	def exec_action(self, client, action, data):
		"""
		Do the asked action through action_ prefixed method
		"""
		#self.logger.debug("%s:worker:%s" % (self.service.name, self.action))
		try:
			method = getattr(self, "action_" + action)
		except:
			#self.logger.debug("GWSService(%s):error:unhandled action %s" % (self.name,action))
			return
		method(client, data)


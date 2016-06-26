#!/usr/bin/env python
import json
from BaseService import BaseService

class SimpleService(BaseService):
	"""
	No daemon mode.
	This service's actions are expected to be non-blocking,
	otherwise the server will stall during them. 
	"""
	def exec_action(self, action, data):
		"""
		Do the asked action through action_ prefixed method
		"""
		#self.logger.debug("%s:worker:%s" % (self.service.name, self.action))
		method = getattr(self, "action_" + action)
		#self.logger.debug("GWSService(%s):error:unhandled action %s" % (self.name,action))
		method(**data)


#!/usr/bin/env python
import traceback
from multiprocessing import Pipe
class BaseService(object):
	"""
	Each service is composed of two ends : a base service which communicates
	with the core, and a module part which executes the functions (may be local or distant).
	"""
	def __init__(self, name):
		#logger.debug("GWSService(%s):init:begin" % name)
		self.name = name
	def set_services (self, services):
		self.services = services
	def exec_action(self, action, data):
		#self.logger.debug("GWSService(%s):add_event:%s" % (self.name, event))
		try:
			"""
			Do the asked action through action_ prefixed method
			"""
			#self.logger.debug("%s:worker:%s" % (self.service.name, self.action))
			method = getattr(self, "action_" + action)
			#self.logger.debug("GWSService(%s):error:unhandled action %s" % (self.name,action))
			method(**data)
			#self.logger.debug("GWSService(%s):action_complete:%s" % (self.name,action))
		except Exception as e:
			print traceback.format_exc()
			#self.logger.debug("GWSService(%s):error:%s" % (self.name,str(e)))
	def action_subscribe (self, **kwargs):
		pass
	def action_unsubscribe (self, **kwargs):
		pass



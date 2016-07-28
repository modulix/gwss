#!/usr/bin/env python
import traceback
from multiprocessing import Pipe
import logging

class BaseService(object):
    """
    Each service is composed of two ends : a base service which communicates
    with the core, and a module part which executes the functions (may be local or distant).
    """
    def __init__(self, name):
        self.logger = logging.getLogger()
        self.logger.debug("GWSService(%s):init" % name)
        self.name = name
        self.daemon = True
    def set_services (self, services):
        self.services = services
    def exec_action(self, action, data):
        self.logger.debug("GWSService(%s):exec_action:%s" % (self.name, action))
        try:
            """
            Do the asked action through action_ prefixed method
            """
            self.logger.debug("%s:action_%s:%s" % (self.name, action, data))
            method = getattr(self, "action_" + action)
            method(**data)
        except Exception as e:
            self.logger.debug("GWSService(%s):error:%s" % (self.name,str(e)))
            self.logger.debug(traceback.format_exc())
    def action_subscribe (self, **kwargs):
        pass
    def action_unsubscribe (self, **kwargs):
        pass



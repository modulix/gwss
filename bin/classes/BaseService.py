#!/usr/bin/env python
import traceback
from multiprocessing import Pipe
import common.logger

class BaseService(object):
    """
    Each service is composed of two ends : a base service which communicates
    with the core, and a module part which executes the functions (may be local or distant).
    """
    def __init__(self, name, config):
        self.logger = common.logger.get_logger_from_config(config.get("logs", []), name)
        self.logger.info("GWSService(%s):init" % name)
        self.config = config
        self.name = name
        self.clientvars = {}
    def set_services (self, services):
        self.services = services
    def exec_action(self, action, data):
        """ Transform action request into action_ prefixed method call """
        self.logger.debug("GWSService(%s):exec_action:%s" % (self.name, action))
        try:
            self.logger.debug("%s:action_%s:%s" % (self.name, action, data))
            method = getattr(self, "action_" + action)
            method(**data)
        except Exception as e:
            self.logger.warning("GWSService(%s):error:%s" % (self.name,str(e)))
            self.logger.debug(traceback.format_exc())
    def action_subscribe (self, client):
        self.clientvars[client] = {}
    def action_unsubscribe (self, client):
        del self.clientvars[client]



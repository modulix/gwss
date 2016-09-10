#!/usr/bin/env python
import traceback
from multiprocessing import Pipe
import common.logger

def make_msg(service, action, data={}, source=None):
    msg = {"service":service, "action":action, "data":data}
    if source:
        msg["source"] = source
    return msg

class BaseService(object):
    """
    Each service is composed of two ends : a base service which communicates
    with the core, and a module part which executes the functions (may be local or distant).
    """
    def __init__(self, name, config):
        self.logger = common.logger.get_logger_from_config(config.get("logs", []), name)
        self.logger.info("Service init")
        self.config = config
        self.name = name
        self.clientvars = [] 
    def set_services (self, services):
        self.services = services
    def exec_action(self, msg):
        """ Transform action request into action_ prefixed method call """
        try:
            action = msg.pop("action")
            method = getattr(self, "action_" + action)
            method(msg)
            self.logger.debug("Executed action: %s" % action)
        except Exception as e:
            self.logger.error("Service excution fail: %s" % str(e))
            self.logger.debug(traceback.format_exc())
    def action_subscribe (self, msg):
        self.clientvars.append({"source": msg["source"]})
    def action_unsubscribe (self, msg):
        self.clientvars = [c for c in self.clientvars if not c["source"] == msg["source"]]
    def reply(self, msg, data={}, source_action=None, source_data={}):
        reply = msg.pop("source")
        if source_action:
            reply["source"] = make_msg(self.name, source_action, source_data)
        if reply["data"]:
            data = data.copy()
            data.update(reply["data"])
        reply["data"] = data
        self.send_action(reply)



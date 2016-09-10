#!/usr/bin/env python
from classes.SimpleService import SimpleService

class EchoService(SimpleService):
    """
    This service sends back received messages 
    """
    def action_kbdecho(self, client, **data):
        self.logger.debug("%s:EchoService:%s" % (self.name, data))
        self.send_action("clients_master", "send_client", client=client, js_action="display", data=data)

def kbdecho(config):
    return EchoService("kbdecho", config)

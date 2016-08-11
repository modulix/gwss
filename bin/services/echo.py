#!/usr/bin/env python
from classes.SimpleService import SimpleService

class EchoService(SimpleService):
    """
    This service broadcast all received messages to all connected clients
    """
    def action_echo(self, client, data):
        self.logger.debug("%s:EchoService:%s" % (self.name, data))
        self.send_action("clients", "send_client", client=client, js_action="display", data=data)

def echo():
    return EchoService("echo")

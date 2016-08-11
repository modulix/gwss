#!/usr/bin/env python
from classes.DaemonService import DaemonService
from datetime import datetime
import time

class SysdateService(DaemonService):
    """
    This service broadcast global sysdate to all subscribed clients
    """
    def __init__ (self, *args):
        self.clients = [] 
        super(SysdateService, self).__init__(*args)
    def action_subscribe(self, client, id="", value=""):
        self.clients.append(client)
    def action_unsubscribe(self, client, id="", value=""):
        try:
            self.clients.remove(client)
        except:
            pass
    def main (self):
        while True:
            msg = datetime.now().strftime("%x %X")
            self.listen(1-0.001)
            for client in self.clients:
                self.send_action("clients", "send_client", client=client, js_action="display", data={"id":"gwss_time", "value": msg})

def sysdate():
    return SysdateService("sysdate")

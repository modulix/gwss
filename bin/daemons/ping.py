#!/usr/bin/env python
from classes.DaemonService import DaemonService
import time

class PingService(DaemonService):
    """
    This service broadcast a ping to all subscribed clients
    """
    def __init__ (self, *args):
        self.clients = [] 
        super(PingService, self).__init__(*args)
    def action_subscribe(self, client):
        self.clients.append(client)
    def action_unsubscribe(self, client):
        self.clients.remove(client)
    def main (self):
        while True:
            t = time.time()
            diff = 0
            while diff < 15:
                self.listen(15-diff)
                diff = time.time() - t
            for client in self.clients :
                self.send_action("clients", "send_client", client=client, js_action="ping", data={})

def ping():
    return PingService("ping")

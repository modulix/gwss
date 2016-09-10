#!/usr/bin/env python
import json
from BaseService import BaseService
from multiprocessing import Process, Pipe
import traceback

class DaemonService(BaseService):
    """
    In charge to receive messages and send responses to subscribed clients
    """
    def __init__(self, name, config):
        super(DaemonService, self).__init__(name, config)
        self.proc = Process(target=self.main)
        self.proc.daemon = True
        self.parent_end, self.child_end = Pipe()
        self.listen_fileno = self.parent_end.fileno()
        self.proc.start()

    def listen (self, timeout=None):
        if not self.child_end.poll(timeout):
            return
        action, data = self.child_end.recv()
        try:
            function = getattr(self, "action_" + action)
            function(**data)
        except Exception as e:
            print(traceback.format_exc())
    def add_event(self, action, data):
        self.logger.debug("Piping action %s to process" % action)
        self.parent_end.send((action, data,))
    def send_action(self, service, action, **kwargs):
        self.child_end.send((service, action, kwargs))
    def recv_action(self):
        return self.parent_end.recv()


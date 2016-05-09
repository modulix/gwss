#!/usr/bin/env python
import sys
import json
import os
import time
from threading import Thread
import gevent
from datetime import datetime

from WebSocketWorker import WebSocketWorker

class WebSocketService(Thread):
    """
    This thread is in charge to send responses
    to subscribed clients from threaded worker(s)
    """
    def __init__(self, gwss, name, track):
        gwss.logger.debug("WebSocketService(%s) init..." % name)
        super(WebSocketService, self).__init__()
        self.name = name
        self.gwss = gwss
        self.track = track
        self.clients = []
        self.groups = []
        self.workers = []
        self.events = []
        self.heartbeat = 0
        self.usages = []
        self.daemon = True
        self.listen = True
        # Get service configuration from ./service/service.py file
        exec("from services import %s" % self.name)
        exec("%s.%s(self, self.gwss)" % (self.name, self.name))

    # Used if service need to send messages at regular intervals
    def timer(self):
        if self.heartbeat > 1:
            self.gwss.logger.debug("%s:timer" % self.name)
        gevent.sleep(self.heartbeat)
        self.events.append({"client" : self.clients, "event": "timer"})

    # Start service working
    def run(self):
        self.gwss.logger.debug("WebSocketService %s run..." % self.name)
        if self.heartbeat:
            gevent.spawn(self.timer)
        while self.listen:
            for evt in self.events:
                if len(self.clients):
                    self.worker = WebSocketWorker(self.gwss, self, evt["client"], evt["event"])
                    self.worker.start()
                    #self.worker.join()
                if evt["event"] == "timer":
                    gevent.spawn(self.timer)
                self.events.remove(evt)
                gevent.sleep(0)
            gevent.sleep(0)
        self.gwss.logger.debug("WebSocketService %s stopping..." % self.name)

    # Adding a new client to this service
    def add_client(self, client):
        self.gwss.logger.debug("%s:add_client(%s)"% (self.name, id(client)))
        if client not in self.clients:
            self.clients.append(client)
            #self.events.append({"client" : client, "event": "client_start"})
            # for each new client shall we launch a worker ?!
            """
            if "sync" in self.usages:
                self.gwss.logger.debug("%s:sync (1 -> 1)" % self.name)
                self.worker = WebSocketWorker(self.gwss, self, client, "add_client")
                self.worker.start()
                self.worker.join()
            """
            if "thread" in self.usages:
                # Default usage, "thread"
                self.gwss.logger.debug("%s:thread (1 -> 1)" % self.name)
                self.worker = WebSocketWorker(self.gwss, self, client, "add_client")
                self.worker.start()

    # Removing a client from this service
    def del_client(self, client):
        self.gwss.logger.debug("%s:del_client %s" % (self.name, id(client)))
        if client in self.clients:
            self.clients.remove(client)

    # Receive a new message on the WebSocket
    def receive(self, client, msg):
        self.gwss.logger.debug("%s:receive:%s(%s)" % (self.name, id(client),msg))
        service = action = data = ""
        message = json.loads(msg)
        service = message["service"]
        action = message["action"]
        data = message["data"]
        self.gwss.logger.debug("service=%s action=%s data=%s" % (service, action, data))
        if action == "unsubscribe":
            self.events.append({"client" : client, "event": "del_svc_client"})
            self.del_client(client)
        if action == "subscribe":
            self.add_client(client)
            self.events.append({"client" : client, "event": "add_svc_client"})
        # Using the "receive" function of ./services/service.py
        exec("from services import %s" % service)
        exec("%s.receive(self.gwss, self, action, client, data)" % service)

    # Send a message by WebSocket to one client
    def send_client(self, client, msg):
        if client in self.clients:
            client.send(msg)
            self.track[id(client)]["last"] = datetime.now()
        else:
            self.gwss.logger.debug("%s:send_client(%s,%s) not found..." % (self.name, id(client), msg))

    # Send a message by WebSocket to all clients
    def send_all(self, msg):
        for client in self.clients:
            self.send_client(client, msg)

    # Create a new group
    def add_group(self, group, client):
        groups.append({"name": group, "owner": client, "clients": [ id(client) ]})
        self.events.append({"client" : client, "event": "add_group", "name": group})

    # Remove a group (need to be owner)
    def del_group(self, group, client):
        for grp in self.groups:
            if grp["name"] == group and grp["owner"] == id(client):
                del grp
                self.events.append({"client" : client, "event": "del_group", "name": name})

    # Add a client to a group
    def add_group_client(self, group, client):
        for grp in self.groups:
            if grp["name"] == group:
                grp["clients"].append(id(client))
                self.events.append({"client" : client, "event": "add_group_client", "client": id(client)})

    # Remove a client from a group
    def del_group_client(self, group, client):
        for grp in self.groups:
            if grp["name"] == group:
                if (id(client) in grp["clients"]:
                    grp["clients"].remove(id(client))
                    self.events.append({"client" : client, "event": "del_group_client", "client": id(client)})

    # Send a message by WebSocket to a group of clients
    def send_group(self, group, msg):
        for grp in groups:
            if grp == group.name:
                for client in self.clients:
                    self.send_client(client, msg)

    # Set running flag to stop running
    def stop(self):
        self.gwss.logger.debug("%s:stop" % self.name)
        self.listen = False

    #def __del__(self):
        #self.gwss.logger.debug("%s:WebSocketService dead" % self.name)


from classes.DaemonService import DaemonService

import json
from threading import Thread
import gevent
from gevent import socket
from geventwebsocket.handler import WebSocketHandler
from gevent.pywsgi import WSGIServer
from classes.GWSSHandler import GWSSHandler
from classes.GWSGIHandler import GWSGIHandler
from gevent.pool import Pool
import logging

#if sys.version_info.major == 2:
    #print("running Python 2.x")
    #import urlparse

#if sys.version_info.major == 3:
    #print("running Python 3.x")
    #import urllib.parse as urlparse

#server = "127.0.0.1"
#port = 10034
#max_clients = 1000
import config

class WSGIThread (Thread):
    def __init__(self, dispatch):
        super(WSGIThread, self).__init__()
        self.logger = logging.getLogger()
        self.logger.debug("WSGIThread(%s):init" % id(self))
        self.dispatch = dispatch
        self.daemon = True
    def run(self):
        self.logger.debug("WSGIThread(%s):run" % id(self))
        pool = Pool(config.max_clients)
        self.logger.info("WebSocket Server is listening at http://%s:%s/" % (config.server, config.port))
        gwsgi = WSGIServer((config.server, config.port), self.dispatch, spawn=pool, handler_class=WebSocketHandler)
        gwsgi.serve_forever()



class ClientService(DaemonService):
    def gwss_dispatch(self, environ, response):
        """
        For each connection we use one of this handlers:
            GWSSHandler:WebSocket (permanent connection)
            GWSGIHandler:WSGI (include /api requests)
        """
        url = environ["PATH_INFO"]
        #self.logger.debug("gwss_dispatch(%s)" % environ)
        ws = False
        try:
            ws = environ["wsgi.websocket"]
        except KeyError:
            pass
        # Is this a WebSocket request (we need to maintain this connection)
        if ws:
            self.logger.debug("ClientService:gwss_dispatch:WebSocket:%s" % (url))
            wshandler = GWSSHandler(self, environ, ws)
            gevent.spawn(wshandler.run())
            return(None)
        # So, this is a WSGI request (not a WebSocket)
        else:
            self.logger.debug("ClientService:gwss_dispatch:WSGI:%s" % (url))
            wsgihandler = GWSGIHandler(self, environ, response)
            msg = wsgihandler.run()
            return(msg)

    def add_client(self, client):
        self.clients[id(client)] = client
    def del_client(self, client):
        self.logger.debug("ClientService:del_client %s" % id(client))
        del self.clients[id(client)]
    def action_send_client (self, client, js_action, data):
        self.logger.debug("ClientService:action_send_client(%s,%s,%s)" % (client,js_action, data))
        try:
            self.clients[client].send(json.dumps({"js_action":js_action, "data":data}))
        except:
            # Lost one...
            self.del_client(client)

    def main(self):
        self.clients = {}
        self.server = WSGIThread(self.gwss_dispatch)
        self.server.start()
        while True:
            self.listen()
        # Starting network listener
        #gevent.signal(signal.SIGQUIT, gevent.kill)
        #gevent.signal(signal.SIGHUP, gwss.sighup)

def clients():
    return ClientService("clients")

from classes.DaemonService import DaemonService

import json
import logging
from threading import Thread
import gevent
from gevent import socket
from geventwebsocket.handler import WebSocketHandler
from gevent.pywsgi import WSGIServer
from classes.GWSSHandler import GWSSHandler
from classes.GWSGIHandler import GWSGIHandler
from gevent.pool import Pool

from routr import route
from routr.static import static
from webob import Request, exc

#if sys.version_info.major == 2:
    #print("running Python 2.x")
    #import urlparse

#if sys.version_info.major == 3:
    #print("running Python 3.x")
    #import urllib.parse as urlparse

class WSGIThread (Thread):
    def __init__(self, logger_name, config, dispatch):
        super(WSGIThread, self).__init__()
        self.dispatch = dispatch
        self.logger = logging.getLogger(logger_name)
        self.daemon = True
        self.config = config
    def run(self):
        self.logger.debug("WSGIThread(%s):run" % id(self))
        pool = Pool(self.config["max_clients"])
        self.logger.info("WebSocket Server is listening at http://%s:%s/" % (self.config["server"], self.config["port"]))
        gwsgi = WSGIServer((self.config["server"], self.config["port"]), self.dispatch, spawn=pool, handler_class=WebSocketHandler)
        gwsgi.serve_forever()

class ClientService(DaemonService):
    def gwss_dispatch(self, environ, response):
        """
        For each connection we use one of this handlers:
            GWSSHandler:WebSocket (permanent connection)
            GWSGIHandler:WSGI (include /api requests)
        """
        url = environ["PATH_INFO"]
        ws = environ.get("wsgi.websocket",None)
        # Is this a WebSocket request (we need to maintain this connection)
        if ws:
            self.logger.debug("gwss_dispatch:WebSocket:%s" % (url))
            wshandler = GWSSHandler(self, environ, ws)
            gevent.spawn(wshandler.run())
            return(None)
        # So, this is a WSGI request (not a WebSocket)
        else:
            self.logger.debug("gwss_dispatch:WSGI:%s" % (url))
            wsgihandler = GWSGIHandler(self.name, self.collected_routes, environ, response)
            msg = wsgihandler.run()
            return(msg)

    def add_client(self, address, client):
        self.clients[address] = client
    def del_client(self, address):
        self.logger.debug("del_client %s" % address)
        try:
            del self.clients[address]
        except:
            pass
    def action_send_client (self, msg):
        try:
            address = msg["data"].pop("client")
            self.clients[address].send(json.dumps(msg["data"]))
        except KeyError:
            self.logger.warning("Invalid packet dropped: %s" % msg)
        except:
            self.logger.info("Client lost, could not deliver %s" % msg)
            self.del_client(address)

    def main(self):
        self.clients = {}
        routes = []
        for s in self.services.values():
            s_routes = s.public_routes
            if s_routes:
                routes.append(route(s.name, *s_routes))
        html_dir = self.config.get("html_dir", "")
        if html_dir:
            routes.append(static("", html_dir))
        self.collected_routes = route("", *routes)
        self.server = WSGIThread(self.name, self.config, self.gwss_dispatch)
        self.server.start()
        while True:
            self.listen()
        # Starting network listener
        #gevent.signal(signal.SIGQUIT, gevent.kill)
        #gevent.signal(signal.SIGHUP, gwss.sighup)

def clients(name, config):
    return ClientService(name, config)

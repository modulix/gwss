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

#if sys.version_info.major == 2:
    #print("running Python 2.x")
    #import urlparse

#if sys.version_info.major == 3:
    #print("running Python 3.x")
    #import urllib.parse as urlparse

class WSGIThread (Thread):
    def __init__(self, config, dispatch, logger):
        super(WSGIThread, self).__init__()
        self.dispatch = dispatch
        self.logger = logger
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
        self.logger.debug("gwss_dispatch(%s)" % environ)
        ws = False
        try:
            ws = environ["wsgi.websocket"]
        except KeyError:
            pass
        # Is this a WebSocket request (we need to maintain this connection)
        if ws:
            self.logger.debug("gwss_dispatch:WebSocket:%s" % (url))
            wshandler = GWSSHandler(self, environ, ws)
            gevent.spawn(wshandler.run())
            return(None)
        # So, this is a WSGI request (not a WebSocket)
        else:
            self.logger.debug("gwss_dispatch:WSGI:%s" % (url))
            wsgihandler = GWSGIHandler(self.logger, self.config["html_dir"], environ, response)
            msg = wsgihandler.run()
            return(msg)

    def add_client(self, client):
        self.clients[id(client)] = client
    def del_client(self, client):
        self.logger.debug("del_client %s" % id(client))
        try:
            del self.clients[id(client)]
        except:
            pass
    def action_send_client (self, msg):
        try:
            client = msg["data"].pop("client")
            self.clients[client].send(json.dumps(msg["data"]))
        except KeyError:
            self.logger.error("Invalid packet dropped: %s" % msg)
        except:
            self.logger.warning("Client lost, could not deliver %s" % msg)
            # Lost one...
            self.del_client(client)

    def main(self):
        self.clients = {}
        self.server = WSGIThread(self.config, self.gwss_dispatch, self.logger)
        self.server.start()
        while True:
            self.listen()
        # Starting network listener
        #gevent.signal(signal.SIGQUIT, gevent.kill)
        #gevent.signal(signal.SIGHUP, gwss.sighup)

def clients(name, config):
    return ClientService(name, config)

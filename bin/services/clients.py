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

server = "127.0.0.1"
port = 44400
max_clients = 1000

class WSGIThread (Thread):
	def __init__(self, dispatch):
		super(WSGIThread, self).__init__()
		self.dispatch = dispatch
	def run(self):
		pool = Pool(max_clients)
		gwsgi = WSGIServer((server, port), self.dispatch, spawn=pool, handler_class=WebSocketHandler)
		gwsgi.serve_forever()



class ClientService(DaemonService):
	def gwss_dispatch(self, environ, response):
		"""
		For each connection we use one of this handlers:
			GWSSHandler:WebSocket (permanent connection)
			GWSGIHandler:WSGI (include /api requests)
		"""
		url = environ["PATH_INFO"]
		ws = False
		try:
			ws = environ["wsgi.websocket"]
		except KeyError:
			pass
		# Is this a WebSocket request (we need to maintain this connection)
		if ws:
			#gwss.logger.debug("gwss:dispatch:%s:WebSocket..." % (url))
			# So this can NOT be run in a separate thread...
			wshandler = GWSSHandler(self, environ, ws)
			gevent.spawn(wshandler.run())
			return(None)
		# So, this is a WSGI request (not a WebSocket)
		else:
			#gwss.logger.debug("gwss:dispatch:%s:WSGI..." % (url))
			wsgihandler = GWSGIHandler(self, environ, response)
			msg = wsgihandler.run()
			return([msg])

	def add_client(self, client):
		self.clients[id(client)] = client
	def del_client(self, client):
		#self.logger.debug("GWSServer:del_client %s" % id_client)
		del self.clients[id(client)]
	def action_send_client (self, client, js_action, data):
		self.clients[client].send(json.dumps({"js_action":js_action, "data":data}))

	def main(self):
		self.clients = {}
		self.server = WSGIThread(self.gwss_dispatch)
		self.server.start()
		while True:
			self.listen()
		# Starting network listener
		#gevent.signal(signal.SIGQUIT, gevent.kill)
		#gevent.signal(signal.SIGHUP, gwss.sighup)
		#self.logger.info("gwss:WebSocket Server is listening at http://%s:%s/" % (server, config.port))

def clients(send_queue):
	return ClientService("clients",send_queue)

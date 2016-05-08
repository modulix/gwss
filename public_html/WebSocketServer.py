from __future__ import print_function
from threading import Thread
import os

class WebSocketServer(Thread):
	"""
	This server is used to control all WebSocketServices
	found in ./services/ directory
	Also a list of all current websocked is also checked to
	send "ping" it no activity is detceted in last 42 sec.
	"""
	def __init__(self):
		super(WebSocketServer, self).__init__()
		print("gwss:WebSocketServer init...")
		self.clients = []
		self.services = []
		self.listen = True
		self.daemon = True
		self.track = {}
	def run(self):
		print("gwss:WebSocketServer run...")
		# This server start a service thread for each .py file found in ./services directory
		print("gwss:WebSocketServer starting all ./services :")
		svc_dir = "./services"
		for file_name in os.listdir(svc_dir):
			(fln, fle) = os.path.splitext(file_name)
			if os.path.isfile(os.path.join(svc_dir, file_name)) and fle == ".py" and fln != "__init__":
				print("gwss:service :%s" % file_name)
				service = WebSocketService(fln, self.track)
				self.services.append(service)
		for service in self.services:
			service.start()
		# Pooling all clients to send ping message to "inactive" clients
		while self.listen:
			curtime = datetime.datetime.now()
			delta = datetime.timedelta(seconds=42)
			for client in self.clients:
				if (curtime - self.track[id(client)]) > delta: 
					self.ping(client)
			# More client, less sleeping... (from 10s to 0.1s)
			# 1->10s, 100->1s 1000+ -> 0.1s
			if len(self.clients):
				t2sleep = max(0.1, min(10, (100 / len(self.clients))))
			else:
				t2sleep = 10
			time.sleep(t2sleep)
			print("g", end="")
	def ping(self, client):
		print("gwss:ping(%s) %s,%s" % (id(client), client.request.remote_ip, client.request.headers['X-Real-Ip']))
		sysdate = datetime.datetime.now()
		msg = "gwss:ping %s" % sysdate.strftime("%x %X")
		client.write_message(msg)
		self.track[id(client)] = sysdate
	def send_all(self, msg):
		if (len(self.clients)):
			print("gwss:send_all %s" % msg)
			for client in self.clients:
				client.write_message(msg)
				self.track[id(client)] = datetime.datetime.now()
	def add_client(self, client):
		print("gwss:add_client %s" % id(client))
		if client not in self.clients:
			self.clients.append(client)
			self.track[id(client)] = datetime.datetime.now()
		for service in self.services:
			service.events.append({"client" : client, "event": "add_client"})
	def del_client(self, client):
		print("gwss:del_client %s" % id(client))
		for service in self.services:
			if client in service.clients:
				service.del_client(client)
				service.events.append({"client" : client, "event": "del_client"})
		if client in self.clients:
			self.clients.remove(client)
			del self.track[id(client)]
	def add_svc_client(self, svc, client, args):
		print("gwss:add_svc_client(%s,%s,%s)" % (svc, id(client), args))
		for service in self.services:
			if service.name == svc:
				service.add_client(client)
				service.events.append({"client" : client, "event": "svc_add_client"})
				break
	def del_svc_client(self, svc, client, args):
		print("gwss:del_svc_client(%s,%s,%s)" % (svc, id(client), args))
		for service in self.services:
			if service.name == svc:
				service.del_client(client)
				service.events.append({"client" : client, "event": "svc_del_client"})
				break
	def stop(self):
		print("stop %s" % self)
		for service in services:
			service.stop()
			service.join()
		self.listen = False
	def __del__(self):
		print("gwss:WebSocketServer dead")

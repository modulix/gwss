#!/usr/bin/env python
import datetime
def sysdate(service, gwss):
	"""
	This service broadcast locale datetime
	"""
	print("%s:%s" % (service.name, "Init/setup"))
	service.heartbeat = 1

def receive(gwss, service, action, client, data):
	"""
	"""
	print("%s:%s(%s)" % (service.name, id(client), data))
	service.send_all(data)

def event(gwss, service, client, event):
	"""
	This is a broadcast worker :
	1 worker -> all connected clients
	"""
	#print("%s:%s" % ("sysdate", event))
	msg = '{"service": "sysdate", "action": "set", "data":{"id":"gwss_time","value": "%s"}}' % datetime.datetime.now().strftime("%x %X")
	service.send_all(msg)

def api(gwss, service, action, data):
	"""
	Management interface
	"""
	# Subscribtion
	if action == "subscribe":
		data = {"service": "sysdate", "action": "subscribe", "data": data}
		msg = json.dumps(data)
		service.send_all(msg)

	if action == "get":
		id = data["id"]
		value = data["value"]
		data = {"service": "echo", "action": "set", "data": {"id": id, "value": value}}
		service.send_all(msg)


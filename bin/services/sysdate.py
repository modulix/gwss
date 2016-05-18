#!/usr/bin/env python
from datetime import datetime
def sysdate(service, gwss):
	"""
	This service broadcast system datetime
	"""
	gwss.logger.debug("%s:%s" % (service.name, "init/setup"))
	service.heartbeat = 1

def action(gwss, service, action, client, data):
	"""
	This is a broadcast timer only worker :
	1 worker -> send_all service subscribed clients
	"""
	if action == "subscribe":
		service.add_client(client)
	if action == "unsubscribe":
		service.del_client(client)
	if action == "timer":
		if len(service.clients):
			#gwss.logger.debug("%s:%s:%s:%s" % (service.name, action, id(client), data))
			message = '{"service": "sysdate", "action": "set", "data":{"id":"gwss_time","value": "%s"}}' % datetime.now().strftime("%x %X")
			service.send_all(message)
	# Other events are ignored...

def api(gwss, service, action, data):
	"""
	Management interface
	"""
	# Subscribtion
	if action == "subscribe":
		data = {"service": "sysdate", "action": "subscribe", "data": data}
		message = json.dumps(data)
		service.send_all(message)

	if action == "get":
		id = data["id"]
		value = data["value"]
		data = {"service": "echo", "action": "set", "data": {"id": id, "value": value}}
		service.send_all(message)


#!/usr/bin/env python
import datetime
import json

def echo(service, gwss):
	"""
	This service broadcast all received messages to all connected clients
	event -> worker -> send_all (same message)
	"""
	gwss.logger.debug("%s:%s" % (service.name, "Init/setup"))
	# Persistent variables of the service:
	service.last = datetime.datetime.now()

def action(gwss, service, action, client, data):
	"""
	This function broadcast messages to all service clients
	"""
	gwss.logger.debug("%s:%s:%s:%s" % (service.name, action, id(client), data))
	message = "%s:%s:error:unhandled action" % (service.name,action)
	if action == "subscribe":
		service.add_client(client)
		message = ""
	if action == "unsubscribe":
		service.del_client(client)
		message = ""
	if action == "set":
		message = '{"service": "echo", "action": "set", "data": %s}' % data
	if action == "add_client" or action == "del_client":
		# Nothing to do...
		message = ""
	if action == "add_svc_client":
		message = '{"service": "echo", "action": "set", "data":{"id":"gwss_message","value": "New client:%s"}}' % id(client)
	if action == "del_svc_client":
		message = '{"service": "echo", "action": "set", "data":{"id":"gwss_message","value": "Bye client:%s"}}' % id(client)

	if message:
		gwss.logger.debug("%s:%s:%s:%s" % (service.name, action, id(client), message))
		service.send_all(message)

def api(gwss, service, action, data):
	"""
	This function permit this service management
	"""
	gwss.logger.debug("%s:api:%s:%s" % (service.name, action, data))
	message = "error:unhandled action"
	if action == "set":
		data = {"service": "echo", "action": "set", "data": data}
		message = json.dumps(data)
		gwss.logger.debug("%s:api:set:send_all:%s" % (service.name, message))
		service.send_all(message)
	if action == "get":
		ident = data["id"]
		value = data["value"]
		gwss.logger.debug("%s:api:get:send_all:%s" % (service.name, message))
		data = {"service": "echo", "action": "set", "data": {"id": ident, "value": value}}
		service.send_all(message)


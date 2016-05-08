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

def receive(gwss, service, action, client, data):
	"""
	This function broadcast evry received message to all service clients
	"""
	gwss.logger.debug("%s:%s(%s)" % (service.name, id(client), data))
	service.send_all(data)

def event(gwss, service, client, event):
	"""
	This function broadcast "event" messages to all service clients
	"""
	gwss.logger.debug("%s:%s" % (service.name, event))
	msg = "%s:%s:error:unhandled event" % (service,event)
	if event == "add_client" or event == "del_client":
		# Nothing to do...
		msg = ""
	if event == "add_svc_client":
		msg = '{"service": "echo", "action": "set", "data":{"id":"gwss_message","value": "New client:%s"}}' % id(client)
	if event == "del_svc_client":
		msg = '{"service": "echo", "action": "set", "data":{"id":"gwss_message","value": "Bye client:%s"}}' % id(client)

	if msg:
		service.send_all(msg)

def api(gwss, service, action, data):
	"""
	This function permit this service management
	"""
	gwss.logger.debug("%s:api:%s:%s" % (service.name, action, data))
	msg = "error:unhandled event"
	if action == "set":
		data = {"service": "echo", "action": "set", "data": data}
		msg = json.dumps(data)
		gwss.logger.debug("%s:api:set:send_all:%s" % (service.name, msg))
		service.send_all(msg)
	if action == "get":
		ident = data["id"]
		value = data["value"]
		gwss.logger.debug("%s:api:get:send_all:%s" % (service.name, msg))
		data = {"service": "echo", "action": "set", "data": {"id": ident, "value": value}}
		service.send_all(msg)


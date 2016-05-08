#!/usr/bin/env python
import datetime
import json

def chat(service, gwss):
	"""
	This service broadcast all received messages to all connected clients
	event -> worker -> send_all (same message)
	"""
	gwss.logger.debug("%s:%s" % (service.name, "Init/setup"))
	# Persistent variables of the service:
	service.last = datetime.datetime.now()
	# Enable "timer" event to send time evry minutes
	service.heartbeat = 60
	
def receive(gwss, service, action, client, data):
	"""
	This function is executed each time somebody send a message
	"""
	gwss.logger.debug("%s:%s:%s:%s:%s" % (service.name, action, id(client),data["id"],data["value"]))
	message = "%s:%s:error:unhandled message" % (service,action)
	if action == "unsubscribe":
		message = ""
	if action == "subscribe":
		message = '{"service": "chat", "action": "set", "data": {"id":"%s", "value":"%s"}}' % (data["id"],id(client))
	if action == "set":
		message = '{"service": "chat", "action": "set", "data": {"id":"%s", "value":"%s"}}' % (data["id"], data["value"])
	if action == "set" and data["id"] == "messages":
		try:
			username = service.track[id(client)]['username']
		except:
			username = id(client)
		message = '{"service": "chat", "action": "set", "data": {"id":"%s", "value":"%s:%s"}}' % (data["id"],username, data["value"])
	if action == "user":
		message = '{"service": "chat", "action": "set", "data": {"id":"messages", "value":"%s is known as %s"}}' % (id(client), data["value"])
		service.track[id(client)]['username'] = data["value"]

	if message:
		gwss.logger.debug("%s:%s:%s" % (service.name, action, message))
		service.send_all(message)

def event(gwss, service, client, event):
	"""
	This function is executed each time there is a new "event"
	"""
	gwss.logger.debug("%s:%s" % ("chat", event))
	msg = "%s:%s:error:unhandled event" % (service,event)
	if event == "add_client":
		# Nothing to do...
		msg = ""
	if event == "timer":
		msg = '{"service": "chat", "action": "set", "data":{"id":"messages","value": "%s"}}' % datetime.datetime.now()
	if event == "del_client":
		msg = '{"service": "chat", "action": "set", "data":{"id":"messages","value": "Bye client:%s"}}' % id(client)
	if event == "add_svc_client":
		msg = '{"service": "chat", "action": "set", "data":{"id":"messages","value": "Welcome %s !"}}' % id(client)
	if event == "del_svc_client":
		msg = '{"service": "chat", "action": "set", "data":{"id":"messages","value": "Bye client:%s"}}' % id(client)

	if msg:
		gwss.logger.debug("%s:%s:%s" % ("chat", event, msg))
		service.send_all(msg)

def api(gwss, service, action, data):
	"""
	REST api to manage this service
	"""
	if action == "set":
		data = {"service": "chat", "action": "set", "data": data}
		msg = json.dumps(data)
		service.send_all(msg)
	if action == "get":
		id = data["id"]
		value = data["value"]
		data = {"service": "chat", "action": "set", "data": {"id": id, "value": value}}
		service.send_all(msg)

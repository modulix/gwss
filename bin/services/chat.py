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

	# Enable "timer" event to send time evry heartbeat seconds
	service.heartbeat = 120
	
def action(gwss, service, action, client, data):
	"""
	This function is executed each time there is a new "event"
	This function is executed each time somebody send a message
	"""
	gwss.logger.debug("%s:%s:%s:%s" % (service.name, action, id(client),data))
	message = "%s:%s:error:unhandled action" % (service.name,action)
	if action == "subscribe":
		service.add_client(client)
		message = '{"service": "chat", "action": "set", "data": {"id":"%s", "value":"%s"}}' % (data["id"],id(client))
	if action == "unsubscribe":
		service.del_client(client)
	if action == "add_group":
		new_group = data["value"]
		exist = False
		for grp in service.groups:
			if grp["name"] == new_group:
				message = '{"service": "chat", "action": "set", "data":{"id":"messages","value": "You need to choose another room name, %s already exists..."}}' % new_group
				service.send_client(client, message)
				exist = True
		if not exist:
			service.add_group(new_group, client)
			message = '{"service": "chat", "action": "set", "data":{"id":"gwss_chat_lst_groups","value": %s}}' % lst_groups(service)
	if action == "del_group":
		service.del_group(new_group, client)
		message = '{"service": "chat", "action": "set", "data":{"id":"gwss_chat_lst_groups","value": %s}}' % lst_groups(service)
	if action == "set":
		message = '{"service": "chat", "action": "set", "data": {"id":"%s", "value":"%s"}}' % (data["id"], data["value"])
	if action == "set" and data["id"] == "messages":
		try:
			username = service.track[id(client)]['username']
		except:
			username = id(client)
		message = '{"service": "chat", "action": "set", "data": {"id":"%s", "value":"%s:%s"}}' % (data["id"],username, data["value"])
	if action == "timer":
		message = '{"service": "chat", "action": "set", "data":{"id":"messages","value": "%s"}}' % datetime.datetime.now().strftime("%X")
	if action == "user":
		message = '{"service": "chat", "action": "set", "data": {"id":"messages", "value":"%s is known as %s"}}' % (id(client), data["value"])
		service.track[id(client)]['username'] = data["value"]
	if action == "add_client":
		message = ""
	if action == "del_client":
		message = ""
	if action == "add_svc_client":
		message = '{"service": "chat", "action": "set", "data":{"id":"gwss_chat_lst_groups","value": %s}}' % lst_groups(service)
		service.send_all(message)
		message = '{"service": "chat", "action": "set", "data":{"id":"gwss_chat_clients_count","value": "%s"}}' % len(service.clients)
		service.send_all(message)
		message = '{"service": "chat", "action": "set", "data":{"id":"gwss_chat_lst_clients","value": %s}}' % lst_clients(service)
		service.send_all(message)
		message = '{"service": "chat", "action": "set", "data":{"id":"messages","value": "Welcome to new user %s !"}}' % id(client)
	if action == "del_svc_client":
		message = '{"service": "chat", "action": "set", "data":{"id":"gwss_chat_lst_groups","value": %s}}' % lst_groups(service)
		service.send_all(message)
		message = '{"service": "chat", "action": "set", "data":{"id":"gwss_chat_lst_clients","value": %s}}' % lst_clients(service)
		service.send_all(message)
		message = '{"service": "chat", "action": "set", "data":{"id":"gwss_chat_clients_count","value": "%s"}}' % len(service.clients)
		service.send_all(message)
		message = '{"service": "chat", "action": "set", "data":{"id":"messages","value": "User %s is leaving... bye, bye !"}}' % id(client)

	if message:
		gwss.logger.debug("%s:%s:%s:%s" % (service.name, action, id(client),message))
		service.send_all(message)

def lst_clients(service):
	lst = []
	for cli in service.clients:
		lst.append(str(id(cli)))
	return(json.dumps(lst))

def lst_groups(service):
	lst = []
	for grp in service.groups:
		lst.append(grp["name"])
	return(json.dumps(lst))

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
